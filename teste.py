import pandas as pd

try:
    weather_data = pd.read_csv('weather_features.csv')
    print("[Info] Dados meteorológicos carregados com sucesso.")
except FileNotFoundError:
    print("[Error] Arquivo CSV de dados meteorológicos não encontrado.")
