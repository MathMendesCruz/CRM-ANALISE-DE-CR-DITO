import streamlit as st
import pandas as pd
import io
from datetime import datetime
import re
import unicodedata

st.set_page_config(page_title="Comparador de Clientes NETFI", layout="wide")

st.title("🔍 Comparador de Clientes NETFI")
st.markdown("Ferramentas para análise de dados e formatação de contatos")

# Criar tabs
tab1, tab2 = st.tabs(["📊 Comparador de Clientes", "📱 Formatador de Contatos OPA!"])

# ===== TAB 1: COMPARADOR DE CLIENTES =====
with tab1:
    st.subheader("Localize os dados de clientes com análise de crédito na base de dados NETFI/LINNE")

    # Sidebar para instruções
    with st.sidebar:
        st.markdown("### 📋 Instruções")
        st.markdown("""
        1. **Arquivo 1**: Insira a planilha com os clientes de análise de crédito
        2. **Arquivo 2**: Insira a planilha LEADS CRM
        3. O site vai comparar e localizar os dados dos clientes com análise de crédito
        """)

    # Seção de upload de arquivos
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        col_titulo, col_help = st.columns([3, 1])
        with col_titulo:
            st.subheader("📁 Arquivo 1: Análise de Crédito")
        with col_help:
            with st.expander("ℹ️ Como extrair?"):
                st.markdown("""
                **Passo a passo:**
                1. No IXC, acesse "Central de consultas (CPF/CNPJ)"
                2. Localize o botão de **Download (CSV)**
                3. Clique para baixar a planilha
                4. Envie o arquivo aqui ✅
                """)
        
        arquivo1 = st.file_uploader(
            "Selecione a planilha com os clientes de análise de crédito",
            type=["csv", "xlsx", "xls"],
            key="arquivo1"
        )

    with col2:
        col_titulo, col_help = st.columns([3, 1])
        with col_titulo:
            st.subheader("📁 Arquivo 2: LEADS CRM")
        with col_help:
            with st.expander("ℹ️ Como extrair?"):
                st.markdown("""
                **Passo a passo:**
                1. Acesse **Ferramentas > Query Builder** no IXC
                2. Localize o botão **Visualização Completa**
                3. Clique em **CSV** para exportar
                4. Envie o arquivo aqui ✅
                """)
        
        arquivo2 = st.file_uploader(
            "Selecione a planilha LEADS CRM",
            type=["csv", "xlsx", "xls"],
            key="arquivo2"
        )

    # Função utilitária para garantir que todo DataFrame esteja em string
    def _coerce_to_str(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df.fillna("")
        for c in df.columns:
            try:
                df[c] = df[c].astype(str)
            except Exception:
                pass
        return df

    # Função para carregar arquivo
    def carregar_arquivo(arquivo):
        try:
            if arquivo.name.endswith('.csv'):
                # Tenta diferentes separadores
                separadores = [',', ';', '\t', '|']
                df = None
                
                for sep in separadores:
                    try:
                        arquivo.seek(0)
                        df = pd.read_csv(arquivo, sep=sep, on_bad_lines='skip', engine='python', dtype=str)
                        if len(df.columns) > 1:  # Se encontrou múltiplas colunas, é o separador certo
                            return _coerce_to_str(df)
                    except Exception:
                        continue
                
                if df is not None:
                    return _coerce_to_str(df)
                else:
                    st.error("❌ Não foi possível identificar o separador do arquivo. Tente abrir em um editor e verificar.")
                    return None
            else:
                df = pd.read_excel(arquivo, dtype=str)
                return _coerce_to_str(df)
        except Exception as e:
            st.error(f"❌ Erro ao carregar arquivo: {e}")
            st.info("💡 Dica: Verifique se o arquivo está corrompido ou tente salvar novamente como CSV com separador de vírgula (,)")
            return None

    # Helpers de normalização para matching
    def _somente_digitos(valor):
        return re.sub(r"\D+", "", str(valor))

    def _normalizar_texto(valor):
        s = str(valor).strip()
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
        s = re.sub(r"\s+", " ", s)
        return s.upper()

    def _chave_match(serie: pd.Series, nome_coluna: str) -> pd.Series:
        nome = (nome_coluna or "").lower()

        def _pad_doc(cell: object) -> str:
            s = _somente_digitos(cell)
            if not s:
                return ""
            if "cpf" in nome:
                return s.zfill(11)
            if "cnpj" in nome:
                return s.zfill(14)
            if any(k in nome for k in ["documento", "doc"]):
                # Heurística: documentos com até 11 dígitos são CPF, >11 são CNPJ
                return s.zfill(11) if len(s) <= 11 else s.zfill(14)
            if "id" in nome:
                # Para IDs, mantenha apenas dígitos (sem padding forçado)
                return s
            return s

        if any(k in nome for k in ["cpf", "cnpj", "documento", "doc", "id"]):
            return serie.map(_pad_doc)
        else:
            return serie.map(_normalizar_texto)

    # Processar arquivos quando ambos são enviados
    if arquivo1 and arquivo2:
        st.markdown("---")
        
        # Carregar dados
        df1 = carregar_arquivo(arquivo1)
        df2 = carregar_arquivo(arquivo2)
        
        if df1 is not None and df2 is not None:
            st.success("✅ Arquivos carregados com sucesso!")
            
            # Exibir informações dos arquivos
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Arquivo 1**: {len(df1)} registros")
                with st.expander("Ver colunas disponíveis"):
                    st.write(df1.columns.tolist())
            
            with col2:
                st.info(f"**Arquivo 2**: {len(df2)} registros")
                with st.expander("Ver colunas disponíveis"):
                    st.write(df2.columns.tolist())
            
            st.markdown("---")
            
            # Seleção de coluna para matching
            st.subheader("⚙️ Configurar Comparação")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Detectar colunas de identificação
                colunas_id_arquivo1 = [col for col in df1.columns if 'id' in col.lower() or 'cnpj' in col.lower() or 'cpf' in col.lower()]
                idx_col1 = list(df1.columns).index(colunas_id_arquivo1[0]) if colunas_id_arquivo1 else 0
                coluna_match_1 = st.selectbox(
                    "Coluna para matching (Arquivo 1):",
                    df1.columns,
                    index=idx_col1,
                    key="col_match_1"
                )
            
            with col2:
                colunas_id_arquivo2 = [col for col in df2.columns if 'id' in col.lower() or 'cnpj' in col.lower() or 'cpf' in col.lower()]
                idx_col2 = list(df2.columns).index(colunas_id_arquivo2[0]) if colunas_id_arquivo2 else 0
                coluna_match_2 = st.selectbox(
                    "Coluna para matching (Arquivo 2):",
                    df2.columns,
                    index=idx_col2,
                    key="col_match_2"
                )
            
            with col3:
                # Detectar coluna de WhatsApp
                colunas_whatsapp = [col for col in df2.columns if 'whatsapp' in col.lower() or 'celular' in col.lower() or 'telefone' in col.lower()]
                idx_whatsapp = list(df2.columns).index(colunas_whatsapp[0]) if colunas_whatsapp else 0
                coluna_whatsapp = st.selectbox(
                    "Coluna de WhatsApp (Arquivo 2):",
                    df2.columns,
                    index=idx_whatsapp,
                    key="col_whatsapp"
                )

            colunas_extras_sel = st.multiselect(
                "Colunas extras do Arquivo 2 para incluir no resultado:",
                options=[c for c in df2.columns if c != coluna_match_2],
                default=[],
                key="colunas_extras_sel"
            )
            
            st.markdown("---")
            
            # Realizar comparação
            if st.button("🔍 Comparar e Encontrar WhatsApps", type="primary", use_container_width=True):
                try:
                    # Fazer merge dos DataFrames
                    # Primeiro, normalizar os valores para comparação (maiúsculas, sem espaços)
                    df1_copy = df1.copy()
                    df2_copy = df2.copy()
                    
                    # Normalizar colunas de matching (remove pontuação de CPF/CNPJ e padroniza texto)
                    df1_copy['_match_key'] = _chave_match(df1_copy[coluna_match_1], coluna_match_1)
                    df2_copy['_match_key'] = _chave_match(df2_copy[coluna_match_2], coluna_match_2)
                    
                    # Realizar merge
                    cols_para_merge = ['_match_key', coluna_whatsapp] + list(colunas_extras_sel)
                    # Remover duplicatas preservando ordem
                    cols_para_merge = list(dict.fromkeys(cols_para_merge))

                    resultado = df1_copy.merge(
                        df2_copy[cols_para_merge],
                        on='_match_key',
                        how='left'
                    )
                    
                    # Renomear coluna de WhatsApp
                    resultado = resultado.rename(columns={coluna_whatsapp: 'WhatsApp'})
                    
                    # Remover coluna auxiliar
                    resultado = resultado.drop('_match_key', axis=1)
                    
                    # Calcular estatísticas
                    encontrados = resultado['WhatsApp'].notna().sum()
                    nao_encontrados = resultado['WhatsApp'].isna().sum()
                    taxa_sucesso = (encontrados / len(resultado) * 100) if len(resultado) > 0 else 0
                    
                    # Exibir estatísticas
                    st.subheader("📊 Resultado da Comparação")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total de Clientes", len(resultado))
                    
                    with col2:
                        st.metric("✅ WhatsApps Encontrados", encontrados, delta=f"{taxa_sucesso:.1f}%")
                    
                    with col3:
                        st.metric("❌ Não Encontrados", nao_encontrados)
                    
                    with col4:
                        st.metric("Taxa de Sucesso", f"{taxa_sucesso:.1f}%")
                    
                    st.markdown("---")
                    
                    # Tabelas de resultado
                    tab1_res, tab2_res, tab3_res = st.tabs(["📋 Todos os Resultados", "✅ Encontrados", "❌ Não Encontrados"])
                    
                    with tab1_res:
                        st.subheader("Resultado Completo")
                        st.dataframe(resultado, use_container_width=True, height=400)
                    
                    with tab2_res:
                        encontrados_df = resultado[resultado['WhatsApp'].notna()]
                        st.subheader(f"Clientes com WhatsApp ({len(encontrados_df)})")
                        st.dataframe(encontrados_df, use_container_width=True, height=400)
                    
                    with tab3_res:
                        nao_encontrados_df = resultado[resultado['WhatsApp'].isna()]
                        st.subheader(f"Clientes Sem WhatsApp ({len(nao_encontrados_df)})")
                        st.dataframe(nao_encontrados_df, use_container_width=True, height=400)
                    
                    st.markdown("---")
                    
                    # Opções de exportação
                    st.subheader("💾 Exportar Resultados")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        csv = resultado.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 Baixar como CSV",
                            data=csv,
                            file_name=f"resultado_comparacao_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        buffer = io.BytesIO()
                        resultado.to_excel(buffer, index=False, sheet_name='Resultados')
                        buffer.seek(0)
                        st.download_button(
                            label="📥 Baixar como Excel",
                            data=buffer,
                            file_name=f"resultado_comparacao_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with col3:
                        apenas_whatsapp = resultado[['Cliente' if 'Cliente' in resultado.columns else coluna_match_1, 'WhatsApp']].dropna()
                        csv_whatsapp = apenas_whatsapp.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📱 Apenas WhatsApps",
                            data=csv_whatsapp,
                            file_name=f"whatsapps_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                except Exception as e:
                    st.error(f"❌ Erro na comparação: {e}")
                    st.info("💡 Verifique se as colunas selecionadas existem e se os dados estão no formato correto.")

    else:
        # Mensagem quando arquivos ainda não foram enviados
        st.info("👆 Por favor, envie os dois arquivos para começar a comparação.")
        
        # Mostrar exemplo de estrutura esperada
        with st.expander("📝 Ver Exemplo de Estrutura de Arquivo"):
            st.markdown("""
            **Arquivo 1 - Análise de Crédito:**
            | ID | Cliente | CNPJ/CPF | Total de Ocorrências | Integração | Tipo de consulta | Data consulta | Valor Total |
            |----|---------|----------|----------------------|------------|------------------|---------------|-------------|
            | 1 | ACME Corp | 12.345.678/0001-00 | 5 | SIM | API | 2024-01-15 | 5000.00 |
            
            **Arquivo 2 - LEADS CRM:**
            | ID | CNPJ/CPF | Cliente | WhatsApp | Email | ... |
            |----|----------|---------|----------|-------|-----|
            | 1 | 12.345.678/0001-00 | ACME Corp | 11987654321 | contact@acme.com | ... |
            """)

# ===== TAB 2: FORMATADOR DE CONTATOS OPA! =====
with tab2:
    st.subheader("Formatador de contatos para o OPA!")
    
    uploaded_file = st.file_uploader("Envie seu arquivo CSV", type=["csv"], key="opa_uploader")

    # Contatos fixos
    contatos_fixos = [
        {"name": "Matheus Mendes", "whatsapp": "(11) 94887-6252"},
    ]

    # Inicializa estado para contatos extras (manuais)
    if "contatos_extras" not in st.session_state:
        st.session_state["contatos_extras"] = []

    def encontrar_indice_padrao(colunas, palavras_chave, default=0):
        for i, col in enumerate(colunas):
            lower = str(col).lower()
            if any(k in lower for k in palavras_chave):
                return i
        return default if 0 <= default < len(colunas) else 0

    if uploaded_file:
        try:
            try:
                df = pd.read_csv(uploaded_file, sep=None, engine="python")
            except Exception:
                # Recomeça leitura com separador padrão
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=",")
            st.subheader("Colunas encontradas:")
            st.write(df.columns.tolist())

            # Seleção das colunas
            st.info("Selecione as colunas de Nome/Razão Social e WhatsApp/Celular abaixo:")
            colunas = df.columns.tolist()
            idx_nome = encontrar_indice_padrao(colunas, ["razão", "razao", "nome", "nome/"])
            idx_wh = encontrar_indice_padrao(colunas, ["whatsapp", "celular", "telefone"], default=1 if len(colunas) > 1 else 0)

            col_nome = st.selectbox("Coluna de Nome/Razão Social", colunas, index=idx_nome)
            col_whatsapp = st.selectbox("Coluna de WhatsApp/Celular", colunas, index=idx_wh)

            st.subheader("Adicionar contato manualmente")
            with st.form("adicionar_contato", clear_on_submit=True):
                nome_extra = st.text_input("Nome do contato")
                whatsapp_extra = st.text_input("WhatsApp do contato")
                adicionar = st.form_submit_button("Adicionar contato")
                if adicionar:
                    if nome_extra.strip() and whatsapp_extra.strip():
                        st.session_state["contatos_extras"].append(
                            {"name": nome_extra.strip(), "whatsapp": whatsapp_extra.strip()}
                        )
                        st.success("Contato adicionado.")
                    else:
                        st.error("Preencha nome e WhatsApp antes de adicionar.")

            # Remover contatos manuais
            if st.session_state["contatos_extras"]:
                st.subheader("Contatos manuais adicionados")
                for idx, contato in enumerate(st.session_state["contatos_extras"]):
                    col1, col2 = st.columns([4,1])
                    col1.write(f"{contato['name']} — {contato['whatsapp']}")
                    if col2.button("Remover", key=f"remover_{idx}"):
                        st.session_state["contatos_extras"].pop(idx)

            # Verifica seleção e formata saída
            if col_nome and col_whatsapp:
                df_formatado = df[[col_nome, col_whatsapp]].copy()
                df_formatado.columns = ["name", "whatsapp"]

                contatos_df = pd.DataFrame(contatos_fixos + st.session_state["contatos_extras"])
                df_final = pd.concat([contatos_df, df_formatado], ignore_index=True)

                csv = df_final.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar CSV formatado",
                    data=csv.encode("utf-8"),
                    file_name="contatos_formatado.csv",
                    mime="text/csv"
                )

                st.success("Colunas selecionadas com sucesso!")
                st.subheader("Pré-visualização:")
                st.dataframe(df_final)

                st.subheader("Resultado Formatado (texto com vírgula):")
                resultado_texto = "\n".join(f"{row['name']}, {row['whatsapp']}" for _, row in df_final.iterrows())
                st.code(resultado_texto, language="text")
            else:
                st.error("Selecione as colunas corretamente.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# ===== RODAPÉ =====
st.markdown("""
<style>
    .stButton>button {background-color: #01B1F2; color: white; font-weight: bold;}
    .stDataFrame {border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: #999; margin-top: 50px;">
    <p>Desenvolvido por MATH NETFIT(The legend) - Auxiliar de Sistemas</p>
    <small>Versão 1.0 | 2026 | Comparador de Clientes + Formatador OPA!</small>
</div>
""", unsafe_allow_html=True)
