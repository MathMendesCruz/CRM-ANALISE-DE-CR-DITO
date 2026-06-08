import re
import unicodedata
from io import BytesIO, StringIO

import pandas as pd
import streamlit as st
from rapidfuzz import process, fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


@st.cache_data
def read_file(uploaded_file):
	if uploaded_file is None:
		return None
	name = uploaded_file.name.lower()
	uploaded_file.seek(0)
	# Excel files
	if name.endswith(('.xls', '.xlsx')):
		try:
			return pd.read_excel(uploaded_file)
		except Exception:
			uploaded_file.seek(0)
	# Read bytes and try multiple decodings for CSV/text
	data = uploaded_file.read()
	# If file is empty
	if not data:
		return pd.DataFrame()

	# Try common text encodings
	for enc in ('utf-8', 'latin1', 'cp1252'):
		try:
			txt = data.decode(enc)
			try:
				return pd.read_csv(StringIO(txt), sep=None, engine='python')
			except Exception:
				# try with default comma separator
				try:
					return pd.read_csv(StringIO(txt))
				except Exception:
					continue
		except Exception:
			continue

	# Last resort: try reading bytes with pandas (it may infer encoding)
	try:
		return pd.read_csv(BytesIO(data))
	except Exception:
		# Give a simple fallback: return a single-column DataFrame with raw content
		try:
			raw = data.decode('utf-8', errors='replace')
		except Exception:
			raw = str(data)
		return pd.DataFrame({'raw': [raw]})


def normalize_value(v: str) -> str:
	if pd.isna(v):
		return ''
	if not isinstance(v, str):
		v = str(v)
	# remove accents
	v = unicodedata.normalize('NFKD', v).encode('ASCII', 'ignore').decode('ASCII')
	# lowercase and remove non-alphanumeric
	v = v.lower()
	v = re.sub(r'[^a-z0-9]', ' ', v)
	v = re.sub(r'\s+', ' ', v).strip()
	return v


def build_key(df: pd.DataFrame, cols: list) -> pd.Series:
	if not cols:
		return pd.Series([''] * len(df), index=df.index)
	parts = []
	for c in cols:
		parts.append(df[c].astype(str).map(normalize_value))
	return pd.Series([' | '.join(vals) for vals in zip(*parts)], index=df.index)


def fuzzy_match_keys(keys_a, keys_b, scorer=fuzz.ratio, threshold=80, top_n=1):
	choices = list(keys_b)
	results = []
	for k in keys_a:
		if not k:
			results.append((None, 0))
			continue
		match = process.extractOne(k, choices, scorer=scorer)
		if match:
			best, score, idx = match[0], match[1], match[2]
			if score >= threshold:
				results.append((best, score))
			else:
				results.append((best, score))
		else:
			results.append((None, 0))
	return results


def to_csv_bytes(df: pd.DataFrame) -> bytes:
	return df.to_csv(index=False).encode('utf-8')


