import pandas as pd

# Leitura do arquivo CSV
df = pd.read_csv('energy_dataset.csv')

# Exibe as primeiras linhas do DataFrame para ver a estrutura
print(df.head())