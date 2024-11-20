# environment.py
import pandas as pd
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
from pytz import timezone, UTC


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
                        print(self.agent.date)
                        self.agent.date += pd.Timedelta(hours=1)
                        print(self.agent.date)
                        response.body = str(price)
                        response.set_metadata("type", "energy_price")

                    elif msg.metadata["type"] == "outside_temperature":
                        weather = self.agent.get_weather_for_each_hour()
                        #self.agent.date += pd.Timedelta(hours=1)
                        response.body = str(weather)  # Já em Celsius
                        response.set_metadata("type", "outside_temperature_response")

                    elif msg.metadata["type"] == "inside_temperature":
                        temp = self.agent.get_indoor_temperature()
                        response.set_metadata("type", "inside_temperature")
                        response.body = str(temp)

                    elif msg.metadata["type"] == "room_temperature_update_heat":
                        self.agent.update_room_temperature_heat(float(msg.body))
                        response.set_metadata("type", "room_temperature_response_heat")

                    elif msg.metadata["type"] == "room_temperature_update_cold":
                        self.agent.update_room_temperature_cold(float(msg.body))
                        response.set_metadata("type", "room_temperature_response_cold")

                    elif msg.metadata["type"] == "temperature_data":
                        inside_temp = self.agent.get_indoor_temperature()
                        outside_temp = self.agent.get_weather_for_each_hour()  # Já em Celsius
                        response.body = f"{inside_temp},{outside_temp}"
                        response.set_metadata("type", "temperature_data")

                    else:
                        print(f"Unknown message type: {msg.metadata['type']}")
                        response.set_metadata("type", "error_response")
                else:
                    print("Message received without valid metadata.")
                    response.body = "Error: Message metadata missing or invalid"
                    response.set_metadata("type", "error_response")

                # Send the response message
                if msg.metadata["type"] != "room_temperature_update_heat" and msg.metadata["type"] != "room_temperature_update_cold":
                    await self.send(response)
                print(f"[{self.agent.date}] Sent response: {response.body}")



    def __init__(self, jid, password, date, city, num_divisions, desired_temperature):
        super().__init__(jid, password)
        self.date = pd.to_datetime(date)  # Simulation date
        self.city = city
        self.num_divisions = num_divisions
        self.desired_temperature = desired_temperature

        # Placeholders for data to be loaded later
        self.weather_time = None
        self.weather_data = None
        self.energy_data = None
        self.energy_prices = None
        self.season = None
        self.indoor_temperature = None

    async def setup(self):

        print(f"Agent {self.name} starting...")
        # Load initial data during setup
        self.weather_data = self.load_weather_data()
        self.energy_data = self.load_energy_data()

        self.weather_time = self.get_weather_time()
        self.energy_prices = self.get_energy_prices()

        self.season = self.determine_season()
        self.indoor_temperature = self.set_standard_indoor_temperature()

        # Add the cyclic behavior
        monitor_behaviour = self.EnvironmentBehaviour()
        self.add_behaviour(monitor_behaviour)

    def convert_kelvin_to_celsius(self, kelvin):
        try:
            return round(kelvin - 273.15, 5)
        except TypeError:
            print(f"Erro ao converter {kelvin} para Celsius. Verifique os dados.")
            return None

    def load_weather_data(self):
        try:
            # Carrega os dados meteorológicos do CSV
            weather_df = pd.read_csv('weather_features.csv', parse_dates=['dt_iso'])

            # Filtra os dados para a cidade especificada
            weather_df = weather_df[weather_df['city_name'] == self.city]

            if weather_df.empty:
                print(f"Nenhum dado meteorológico encontrado para a cidade {self.city}.")
                return None

            print(f"Dados meteorológicos para {self.city} carregados com sucesso:")
            print(weather_df.head())  # Exibe as primeiras linhas do DataFrame para debug
            return weather_df
        except FileNotFoundError:
            print("O arquivo 'weather_features.csv' não foi encontrado.")
            return None

    def get_weather_time(self):
        if self.weather_data is not None:
            # Converte a coluna de tempo para datetime
            self.weather_data['dt_iso'] = pd.to_datetime(self.weather_data['dt_iso'], errors='coerce')

            # Transforma em dicionário com 'dt_iso' como chave e 'temp' como valor
            weather_dict = self.weather_data.set_index('dt_iso')['temp'].to_dict()

            print("Dados meteorológicos processados com sucesso.")
            return weather_dict
        else:
            print("Nenhum dado meteorológico disponível.")
            return {}

    def get_weather_for_each_hour(self):
        # Normaliza a hora atual para o início da hora
        current_hour = self.date.replace(minute=0, second=0, microsecond=0)
        print(f"Consultando dados meteorológicos para a hora: {current_hour.isoformat()}")

        try:
            # Garante que o horário atual está em UTC+1 (como no CSV)
            current_hour_utc1 = current_hour.tz_localize('Europe/Berlin', ambiguous='NaT')
            print(f"Hora em UTC+1: {current_hour_utc1}")

            # Busca os dados no dicionário
            weather = self.weather_time.get(current_hour_utc1)

            if weather is not None:
                print(f"Dados meteorológicos encontrados: {weather} (em Kelvin)")

                # Converte para Celsius antes de retornar
                weather_celsius = self.convert_kelvin_to_celsius(weather)
                print(f"Temperatura em Celsius: {weather_celsius:.5f}°C")
                return weather_celsius
            else:
                print(f"Dados meteorológicos não encontrados para {current_hour_utc1}.")
                return None
        except Exception as e:
            print(f"Erro ao consultar os dados meteorológicos: {e}")
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

        # Localiza o timestamp como UTC+1
        current_hour_utc1 = current_hour.tz_localize('Europe/Berlin',
                                                     ambiguous='NaT')  # Ambiguous evita problemas com transições de horário de verão

        price = self.energy_prices.get(current_hour_utc1)

        if price is None:
            print(f"Preço não encontrado em UTC+1, tentando UTC+2.")
            current_hour_utc2 = current_hour_utc1.tz_convert('Europe/Istanbul')  # UTC+2
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

    def update_room_temperature_heat(self, degrees_heated):
        print("Ni")
        self.indoor_temperature += degrees_heated

    def update_room_temperature_cold(self, degrees_cooled):
        print("niiiii")
        self.indoor_temperature -= degrees_cooled  # needs a function to load external temperature