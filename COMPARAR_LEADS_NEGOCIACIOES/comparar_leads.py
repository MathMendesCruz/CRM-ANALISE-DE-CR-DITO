import streamlit as st
import pandas as pd
from io import BytesIO

# APP.PY
# Streamlit app para comparar Leads, Negociações e/Base de Clientes (IXC)
# GitHub Copilot


st.set_page_config(page_title="Comparador Inmap Sales / IXC", layout="wide")
st.title("Comparador de Leads / Negociações / Clientes (IXC)")


uploaded = st.file_uploader("Envie 3 arquivos: Leads, Negociações e Clientes Opa Suite (CSV ou XLSX)", accept_multiple_files=True, type=["csv", "xls", "xlsx"])
if not uploaded or len(uploaded) != 3:
    st.info("Envie exatamente 3 arquivos para comparar: Leads, Negociações e Clientes Opa Suite.")
    st.stop()

def read_file(f):
    name = f.name
    try:
        if name.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(f)
        else:
            df = pd.read_csv(f, sep=None, engine='python')
    except Exception:
        f.seek(0)
        df = pd.read_csv(f)
    return df

dfs = {}
for f in uploaded:
    try:
        df = read_file(f)
    except Exception as e:
        st.error(f"Erro lendo {f.name}: {e}")
        st.stop()
    dfs[f.name] = df


# Mapear arquivos obrigatoriamente para as funções corretas
st.sidebar.header("Mapear arquivos para funções")
roles = ["Leads", "Negociações", "Clientes Opa Suite"]
file_names = list(dfs.keys())
mapping = {}
used_roles = set()
for fn in file_names:
    available_roles = [r for r in roles if r not in used_roles]
    mapping[fn] = st.sidebar.selectbox(f"Função para: {fn}", options=available_roles, key=fn)
    used_roles.add(mapping[fn])

# Garantir que todos os papéis foram mapeados
if set(mapping.values()) != set(roles):
    st.error("Cada arquivo deve ser mapeado para uma função diferente: Leads, Negociações e Clientes Opa Suite.")
    st.stop()

# show a preview and columns

# Visualização lado a lado dos arquivos carregados
st.subheader("Pré-visualização dos arquivos carregados")
cols = st.columns(len(dfs))
for idx, (fn, df) in enumerate(dfs.items()):
    with cols[idx]:
        st.markdown(f"**{fn}**<br><small>Função: {mapping[fn]}<br>Linhas: {len(df)}</small>", unsafe_allow_html=True)
        st.dataframe(df.head(200), use_container_width=True)
        st.caption(", ".join(df.columns.astype(str).tolist()))


# Selecionar colunas-chave para cada função
st.subheader("Selecionar colunas de telefone para cada arquivo")
df_leads = dfs[[fn for fn, role in mapping.items() if role == "Leads"][0]]
df_negociacoes = dfs[[fn for fn, role in mapping.items() if role == "Negociações"][0]]
df_clientes = dfs[[fn for fn, role in mapping.items() if role == "Clientes Opa Suite"][0]]

col_leads = st.selectbox("Coluna de telefone em Leads", options=df_leads.columns.tolist(), index=0, key="leads")
col_negociacoes = st.selectbox("Coluna de telefone em Negociações", options=df_negociacoes.columns.tolist(), index=0, key="negociacoes")
col_clientes = st.selectbox("Coluna de telefone em Clientes Opa Suite", options=df_clientes.columns.tolist(), index=0, key="clientes")

# normalization options

st.subheader("Opções de normalização (aplicadas às chaves)")
case_insensitive = st.checkbox("Ignorar maiúsculas/minúsculas (lower)", value=True)
strip_spaces = st.checkbox("Remover espaços iniciais/finais", value=True)
remove_multi_space = st.checkbox("Normalizar espaços internos (reduzir múltiplos para um)", value=True)
normalize_phone = st.checkbox("Normalizar números de telefone (remover símbolos e manter apenas dígitos)", value=False)

def normalize(series):
    s = series.astype(str)
    if strip_spaces:
        s = s.str.strip()
    if remove_multi_space:
        s = s.str.replace(r"\s+", " ", regex=True)
    if case_insensitive:
        s = s.str.lower()
    if normalize_phone:
        # Remove tudo que não for dígito
        s = s.str.replace(r"\D", "", regex=True)
        # Remove o 55 do início, se houver (código do Brasil)
        s = s.str.replace(r"^55", "", regex=True)
    return s


# Normalizar telefones
phones_leads = normalize(df_leads[col_leads])
phones_negociacoes = normalize(df_negociacoes[col_negociacoes])
phones_clientes = normalize(df_clientes[col_clientes])


