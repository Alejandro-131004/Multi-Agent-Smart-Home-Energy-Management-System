from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class WindowAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    class WindowBehaviour(CyclicBehaviour):
        async def run(self):
            # Solicitar temperatura externa e interna ao ambiente
            env_agent_id = "environment@localhost"
            msg = Message(to=env_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "temperature_data")
            await self.send(msg)

            # Receber temperaturas externa e interna
            while True:
                response = await self.receive(timeout=10)
                if response and response.get_metadata("type") == "temperature_data":
                    inside_temp, outside_temp = map(float, response.body.split(","))
                    break
                else:
                    print("[WindowAgent] Waiting for temperature data...")

            print(f"[WindowAgent] Inside: {inside_temp}°C, Outside: {outside_temp}°C")

            # Decidir se abre ou fecha as janelas
            desired_temp = 22  # Temperatura ideal (pode ser configurável)
            if inside_temp < desired_temp and outside_temp > inside_temp:
                # Abrir janelas para aquecer a casa
                print("[WindowAgent] Opening windows to heat the house.")
                window_status = "open"
            else:
                # Fechar janelas
                print("[WindowAgent] Closing windows.")
                window_status = "closed"

            # Enviar status das janelas ao HeaterAgent
            heater_agent_id = "heater@localhost"
            msg = Message(to=heater_agent_id)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "window_status")
            msg.body = window_status
            await self.send(msg)

            await asyncio.sleep(1)

    async def setup(self):
        print("[WindowAgent] Agent starting...")
        behaviour = self.WindowBehaviour()
        self.add_behaviour(behaviour)
