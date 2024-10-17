from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time


'''class EnergyAgent:
    def __init__(self, name, password, environment):
        self.name = name
        self.password = password
        self.environment = environment
        self.current_price = None  # Initialize the current price variable

    def start(self):
        print(f"{self.name} agent started.")

    def stop(self):
        print(f"{self.name} agent stopped.")

    def update_price(self):
        """Update the current price from the environment."""
        self.current_price = self.environment.get_price_for_current_hour()

    def act_on_price(self):
        """Take action based on the current energy price."""
        if self.current_price is not None:
            print(f"{self.name} received energy price: {self.current_price}")

            # Example decision-making based on price
            if self.current_price < 0.15:  # If the price is low, suggest using more energy
                print(f"{self.name}: It's a good time to consume more energy.")
            elif self.current_price > 0.30:  # If the price is high, suggest conserving energy
                print(f"{self.name}: It's a good time to conserve energy.")
        else:
            print(f"{self.name} could not retrieve the current price.")'''


class EnergyAgent:
    def __init__(self, name, password, environment):
        self.name = name
        self.password = password
        self.environment = environment  # O ambiente é um atributo da classe
        self.current_price = None  # Preço atual da energia da rede
        self.energy_consumption_needed = 0.0  # Energia que os outros agentes vão precisar (em kWh)

    def start(self):
        print(f"{self.name} agent started.")

    def stop(self):
        print(f"{self.name} agent stopped.")

    def update_price(self):
        """Atualiza o preço da energia da rede a partir do environment."""
        self.current_price = self.environment.get_energy_prices()  # Chame o método correto do environment

    def receive_energy_request(self, consumption_needed):
        """Recebe pedidos de consumo de energia de outros agentes."""
        self.energy_consumption_needed += consumption_needed

    def act_on_price(self):
        """Toma ação baseada no preço da energia e no estado da bateria solar."""
        solar_energy_available = self.environment.solar_battery.get_state_of_charge()  # Supondo que solar_battery é um atributo de environment

        if self.current_price is not None:
            print(f"{self.name} received energy price: {self.current_price}")

            # Se houver energia solar suficiente, usamos a energia solar primeiro
            if solar_energy_available > 0:
                energy_to_use = min(solar_energy_available, self.energy_consumption_needed)
                self.environment.solar_battery.discharge(energy_to_use)  # Discharge solar battery
                self.energy_consumption_needed -= energy_to_use
                print(f"{self.name}: Usou {energy_to_use} kWh de energia solar.")
            else:
                print(f"{self.name}: Não há energia solar disponível.")

            # Caso ainda haja consumo necessário, usa energia da rede
            if self.energy_consumption_needed > 0:
                print(f"{self.name}: Ainda precisa de {self.energy_consumption_needed} kWh da rede.")
                if self.current_price < 0.15:
                    print(f"{self.name}: O preço está baixo, pode consumir energia da rede.")
                elif self.current_price > 0.30:
                    print(f"{self.name}: O preço está alto, deve evitar consumo da rede.")
        else:
            print(f"{self.name} could not retrieve the current price.")