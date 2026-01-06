# 🔍 Comparador de Clientes NETFI

Aplicativo Streamlit para comparar bases de dados e identificar WhatsApps de clientes.

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip

### Passos

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o aplicativo:
```bash
streamlit run app.py
```

3. O navegador abrirá automaticamente em `http://localhost:8501`

## 📋 Como Usar

1. **Upload Arquivo 1**: Carregue a planilha com os clientes que deseja consultar
   - Deve conter: ID, Cliente, CNPJ/CPF, Total de Ocorrências, Integração, Tipo de consulta, Data consulta, Valor Total

2. **Upload Arquivo 2**: Carregue a base de dados completa do sistema NETFI
   - Deve conter: Identificadores (ID, CNPJ/CPF) e coluna de WhatsApp

3. **Configurar Comparação**:
   - Selecione a coluna de matching no Arquivo 1 (geralmente ID ou CNPJ/CPF)
   - Selecione a coluna de matching no Arquivo 2 (coluna correspondente)
   - Selecione a coluna de WhatsApp no Arquivo 2

4. **Comparar**: Clique no botão "Comparar e Encontrar WhatsApps"

5. **Visualizar e Exportar**: 
   - Veja os resultados em abas separadas
   - Baixe como CSV ou Excel

## 📊 Recursos

- ✅ Suporta CSV e Excel
- ✅ Normalização automática de dados (maiúsculas, espaços)
- ✅ Estatísticas em tempo real
- ✅ Visualização de resultados em abas
- ✅ Exportação em múltiplos formatos
- ✅ Cálculo automático de taxa de sucesso

## 📁 Estrutura de Arquivos

```
COMPARADOR_CLIENTES/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências
└── README.md          # Este arquivo
```

## 💡 Dicas

- Se as colunas tiverem nomes diferentes nos dois arquivos, selecione as colunas correspondentes
- O app detecta automaticamente colunas com nomes como "ID", "CNPJ", "CPF", "WhatsApp", "Celular"
- Certifique-se de que os identificadores estão em formato consistente (com ou sem formatação)

## 🆘 Troubleshooting

### Erro ao carregar arquivo
- Verifique se o arquivo está no formato CSV ou Excel
- Certifique-se de que o arquivo não está corrompido

### Nenhum WhatsApp encontrado
- Verifique se o identificador (ID/CNPJ/CPF) está igual nos dois arquivos
- Confira se há espaços ou caracteres especiais extras
- Valide se a coluna de WhatsApp existe e tem dados preenchidos

## 👨‍💼 Autor
Desenvolvido para NETFI - Provedora de Internet

## 📝 Versão
1.0 - Janeiro 2025
