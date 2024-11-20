from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class FridgeAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    class FridgeBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.consumption = 0.0  # Total energy consumption initialized to 0
            self.priority = 0
            self.status = "on"

        async def run(self):
            energy_price = None
            solar_energy_available = 0  # Inicialize com um valor padrão

            # Solicite o preço da energia atual ao SystemState
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "solar_auction_started":
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[Fridge] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Fridge] No message received within the timeout.")

            # Configurar prioridade
            self.priority = 10
            request_msg = Message(to="system@localhost")  # Enviar para um agente específico
            request_msg.set_metadata("performative", "request")
            request_msg.set_metadata("type", "priority")
            request_msg.body = str(self.priority)  # Corpo da mensagem contém o valor de prioridade
            await self.send(request_msg)

            # Aguarde a resposta do agente SystemState
            while True:
                response = await self.receive(timeout=30)
                if response and response.get_metadata("type") == "energy_availablility":
                    try:
                        solar_energy_available, battery_status, energy_price = map(float, response.body.split(","))
                        print(f"[Fridge] Received solar energy available: {solar_energy_available} kWh")
                        break
                    except ValueError:
                        print("[Fridge] Received invalid solar energy value.")
                else:
                    print("[Fridge] No response from SystemState or invalid message.")

            # Consumo fixo do refrigerador
            consumption_amount = 0.5  # Consumo fixo para este ciclo

            
            # Calcular o consumo de energia
            solar_energy_consumed,battery_energy_comsumed, cost = self.calculate_consumption(
                consumption_amount, solar_energy_available,battery_status, energy_price
            )
            print(f"[Fridge] Consuming energy... Solar: {solar_energy_consumed} kWh,battery:{battery_energy_comsumed}, Cost: {cost} €")
            # Enviar mensagem de confirmação ao SystemState
            msg = Message(to="system@localhost")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "confirmation")
            msg.body = f"{solar_energy_consumed},{battery_energy_comsumed},{cost}" 
            await self.send(msg)
            msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
            if msg:
                msg_type = msg.get_metadata("type")
                if msg_type == "state_request":
                    # Handle state request and reply with the fridge status
                    response = Message(to="system@localhost")
                    response.set_metadata("performative", "inform")
                    response.set_metadata("type", "state_response")
                    response.body = self.status
                    await self.send(response)
                    print(f"[Fridge] Sent state response: {self.status} to {msg.sender}.")
                else:
                    print(f"[Fridge] Ignored message with metadata type: {msg_type}.")
            else:
                print("[Fridge] No message received within the timeout.")

            # Simular tempo de espera antes do próximo ciclo
            await asyncio.sleep(0.1)  # Ajuste a duração conforme necessário

        def calculate_consumption(self, consumption_amount, solar_energy_available, battery_status, energy_price):
            # Initialize variables
            solar_used = 0
            battery_used = 0
            cost = 0

            # First, use solar energy
            if solar_energy_available >= consumption_amount:
                solar_used = consumption_amount
                cost = 0  # No additional cost, solar covers everything
            else:
                # Use all available solar energy
                solar_used = solar_energy_available
                remaining_energy = consumption_amount - solar_used

                # Next, use battery energy
                if battery_status >= remaining_energy:
                    battery_used = remaining_energy
                    cost = 0  # No cost as battery covers the rest
                else:
                    # Use all available battery energy
                    battery_used = battery_status
                    remaining_energy -= battery_used

                    # Finally, calculate cost for the remaining energy from the grid
                    cost = remaining_energy * energy_price

            return solar_used, battery_used, cost

