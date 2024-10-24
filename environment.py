# environment.py
import pandas as pd

class Environment:
    def __init__(self, date, city, num_divisions,desired_temperature):
        self.date = pd.to_datetime(date)  # Data da simulação
        self.city = city
        self.num_divisions = num_divisions
        self.desired_temperature=desired_temperature
        
        # Carregar dados climáticos e de energia
        self.weather_data = self.load_weather_data()  # Carrega dados climáticos
        self.energy_data = self.load_energy_data()  # Carrega dados de energia
        self.energy_prices = self.get_energy_prices()  # Obtém preços de energia

        self.season = self.determine_season()  # Determina a estação do ano
        self.indoor_temperature_standard = self.set_standard_indoor_temperature()  # Define a temperatura padrão

    def load_weather_data(self):
        try:
            # Carrega os dados do CSV de clima, garantindo que 'dt_iso' é tratado como datetime com fuso horário
            weather_df = pd.read_csv('weather_features.csv', parse_dates=['dt_iso'])
            
            print("Dados meteorológicos carregados com sucesso:")
            
            # Verifica se a coluna dt_iso é do tipo datetime com timezone
            if weather_df['dt_iso'].dtype != 'datetime64[ns, UTC]':
                weather_df['dt_iso'] = pd.to_datetime(weather_df['dt_iso'], utc=True)

            # Filtra os dados pela cidade
            city_data = weather_df[weather_df['city_name'] == self.city]

            # Verifique se self.date tem timezone, e ajusta para UTC se não tiver
            if self.date.tzinfo is None:
                self.date = self.date.tz_localize('UTC')
            
            # Normaliza ambas as datas para garantir que a comparação seja feita apenas até a hora exata
            self.date = self.date.normalize()
            city_data.loc[:, 'dt_iso'] = city_data['dt_iso'].dt.normalize()

            # Filtra os dados com base na data/hora normalizada
            filtered_data = city_data[city_data['dt_iso'] == self.date]
            filtered_data= filtered_data.reset_index(drop=True)
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
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
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
            energy_df = pd.read_csv('energy_dataset.csv', parse_dates=['time'])
            print("Dados de energia carregados com sucesso:")
            print(energy_df.head())  # Exibe as primeiras linhas do DataFrame para debug
            return energy_df
        except FileNotFoundError:
            print("O arquivo 'energy_dataset.csv' não foi encontrado.")
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

            # Como current_hour já tem fuso horário, use tz_convert em vez de tz_localize
            current_hour_utc1 = current_hour.tz_convert('Europe/Berlin')  # UTC+1 para o inverno
            price = self.energy_prices.get(current_hour_utc1)

            if price is None:
                print(f"Preço não encontrado em UTC+1, tentando UTC+2.")
                current_hour_utc2 = current_hour.tz_convert('Europe/Istanbul')  # UTC+2
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
        
    def update_room_temperature(self,degrees_heated):
        return self.season