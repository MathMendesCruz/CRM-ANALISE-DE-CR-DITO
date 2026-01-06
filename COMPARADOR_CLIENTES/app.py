import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Comparador de Clientes NETFI", layout="wide")

st.title("🔍 Comparador de Clientes NETFI")
st.markdown("Identifique os WhatsApps dos clientes comparando duas bases de dados")

# Sidebar para instruções
with st.sidebar:
    st.markdown("### 📋 Instruções")
    st.markdown("""
    1. **Arquivo 1**: Planilha de clientes a consultar
    2. **Arquivo 2**: Base de dados completa do sistema NETFI
    3. O app vai encontrar o WhatsApp dos clientes do Arquivo 1
    """)

# Seção de upload de arquivos
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Arquivo 1: Clientes a Consultar")
    arquivo1 = st.file_uploader(
        "Selecione o arquivo com os clientes a consultar",
        type=["csv", "xlsx", "xls"],
        key="arquivo1"
    )

with col2:
    st.subheader("📁 Arquivo 2: Base de Dados NETFI")
    arquivo2 = st.file_uploader(
        "Selecione a base de dados completa do sistema",
        type=["csv", "xlsx", "xls"],
        key="arquivo2"
    )

# Função para carregar arquivo
def carregar_arquivo(arquivo):
    try:
        if arquivo.name.endswith('.csv'):
            return pd.read_csv(arquivo)
        else:
            return pd.read_excel(arquivo)
    except Exception as e:
        st.error(f"❌ Erro ao carregar arquivo: {e}")
        return None

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
            coluna_match_1 = st.selectbox(
                "Coluna para matching (Arquivo 1):",
                df1.columns,
                index=colunas_id_arquivo1[0] if colunas_id_arquivo1 else 0,
                key="col_match_1"
            )
        
        with col2:
            colunas_id_arquivo2 = [col for col in df2.columns if 'id' in col.lower() or 'cnpj' in col.lower() or 'cpf' in col.lower()]
            coluna_match_2 = st.selectbox(
                "Coluna para matching (Arquivo 2):",
                df2.columns,
                index=colunas_id_arquivo2[0] if colunas_id_arquivo2 else 0,
                key="col_match_2"
            )
        
        with col3:
            # Detectar coluna de WhatsApp
            colunas_whatsapp = [col for col in df2.columns if 'whatsapp' in col.lower() or 'celular' in col.lower() or 'telefone' in col.lower()]
            coluna_whatsapp = st.selectbox(
                "Coluna de WhatsApp (Arquivo 2):",
                df2.columns,
                index=colunas_whatsapp[0] if colunas_whatsapp else 0,
                key="col_whatsapp"
            )
        
        st.markdown("---")
        
        # Realizar comparação
        if st.button("🔍 Comparar e Encontrar WhatsApps", type="primary", use_container_width=True):
            try:
                # Fazer merge dos DataFrames
                # Primeiro, normalizar os valores para comparação (maiúsculas, sem espaços)
                df1_copy = df1.copy()
                df2_copy = df2.copy()
                
                # Normalizar colunas de matching
                df1_copy['_match_key'] = df1_copy[coluna_match_1].astype(str).str.strip().str.upper()
                df2_copy['_match_key'] = df2_copy[coluna_match_2].astype(str).str.strip().str.upper()
                
                # Realizar merge
                resultado = df1_copy.merge(
                    df2_copy[['_match_key', coluna_whatsapp]],
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
                tab1, tab2, tab3 = st.tabs(["📋 Todos os Resultados", "✅ Encontrados", "❌ Não Encontrados"])
                
                with tab1:
                    st.subheader("Resultado Completo")
                    st.dataframe(resultado, use_container_width=True, height=400)
                
                with tab2:
                    encontrados_df = resultado[resultado['WhatsApp'].notna()]
                    st.subheader(f"Clientes com WhatsApp ({len(encontrados_df)})")
                    st.dataframe(encontrados_df, use_container_width=True, height=400)
                
                with tab3:
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
        **Arquivo 1 - Clientes a Consultar:**
        | ID | Cliente | CNPJ/CPF | Total de Ocorrências | Integração | Tipo de consulta | Data consulta | Valor Total |
        |----|---------|----------|----------------------|------------|------------------|---------------|-------------|
        | 1 | ACME Corp | 12.345.678/0001-00 | 5 | SIM | API | 2024-01-15 | 5000.00 |
        
        **Arquivo 2 - Base de Dados NETFI:**
        | ID | CNPJ/CPF | Cliente | WhatsApp | Email | ... |
        |----|----------|---------|----------|-------|-----|
        | 1 | 12.345.678/0001-00 | ACME Corp | 11987654321 | contact@acme.com | ... |
        """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999;">
    <p>Desenvolvido para NETFI - Provedora de Internet</p>
    <small>Versão 1.0 | 2025</small>
</div>
""", unsafe_allow_html=True)
