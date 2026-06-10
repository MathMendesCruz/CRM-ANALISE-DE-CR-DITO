# 📄 Conversor PDF para Excel

Uma aplicação web simples e intuitiva para converter tabelas de PDFs para arquivos Excel.

## 🚀 Recursos

- ✅ Upload de arquivos PDF
- 📊 Extração automática de tabelas
- 📑 Suporte para PDFs com múltiplas páginas
- 📈 Conversão para Excel com formatação automática
- ⬇️ Download direto do arquivo convertido
- 🎨 Interface amigável com Streamlit

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 📦 Instalação

1. **Clone ou navegue até o diretório do projeto:**
   ```bash
   cd "PDF TO EXCEL"
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Como Usar

1. **Inicie a aplicação:**
   ```bash
   streamlit run app.py
   ```

2. **A aplicação abrirá no seu navegador padrão** (geralmente em `http://localhost:8501`)

3. **Siga os passos:**
   - 📤 Faça upload de um arquivo PDF
   - ⚙️ Configure as opções (selecione página, se necessário)
   - 👁️ Visualize os dados extraídos
   - ⬇️ Baixe o arquivo Excel

## 💡 Dicas de Uso

- **PDFs estruturados**: Para melhores resultados, use PDFs com tabelas bem estruturadas
- **Múltiplas páginas**: A aplicação pode processar uma página específica ou todas as páginas
- **Compatibilidade**: O arquivo gerado é compatível com Excel, Google Sheets e LibreOffice

## 🛠️ Dependências Principais

| Pacote | Versão | Função |
|--------|--------|--------|
| streamlit | 1.41.1 | Framework web |
| pandas | 2.1.3 | Processamento de dados |
| pdfplumber | 10.3 | Extração de tabelas de PDF |
| openpyxl | 3.11.2 | Criação de arquivos Excel |

## 📝 Estrutura do Projeto

```
PDF TO EXCEL/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências do projeto
└── README.md          # Este arquivo
```

## ⚠️ Limitações

- Funciona melhor com PDFs que contêm tabelas estruturadas
- PDFs com imagens ou textos não estruturados podem não extrair corretamente
- O tamanho máximo de arquivo depende da memória disponível

## 🐛 Solução de Problemas

### "Nenhuma tabela encontrada"
- Verifique se o PDF contém tabelas bem estruturadas
- Tente uma página específica se o PDF tiver múltiplas páginas

### "Erro ao processar o PDF"
- Certifique-se de que o arquivo não está corrompido
- Tente com outro PDF para confirmar

### Módulo não encontrado
- Execute `pip install -r requirements.txt` novamente
- Verifique se o Python está no PATH do seu sistema

## 📧 Suporte

Para dúvidas ou problemas, verifique o arquivo do PDF e tente novamente com um arquivo diferente.

## 📄 Licença

Uso livre para fins pessoais e comerciais.
