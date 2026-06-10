import streamlit as st
import pdfplumber
import pandas as pd
import io
import os

# Configuração da página
st.set_page_config(
    page_title="PDF para Excel",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.title("📄 Conversor PDF para Excel")
st.markdown("Converta tabelas de PDFs para arquivos Excel de forma rápida e fácil!")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    st.markdown("---")
    
    st.subheader("Formatos Suportados")
    st.write("- 📊 Tabelas em PDF")
    st.write("- 📈 Dados estruturados")
    
    st.markdown("---")
    st.subheader("⚙️ Opções Avançadas")
    
    estrategia = st.radio(
        "Estratégia de Extração:",
        options=["Automática (Recomendado)", "Apenas Linhas", "Apenas Texto"],
        help="Escolha a estratégia de detecção de tabelas"
    )
    
    st.markdown("---")
    st.info("💡 **Dica**: PDFs com tabelas bem estruturadas geram melhores resultados.")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1️⃣ Upload do PDF")
    uploaded_file = st.file_uploader(
        "Selecione um arquivo PDF",
        type="pdf",
        help="Escolha um arquivo PDF contendo tabelas"
    )

selected_page = None

if uploaded_file:
    with col2:
        st.subheader("2️⃣ Opções de Conversão")
        
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                num_pages = len(pdf.pages)
            
            st.info(f"📑 Total de páginas: **{num_pages}**")
            
            if num_pages > 1:
                page_range = st.radio(
                    "Qual página deseja processar?",
                    options=["Todas", "Página específica"],
                    horizontal=True
                )
                
                if page_range == "Página específica":
                    selected_page = st.number_input(
                        "Selecione a página",
                        min_value=1,
                        max_value=num_pages,
                        value=1
                    ) - 1
            else:
                selected_page = 0
        except Exception as e:
            st.error(f"❌ Erro ao ler o PDF: {str(e)}")
            st.stop()

# Seção de processamento
if uploaded_file:
    st.markdown("---")
    st.subheader("3️⃣ Resultado da Conversão")
    
    if st.button("🔍 Processar PDF", use_container_width=True, key="process_button"):
        try:
            with st.spinner("⏳ Processando PDF... Isso pode levar alguns segundos."):
                all_tables = []
                
                with pdfplumber.open(uploaded_file) as pdf:
                    if selected_page is not None:
                        pages_to_process = [selected_page]
                    else:
                        pages_to_process = range(len(pdf.pages))
                    
                    for page_idx in pages_to_process:
                        page = pdf.pages[page_idx]
                        tables = None
                        
                        # Aplicar estratégia selecionada
                        if estrategia == "Automática (Recomendado)":
                            tables = page.extract_tables()
                            if not tables:
                                tables = page.extract_tables(
                                    table_settings={
                                        "vertical_strategy": "lines",
                                        "horizontal_strategy": "lines",
                                    }
                                )
                            if not tables:
                                tables = page.extract_tables(
                                    table_settings={
                                        "vertical_strategy": "lines_strict",
                                        "horizontal_strategy": "lines_strict",
                                    }
                                )
                            if not tables:
                                tables = page.extract_tables(
                                    table_settings={
                                        "vertical_strategy": "text",
                                        "horizontal_strategy": "text",
                                        "text_tolerance": 3,
                                    }
                                )
                        
                        elif estrategia == "Apenas Linhas":
                            tables = page.extract_tables(
                                table_settings={
                                    "vertical_strategy": "lines",
                                    "horizontal_strategy": "lines",
                                }
                            )
                        
                        elif estrategia == "Apenas Texto":
                            tables = page.extract_tables(
                                table_settings={
                                    "vertical_strategy": "text",
                                    "horizontal_strategy": "text",
                                    "text_tolerance": 3,
                                }
                            )
                        
                        if tables:
                            for table in tables:
                                if table and len(table) > 0:
                                    try:
                                        df = pd.DataFrame(
                                            table[1:], 
                                            columns=table[0]
                                        ) if len(table) > 1 else pd.DataFrame(table)
                                        
                                        if not df.empty:
                                            df.insert(0, '_page', page_idx + 1)
                                            all_tables.append(df)
                                    except:
                                        continue
                
                if all_tables:
                    resultado_df = pd.concat(all_tables, ignore_index=True)
                    
                    st.success("✅ Tabelas encontradas e extraídas com sucesso!")
                    
                    with st.expander("📊 Visualizar Dados Extraídos", expanded=True):
                        st.dataframe(resultado_df, use_container_width=True)
                        
                        st.markdown(f"""
                        **Estatísticas:**
                        - Linhas: {len(resultado_df)}
                        - Colunas: {len(resultado_df.columns)}
                        """)
                    
                    excel_buffer = io.BytesIO()
                    
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        resultado_df.to_excel(writer, sheet_name='Dados', index=False)
                        
                        worksheet = writer.sheets['Dados']
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            
                            adjusted_width = min(max_length + 2, 50)
                            worksheet.column_dimensions[column_letter].width = adjusted_width
                    
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Baixar Excel",
                        data=excel_buffer,
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Nenhuma tabela foi detectada no PDF!")
                    
                    with st.expander("💡 Como resolver este problema?", expanded=True):
                        st.markdown("""
                        **Possíveis causas:**
                        - O PDF contém tabelas como imagens (OCR seria necessário)
                        - As tabelas não têm bordas/linhas bem visíveis
                        - O arquivo contém apenas texto, não tabelas estruturadas
                        
                        **Soluções:**
                        - ✓ Tente uma estratégia diferente na sidebar
                        - ✓ Verifique se o PDF tem tabelas com linhas visíveis
                        - ✓ Exporte a tabela em um novo PDF mais simples
                        - ✓ Teste com outro PDF para confirmar
                        """)
                    
                    st.info("📌 Use a estratégia 'Apenas Texto' para PDFs com texto bem espaçado")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar: {str(e)}")
            st.info("💡 Tente novamente ou escolha outro PDF")

else:
    st.info("👆 Selecione um arquivo PDF para começar!")
