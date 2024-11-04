import pandas as pd

# Carregar a planilha
tabela = pd.read_excel('tabela_precos.xlsx', sheet_name='Hidráulica')

# Exibir os nomes das colunas
print(tabela.columns)