st.subheader("Resultados da comparação entre os 3 arquivos")

# Encontrados em todos
mask_leads_in_neg = phones_leads.isin(phones_negociacoes)
mask_leads_in_cli = phones_leads.isin(phones_clientes)
mask_neg_in_leads = phones_negociacoes.isin(phones_leads)
mask_neg_in_cli = phones_negociacoes.isin(phones_clientes)
mask_cli_in_leads = phones_clientes.isin(phones_leads)
mask_cli_in_neg = phones_clientes.isin(phones_negociacoes)

leads_em_todos = df_leads[mask_leads_in_neg & mask_leads_in_cli]
negociacoes_em_todos = df_negociacoes[mask_neg_in_leads & mask_neg_in_cli]
clientes_em_todos = df_clientes[mask_cli_in_leads & mask_cli_in_neg]

st.write(f"Clientes presentes nos 3 arquivos: {len(leads_em_todos)} (base: Leads)")
st.dataframe(leads_em_todos)

# Encontrados em apenas 2 arquivos
leads_em_leads_e_neg = df_leads[mask_leads_in_neg & ~mask_leads_in_cli]
leads_em_leads_e_cli = df_leads[~mask_leads_in_neg & mask_leads_in_cli]
negociacoes_em_neg_e_cli = df_negociacoes[mask_neg_in_cli & ~mask_neg_in_leads]

st.write(f"Clientes em Leads e Negociações, mas não em Clientes Opa Suite: {len(leads_em_leads_e_neg)}")
st.dataframe(leads_em_leads_e_neg)
st.write(f"Clientes em Leads e Clientes Opa Suite, mas não em Negociações: {len(leads_em_leads_e_cli)}")
st.dataframe(leads_em_leads_e_cli)
st.write(f"Clientes em Negociações e Clientes Opa Suite, mas não em Leads: {len(negociacoes_em_neg_e_cli)}")
st.dataframe(negociacoes_em_neg_e_cli)

# Não encontrados nos outros
leads_somente = df_leads[~mask_leads_in_neg & ~mask_leads_in_cli]
negociacoes_somente = df_negociacoes[~mask_neg_in_leads & ~mask_neg_in_cli]
clientes_somente = df_clientes[~mask_cli_in_leads & ~mask_cli_in_neg]

st.write(f"Clientes somente em Leads: {len(leads_somente)}")
st.dataframe(leads_somente)
st.write(f"Clientes somente em Negociações: {len(negociacoes_somente)}")
st.dataframe(negociacoes_somente)
st.write(f"Clientes somente em Clientes Opa Suite: {len(clientes_somente)}")
st.dataframe(clientes_somente)


# Exportar resultados
def to_csv_bytes(df):
    b = BytesIO()
    df.to_csv(b, index=False)
    return b.getvalue()

st.subheader("Exportar resultados")
if not leads_em_todos.empty:
    st.download_button("Baixar: Presentes nos 3 arquivos (base: Leads)",
        data=to_csv_bytes(leads_em_todos),
        file_name="presentes_nos_3.csv", mime="text/csv")
if not leads_em_leads_e_neg.empty:
    st.download_button("Baixar: Leads e Negociações, não em Clientes Opa Suite",
        data=to_csv_bytes(leads_em_leads_e_neg),
        file_name="leads_e_negociacoes.csv", mime="text/csv")
if not leads_em_leads_e_cli.empty:
    st.download_button("Baixar: Leads e Clientes Opa Suite, não em Negociações",
        data=to_csv_bytes(leads_em_leads_e_cli),
        file_name="leads_e_clientes.csv", mime="text/csv")
if not negociacoes_em_neg_e_cli.empty:
    st.download_button("Baixar: Negociações e Clientes Opa Suite, não em Leads",
        data=to_csv_bytes(negociacoes_em_neg_e_cli),
        file_name="negociacoes_e_clientes.csv", mime="text/csv")
if not leads_somente.empty:
    st.download_button("Baixar: Somente em Leads",
        data=to_csv_bytes(leads_somente),
        file_name="somente_leads.csv", mime="text/csv")
if not negociacoes_somente.empty:
    st.download_button("Baixar: Somente em Negociações",
        data=to_csv_bytes(negociacoes_somente),
        file_name="somente_negociacoes.csv", mime="text/csv")
if not clientes_somente.empty:
    st.download_button("Baixar: Somente em Clientes Opa Suite",
        data=to_csv_bytes(clientes_somente),
        file_name="somente_clientes.csv", mime="text/csv")

st.success("Comparação concluída. Use as opções acima para revisar e exportar os resultados.")