def main():
	st.title('Comparador de Clientes — Playhub')
	st.write('Faça upload de dois arquivos (CSV ou Excel) e selecione as colunas para comparar.')

	col1, col2 = st.columns(2)
	with col1:
		file_a = st.file_uploader('Arquivo A', type=['csv', 'xls', 'xlsx'], key='a')
	with col2:
		file_b = st.file_uploader('Arquivo B', type=['csv', 'xls', 'xlsx'], key='b')

	df_a = read_file(file_a)
	df_b = read_file(file_b)

	if df_a is not None:
		st.subheader('A — Pré-visualização')
		st.write(df_a.head())
	if df_b is not None:
		st.subheader('B — Pré-visualização')
		st.write(df_b.head())

	if df_a is None or df_b is None:
		st.info('Envie os dois arquivos para iniciar a comparação.')
		return

	cols_a = st.multiselect('Colunas para chave (Arquivo A)', options=list(df_a.columns), default=[list(df_a.columns)[0]])
	cols_b = st.multiselect('Colunas para chave (Arquivo B)', options=list(df_b.columns), default=[list(df_b.columns)[0]])

	method = st.radio('Método de comparação', options=['Exato', 'Fuzzy (rapidfuzz)', 'TF-IDF (cosine)'], index=1)
	threshold = st.slider('Limite de similaridade (para Fuzzy)', min_value=0, max_value=100, value=85)

	if st.button('Executar comparação'):
		with st.spinner('Gerando chaves e comparando...'):
			key_a = build_key(df_a, cols_a)
			key_b = build_key(df_b, cols_b)

			df_a = df_a.copy()
			df_b = df_b.copy()
			df_a['_key_playhub'] = key_a
			df_b['_key_playhub'] = key_b

			if method == 'Exato':
				merged = df_a.merge(df_b, on='_key_playhub', how='left', suffixes=('_A', '_B'), indicator=True)
				matched = merged[merged['_merge'] == 'both'].drop(columns=['_merge'])
				unmatched_a = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
				st.success(f'Matching exato completo — {len(matched)} correspondências encontradas')
				st.dataframe(matched.head(200))

				st.download_button('Download — correspondências (CSV)', data=to_csv_bytes(matched), file_name='matches_exact.csv')
				st.download_button('Download — não casados A (CSV)', data=to_csv_bytes(unmatched_a), file_name='unmatched_a_exact.csv')
			elif method.startswith('Fuzzy'):
				# fuzzy (rapidfuzz)
				keys_b_list = list(df_b['_key_playhub'])
				keys_a_list = list(df_a['_key_playhub'])

				nA = len(keys_a_list)
				nB = len(keys_b_list)
				total_ops = nA * nB
				if total_ops > 5_000_000:
					st.warning(f'Esta operação fará aproximadamente {total_ops:,} comparações (A:{nA} × B:{nB}).')
					proceed = st.checkbox('Confirmo que desejo continuar (pode demorar muito)')
					if not proceed:
						st.info('Operação abortada pelo usuário — reduza o tamanho dos arquivos ou selecione amostra.')
						return

				batch = st.number_input('Tamanho do lote para progresso (rows por atualização)', min_value=10, max_value=5000, value=200)
				progress = st.progress(0)
				matched_rows = []
				scores = []
				matched_idx = []

				# run matching in batches and update progress
				for start in range(0, nA, batch):
					end = min(start + batch, nA)
					for i in range(start, end):
						k = keys_a_list[i]
						if not k:
							scores.append(0)
							matched_idx.append(None)
							matched_rows.append({})
							continue
						try:
							match = process.extractOne(k, keys_b_list, scorer=fuzz.ratio)
						except Exception:
							match = None

						if not match:
							scores.append(0)
							matched_idx.append(None)
							matched_rows.append({})
							continue

						best, score, idx = match[0], match[1], match[2]
						scores.append(score)
						if best is None:
							matched_idx.append(None)
							matched_rows.append({})
							continue

						try:
							idx_b = df_b[df_b['_key_playhub'] == best].index[0]
							matched_idx.append(idx_b)
							matched_rows.append(df_b.loc[idx_b].to_dict())
						except Exception:
							matched_idx.append(None)
							matched_rows.append({})

					progress.progress(min(100, int((end / nA) * 100)))

				df_res = df_a.reset_index(drop=True).copy()
				df_res['match_score'] = scores
				df_res['matched_key_b'] = [r.get('_key_playhub', None) if isinstance(r, dict) else None for r in matched_rows]

				# attach matched columns from B (prefix B_)
				df_b_pref = df_b.copy()
				df_b_pref = df_b_pref.add_prefix('B_')
				df_b_pref = df_b_pref.reset_index()
				df_res['B_index'] = matched_idx
				merged = df_res.merge(df_b_pref, left_on='B_index', right_on='index', how='left')

				matches_pass = merged[merged['match_score'] >= threshold]
				st.success(f'Fuzzy matching executado — {len(matches_pass)} acima do limite ({threshold})')
				st.dataframe(matches_pass.head(200))

				st.download_button('Download — correspondências fuzzy (CSV)', data=to_csv_bytes(matches_pass), file_name='matches_fuzzy.csv')
			elif method.startswith('TF-IDF'):
				# TF-IDF + NearestNeighbors (cosine) — faster on larger datasets
				st.info('Usando TF-IDF + NearestNeighbors (cosine).')
				prefix_block = st.number_input('Bloqueio por prefixo (comprimento, 0 desativa)', min_value=0, max_value=10, value=0)

				keys_a_list = list(df_a['_key_playhub'])
				keys_b_list = list(df_b['_key_playhub'])

				# optional blocking by prefix
				if prefix_block > 0:
					def prefix_key(s):
						return (s[:prefix_block] if s else '')

					df_a['_block'] = df_a['_key_playhub'].map(prefix_key)
					df_b['_block'] = df_b['_key_playhub'].map(prefix_key)
				else:
					df_a['_block'] = ''
					df_b['_block'] = ''

				results_rows = []
				progress = st.progress(0)
				unique_blocks = df_a['_block'].unique()
				total_blocks = len(unique_blocks)
				processed_blocks = 0

				for blk in unique_blocks:
					sub_a = df_a[df_a['_block'] == blk]
					sub_b = df_b[df_b['_block'] == blk]
					if len(sub_a) == 0 or len(sub_b) == 0:
						# append unmatched
						for _ in range(len(sub_a)):
							results_rows.append((None, 0, None))
						processed_blocks += 1
						progress.progress(int((processed_blocks / total_blocks) * 100))
						continue

					vec = TfidfVectorizer(analyzer='char_wb', ngram_range=(2,4)).fit(list(sub_b['_key_playhub']))
					Xb = vec.transform(list(sub_b['_key_playhub']))
					Xa = vec.transform(list(sub_a['_key_playhub']))

					nn = NearestNeighbors(n_neighbors=1, metric='cosine', algorithm='brute').fit(Xb)
					dist, ind = nn.kneighbors(Xa, return_distance=True)
					# cosine distance -> similarity
					sim = 1 - dist.ravel()
					inds = ind.ravel()

					for s, idxb in zip(sim, inds):
						if idxb is None or idxb >= len(sub_b):
							results_rows.append((None, 0, None))
						else:
							keyb = list(sub_b['_key_playhub'])[idxb]
							# find global index
							try:
								idx_global = sub_b[sub_b['_key_playhub'] == keyb].index[0]
							except Exception:
								idx_global = None
							results_rows.append((keyb, int(s * 100), idx_global))

					processed_blocks += 1
					progress.progress(int((processed_blocks / total_blocks) * 100))

				# build DataFrame result
				df_res = df_a.reset_index(drop=True).copy()
				sims = [r[1] for r in results_rows]
				matched_keys = [r[0] for r in results_rows]
				matched_idxs = [r[2] for r in results_rows]
				df_res['match_score'] = sims
				df_res['matched_key_b'] = matched_keys
				df_b_pref = df_b.copy()
				df_b_pref = df_b_pref.add_prefix('B_')
				df_b_pref = df_b_pref.reset_index()
				df_res['B_index'] = matched_idxs
				merged = df_res.merge(df_b_pref, left_on='B_index', right_on='index', how='left')

				matches_pass = merged[merged['match_score'] >= threshold]
				st.success(f'TF-IDF matching executado — {len(matches_pass)} acima do limite ({threshold})')
				st.dataframe(matches_pass.head(200))
				st.download_button('Download — correspondências TF-IDF (CSV)', data=to_csv_bytes(matches_pass), file_name='matches_tfidf.csv')

		st.balloons()


if __name__ == '__main__':
	main()

