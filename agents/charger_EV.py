from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
import random
from datetime import datetime

class CarChargerAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    class CarChargerBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.consumption = 0.0  # Total energy consumption initialized to 0
            self.priority = 0

        async def run(self):
            energy_price = None
            solar_energy_available = 0  # Inicialize com um valor padrão
            car_battery = 0.0  # Estado inicial da bateria do carro

            # Solicite o preço da energia atual ao SystemState
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "energy_price":
                    try:
                        energy_price = float(msg.body)
                        print(f"[CarCharger] Current electricity price: {energy_price} €/kWh")
                    except ValueError:
                        print("[CarCharger] Received invalid energy price.")
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[CarCharger] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[CarCharger] No message received within the timeout.")
                    break

            # Configurar prioridade
            self.priority = 1
            request_msg = Message(to="system@localhost")  # Enviar para um agente específico
            request_msg.set_metadata("performative", "request")
            request_msg.set_metadata("type", "priority")
            request_msg.body = str(self.priority)  # Corpo da mensagem contém o valor de prioridade
            await self.send(request_msg)

            # Aguarde a resposta do agente SystemState
            response = await self.receive(timeout=10)
            if response and response.get_metadata("type") == "solar_energy_available":
                try:
                    solar_energy_available = float(response.body)
                    print(f"[CarCharger] Received solar energy available: {solar_energy_available} kWh")
                except ValueError:
                    print("[CarCharger] Received invalid solar energy value.")
            else:
                print("[CarCharger] No response from SystemState or invalid message.")

            # Verificar se o carro está em casa (probabilidade dependente da hora do dia)
            current_hour = datetime.now().hour
            home_probability = self.get_home_probability(current_hour)

            # Gerar número aleatório para decidir se o carro está em casa
            random_number = random.randint(0, 99)
            is_home = random_number < home_probability
            print(f"[CarCharger] Car is {'home' if is_home else 'not home'} (Probability: {home_probability}%)")

            if is_home:
                # Consumo do carregador do carro (exemplo)
                consumption_amount = 3.0  # Exemplo de consumo do carregador em kWh

                if energy_price is not None:
                    # Calcular o consumo de energia
                    solar_energy_consumed, cost = self.calculate_comsumption(
                        consumption_amount, solar_energy_available, energy_price
                    )
                    print(f"[CarCharger] Charging car... Solar: {solar_energy_consumed} kWh, Cost: {cost} €")
                    # Enviar mensagem de confirmação ao SystemState
                    msg = Message(to="system@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("type", "confirmation")
                    msg.body = f"{solar_energy_consumed},{cost}" 
                    await self.send(msg)
                else:
                    print("[CarCharger] Energy price unavailable. Cannot calculate cost.")

            # Simular tempo de espera antes do próximo ciclo
            await asyncio.sleep(0.1)  # Ajuste a duração conforme necessário

        def get_home_probability(self, hour):
            # Definir a probabilidade de o carro estar em casa em função da hora do dia
            if 6 <= hour < 9:
                return 30  # 30% chance de estar em casa pela manhã
            elif 9 <= hour < 18:
                return 10  # 10% chance de estar em casa durante o dia
            elif 18 <= hour < 22:
                return 80  # 80% chance de estar em casa à noite
            else:
                return 50  # 50% chance de estar em casa de madrugada

        def calculate_comsumption(self, consumption_amount, solar_energy_available, energy_price):
            # Se a energia solar puder cobrir totalmente o consumo
            if solar_energy_available >= consumption_amount:
                solar_used = consumption_amount
                cost = 0  # Sem custo adicional, já que a solar cobre tudo
            else:
                # Usar toda a energia solar disponível
                solar_used = solar_energy_available
                # Calcular o custo para a energia restante
                remaining_energy = consumption_amount - solar_energy_available
                cost = remaining_energy * energy_price

            return solar_used, cost
