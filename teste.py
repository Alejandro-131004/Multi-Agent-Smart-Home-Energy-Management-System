# environment.py
import pandas as pd

class Environment:
    def __init__(self, date, city, num_divisions):
        self.date = pd.to_datetime(date)  # Data da simulação
        self.city = city
        self.num_divisions = num_divisions
        
        # Carregar dados climáticos e de energia
        self.weather_data = self.load_weather_data()  # Carrega dados climáticos
        self.energy_data = self.load_energy_data()  # Carrega dados de energia
        self.energy_prices = self.get_energy_prices()  # Obtém preços de energia

        self.season = self.determine_season()  # Determina a estação do ano
        self.indoor_temperature_standard = self.set_standard_indoor_temperature()  # Define a temperatura padrão

    def load_weather_data(self):
        try:
            # Carrega os dados do CSV de clima
            weather_df = pd.read_csv('weather_features.csv', parse_dates=['dt_iso'])
            print("Dados meteorológicos carregados com sucesso:")
            print(weather_df.head())  # Exibe as primeiras linhas do DataFrame para debug
            
            # Filtra os dados pela cidade
            city_data = weather_df[weather_df['city_name'] == self.city]
            print(f"Dados filtrados para a cidade {self.city}:")
            print(city_data.head())  # Exibe os dados filtrados

            # Filtra os dados com base na data/hora
            filtered_data = city_data[city_data['dt_iso'] == self.date]
            print(f"Dados meteorológicos para {self.city} em {self.date}:")
            print(filtered_data)  # Verifique o resultado da filtragem

            if filtered_data.empty:
                print("Nenhum dado meteorológico encontrado para esta data e hora.")
                return None

            # Conversão de temperatura de Kelvin para Celsius
            filtered_data['temp'] -= 273.15  # Converte Kelvin para Celsius
            filtered_data['temp_min'] -= 273.15  # Converte para Celsius
            filtered_data['temp_max'] -= 273.15  # Converte para Celsius

            return filtered_data.iloc[0]
        except FileNotFoundError:
            print("O arquivo 'weather_features.csv' não foi encontrado.")
            return None

    def display_weather_data(self):
        if self.weather_data is not None:
            print(f"Weather data for {self.city} at {self.date.hour:02d} hours:")
            print(f"Temperature: {self.weather_data['temp']:.2f} °C")
            print(f"Min Temperature: {self.weather_data['temp_min']:.2f} °C")
            print(f"Max Temperature: {self.weather_data['temp_max']:.2f} °C")
            print(f"Pressure: {self.weather_data['pressure']} hPa")
            print(f"Humidity: {self.weather_data['humidity']}%")
            print(f"Wind Speed: {self.weather_data['wind_speed']} m/s")
            print(f"Weather: {self.weather_data['weather_description']}")
        else:
            print("No weather data available.")

    def load_energy_data(self):
        try:
            # Carrega os dados de energia de um CSV (substitua pelo seu arquivo real)
            energy_df = pd.read_csv('energy_data.csv', parse_dates=['time'])
            print("Dados de energia carregados com sucesso:")
            print(energy_df.head())  # Exibe as primeiras linhas do DataFrame para debug
            return energy_df
        except FileNotFoundError:
            print("O arquivo 'energy_data.csv' não foi encontrado.")
            return None

    def get_energy_prices(self):
        if self.energy_data is not None:
            self.energy_data['date_time'] = pd.to_datetime(self.energy_data['time'], errors='coerce')
            prices = self.energy_data.set_index('date_time')['price actual'].to_dict()
            print("Preços de energia obtidos com sucesso.")
            return prices
        else:
            print("Nenhum dado de energia disponível.")
            return {}

    def get_price_for_current_hour(self):
        current_hour = self.date.replace(minute=0, second=0, microsecond=0)
        print(f"Consultando preço para a hora: {current_hour.isoformat()}")

        current_hour_utc1 = current_hour.tz_localize('UTC+01:00')
        price = self.energy_prices.get(current_hour_utc1)

        if price is None:
            print(f"Preço não encontrado em UTC+1, tentando UTC+2.")
            current_hour_utc2 = current_hour.tz_localize('UTC+02:00')
            price = self.energy_prices.get(current_hour_utc2)

            if price is not None:
                print(f"Preço encontrado em UTC+2: {price}")
            else:
                print(f"Preço não encontrado em UTC+2.")
        else:
            print(f"Preço encontrado em UTC+1: {price}")

        return price

    def determine_season(self):
        month = self.date.month
        if month in [12, 1, 2]:
            return "Inverno"
        elif month in [3, 4, 5]:
            return "Primavera"
        elif month in [6, 7, 8]:
            return "Verão"
        else:
            return "Outono"

    def set_standard_indoor_temperature(self):
        if self.season == "Inverno":
            return 20  # Exemplo de temperatura padrão para o Inverno
        elif self.season == "Primavera":
            return 22  # Temperatura padrão para a Primavera
        elif self.season == "Verão":
            return 24  # Temperatura padrão para o Verão
        else:  # Outono
            return 21  # Temperatura padrão para o Outono

    def get_indoor_temperature(self):
        # Retorna a temperatura interior
        return self.indoor_temperature_standard

    def verify_season(self):
        print(f"A data {self.date.date()} corresponde à estação: {self.season}.")

# Exemplo de uso
if __name__ == "__main__":
    env = Environment('2015-01-01 00:00:00', 'Cidade Exemplo', 5)
    env.display_weather_data()
    current_price = env.get_price_for_current_hour()
    print(f"Current energy price: {current_price}")
    env.verify_season()
