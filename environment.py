# environment.py
import pandas as pd
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class EnvironmentAgent(Agent):
    class EnvironmentBehaviour(CyclicBehaviour):
        async def run(self):
            print("[Env] waiting for messages")
            # Wait indefinitely for a message
            msg = await self.receive(timeout=200)  # Wait until a message is received
            print(f"[env] Received message: {msg.body}")
            if msg:
                

                response = Message(to=str(msg.sender))  # Create a response message to the sender
                response.set_metadata("performative", "inform")  # Metadata to define the message purpose

                # Process the message based on its metadata
                if msg.metadata and "type" in msg.metadata:
                    if msg.metadata["type"] == "energy_price_update":
                        price = self.agent.get_price_for_current_hour()
                        self.agent.date += pd.Timedelta(hours=1)
                        response.body = str(price)
                        response.set_metadata("type", "energy_price")
                    elif msg.metadata["type"] == "outside_temperature":
                        wheater = self.agent.get_weather_for_each_hour()
                        response.body = str(wheater)
                        response.set_metadata("type", "outside_temperature_response")
                    elif msg.metadata["type"] == "inside_temperature":
                        temp = self.agent.get_indoor_temperature()
                        response.set_metadata("type", "inside_temperature")
                        response.body = str(temp)
                    elif msg.metadata["type"] == "room_temperature_update":
                        self.agent.update_room_temperature(float(msg.body))
                        response.set_metadata("type", "room_temperature_response")
                    else:
                        print(f"Unknown message type: {msg.metadata['type']}")
                        response.set_metadata("type", "error_response")
                else:
                    print("Message received without valid metadata.")
                    response.body = "Error: Message metadata missing or invalid"
                    response.set_metadata("type", "error_response")

                # Send the response message
                if(msg.metadata["type"] != "room_temperature_update"):
                    await self.send(response)
                print(f"[{self.agent.date}] Sent response: {response.body}")


            
    
    def __init__(self, jid, password, date, city, num_divisions, desired_temperature):
        super().__init__(jid, password)
        self.date = pd.to_datetime(date)  # Simulation date
        self.city = city
        self.num_divisions = num_divisions
        self.desired_temperature = desired_temperature

        # Placeholders for data to be loaded later
        self.weather_data = None
        self.energy_data = None
        self.energy_prices = None
        self.season = None
        self.indoor_temperature = None
        self.weather_hour = None

    async def setup(self):
        print(f"Agent {self.name} starting...")
        # Load initial data during setup
        self.weather_data = self.load_weather_data()
        self.energy_data = self.load_energy_data()
        self.energy_prices = self.get_energy_prices()
        self.season = self.determine_season()
        self.indoor_temperature = self.set_standard_indoor_temperature()
        self.weather_hour = self.get_weather_for_each_hour()

        # Add the cyclic behavior
        monitor_behaviour = self.EnvironmentBehaviour()
        self.add_behaviour(monitor_behaviour)

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


    def get_weather_for_each_hour(self):
        # Normaliza a hora atual para o início da hora (sem minutos, segundos, etc.)
        current_hour = self.date.replace(minute=0, second=0, microsecond=0)
        print(f"Consultando dados meteorológicos para a hora: {current_hour.isoformat()}")

        try:
            # Primeiro, tenta buscar diretamente em UTC
            current_hour_utc = current_hour.tz_convert('UTC')
            weather_data = self.weather_data.get(current_hour_utc)

            if weather_data is None:
                print(f"Dados meteorológicos não encontrados em UTC, tentando UTC+1.")
                # Tenta UTC+1 se não encontrar em UTC
                current_hour_utc1 = current_hour.tz_convert('Europe/Berlin')  # UTC+1
                weather_data = self.weather_data.get(current_hour_utc1)

                if weather_data is None:
                    print(f"Dados meteorológicos não encontrados em UTC+1, tentando UTC+2.")
                    # Tenta UTC+2 se não encontrar em UTC+1
                    current_hour_utc2 = current_hour.tz_convert('Europe/Istanbul')  # UTC+2
                    weather_data = self.weather_data.get(current_hour_utc2)

                    if weather_data is not None:
                        print(f"Dados meteorológicos encontrados em UTC+2: {weather_data}")
                    else:
                        print(f"Dados meteorológicos não encontrados em UTC+2.")
                else:
                    print(f"Dados meteorológicos encontrados em UTC+1: {weather_data}")
            else:
                print(f"Dados meteorológicos encontrados em UTC: {weather_data}")

            return weather_data

        except Exception as e:
            print(f"Erro ao processar a data {self.date}: {e}")
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
            return 20.0  # Exemplo de temperatura padrão para o Inverno
        elif self.season == "Primavera":
            return 22.0  # Temperatura padrão para a Primavera
        elif self.season == "Verão":
            return 24.0  # Temperatura padrão para o Verão
        else:  # Outono
            return 21.0  # Temperatura padrão para o Outono

    def get_indoor_temperature(self):
        # Retorna a temperatura interior
        return self.indoor_temperature

    def verify_season(self):
        print(f"A data {self.date.date()} corresponde à estação: {self.season}.")
        
    def update_room_temperature(self,degrees_heated):
        self.indoor_temperature += degrees_heated
    
    def decrease_temperature(self):
        self.indoor_temperature -= .5 #needs a function to load external temperature
        