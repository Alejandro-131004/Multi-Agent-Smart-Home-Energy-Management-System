from itertools import cycle

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
import random

class WashingMachineAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    class WashingMachineBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.clothes_count = 0  # Número atual de peças na caixa
            self.box_capacity = 10  # Capacidade máxima antes de lavar
            self.energy_per_cycle = 1.0  # Consumo de energia por ciclo (kWh)
            self.cycle_washtime = 2
            self.priority = 15  # Prioridade da máquina de lavar
            self.cycle_hour = 0

        async def run(self):
            energy_price = None
            solar_energy_available = 0  # Valor inicial de energia solar disponível
            battery_status = 0  # Valor inicial de status da bateria
            # Solicite o preço da energia atual ao SystemState
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "solar_auction_started":
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[Washing Machine] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Washing Machine] No message received within the timeout.")

            # Adicionar roupas por hora
            self.add_clothes()

            # Se a caixa está cheia, preparar para lavar
            if (self.clothes_count >= self.box_capacity*0.8) or (self.cycle_hour == 1):
                if self.cycle_hour == 0:
                    print(f"[Washing Machine] Box full with {self.clothes_count} clothes. Ready to wash.")
                self.cycle_hour+=1
                # Configurar prioridade e enviar ao `SystemState`
                request_msg = Message(to="system@localhost")
                request_msg.set_metadata("performative", "request")
                request_msg.set_metadata("type", "priority")
                request_msg.body = str(self.priority)
                await self.send(request_msg)

                # Aguardar resposta com condições de energia
                while True:
                    response = await self.receive(timeout=30)
                    if response and response.get_metadata("type") == "energy_availablility":
                        try:
                            solar_energy_available, battery_status, energy_price = map(float, response.body.split(","))
                            print(f"[Washing Machine] Energy conditions received: Solar={solar_energy_available} kWh, Battery={battery_status} kWh, Price={energy_price} €/kWh")
                            break
                        except ValueError:
                            print("[Washing Machine] Received invalid energy data.")
                    else:
                        print("[Washing Machine] No response from SystemState.")
                        return

                if energy_price is not None:
                    # Calcular o consumo de energia
                    solar_used, battery_used, cost = self.calculate_consumption(
                        self.energy_per_cycle, solar_energy_available, battery_status, energy_price
                    )
                    print(
                        f"[Washing Machine] Washing started. Solar: {solar_used} kWh, Battery: {battery_used} kWh, Cost: {cost} €")

                    if self.cycle_hour == 1:
                        # Resetar o número de roupas após lavar
                        self.clothes_count = 0

                    # Enviar mensagem de confirmação ao SystemState
                    confirmation_msg = Message(to="system@localhost")
                    confirmation_msg.set_metadata("performative", "inform")
                    confirmation_msg.set_metadata("type", "confirmation")
                    confirmation_msg.body = f"{solar_used},{battery_used},{cost}"
                    await self.send(confirmation_msg)
                else:
                    print("[Washing Machine] Energy price unavailable. Cannot start washing.")

            elif self.cycle_hour == 2:
                self.cycle_hour = 0
                print(f"[Washing Machine] Waiting for more clothes. Current count: {self.clothes_count}/{self.box_capacity}")
            else:
                print(f"[Washing Machine] Waiting for more clothes. Current count: {self.clothes_count}/{self.box_capacity}")

            # Simular espera de uma hora antes do próximo ciclo
            await asyncio.sleep(1)

        def add_clothes(self):
            """Adiciona roupas de forma aleatória à máquina de lavar."""
            new_clothes = random.randint(1, 5)  # Adiciona de 1 a 5 peças de roupa
            self.clothes_count += new_clothes
            print(f"[Washing Machine] Added {new_clothes} clothes. Total: {self.clothes_count}/{self.box_capacity}")

        def calculate_consumption(self, consumption_amount, solar_energy_available, battery_status, energy_price):
            """Calcula a energia consumida durante o ciclo."""
            solar_used = 0
            battery_used = 0
            cost = 0

            # Priorizar energia solar
            if solar_energy_available >= consumption_amount:
                solar_used = consumption_amount
                cost = 0
            else:
                solar_used = solar_energy_available
                remaining_energy = consumption_amount - solar_used

                # Utilizar energia da bateria
                if battery_status >= remaining_energy:
                    battery_used = remaining_energy
                    cost = 0
                else:
                    battery_used = battery_status
                    remaining_energy -= battery_used

                    # Usar energia da rede elétrica
                    cost = remaining_energy * energy_price

            return solar_used, battery_used, cost

