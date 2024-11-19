from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
from spade.message import Message


class AirconAgent(Agent):
    def __init__(self, jid, password, desired_temperature):
        super().__init__(jid, password)
        self.desired_temperature = desired_temperature
        self.cooling_power_per_degree = 2.0  # Potência de resfriamento em kW por grau
        self.base_priority = 1.0  # Prioridade base do ar-condicionado

    class AirconBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.window_status = "closed"  # Estado inicial das janelas

        async def run(self):
            # Solicitar temperatura interna
            env_agent_id = "environment@localhost"
            msg = Message(to=env_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "inside_temperature")
            await self.send(msg)

            while True:
                msg = await self.receive(timeout=10)
                if msg and msg.get_metadata("type") == "inside_temperature":
                    current_room_temp = float(msg.body)
                    break

            # Calcular o nível de insatisfação
            desired_temp_range = (self.agent.desired_temperature - 1,
                                  self.agent.desired_temperature + 1)
            if current_room_temp > desired_temp_range[1]:
                dissatisfaction = (current_room_temp - desired_temp_range[1])
            else:
                dissatisfaction = 0

            # Atualizar a prioridade dinâmica
            dynamic_priority = self.calculate_priority(dissatisfaction)
            print(f"[Aircon] Dissatisfaction level: {dissatisfaction}°C. Dynamic priority: {dynamic_priority}.")

            # Receber status das janelas
            while True:
                msg = await self.receive(timeout=10)
                if msg and msg.get_metadata("type") == "window_status":
                    self.window_status = msg.body
                    print(f"[Aircon] Received window status: {self.window_status}")
                    break
                elif msg and msg.get_metadata("type") == "solar_auction_started":
                    break
                elif msg:
                    print(f"[Aircon] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Aircon] No message received within the timeout.")

            # Decidir se o resfriamento deve ser ativado
            if dissatisfaction > 0 and self.window_status == "closed":
                # Solicitar energia e realizar resfriamento
                energy_needed = self.calculate_energy_consumption(dissatisfaction)
                print(f"[Aircon] Energy needed: {energy_needed} kWh.")
            elif self.window_status == "open":
                print("[Aircon] Windows are open. Cooling disabled to save energy.")
            else:
                print("[Aircon] Comfortable temperature, no cooling needed.")

            await asyncio.sleep(0.1)

        def calculate_priority(self, dissatisfaction):
            """Calcula prioridade dinâmica com base na insatisfação."""
            return self.agent.base_priority + dissatisfaction

        def calculate_energy_consumption(self, dissatisfaction):
            """Calcula consumo de energia com base no nível de insatisfação."""
            return dissatisfaction * self.agent.cooling_power_per_degree

    async def setup(self):
        print("[Aircon] Agent starting...")
        behaviour = self.AirconBehaviour()
        self.add_behaviour(behaviour)
