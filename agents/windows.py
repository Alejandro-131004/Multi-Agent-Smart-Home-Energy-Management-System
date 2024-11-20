from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class WindowAgent(Agent):
    def __init__(self, jid, password, desired_temperature):
        super().__init__(jid, password)
        self.desired_temperature = desired_temperature

    class WindowBehaviour(CyclicBehaviour):
        async def run(self):
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "solar_auction_started":
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[Heater] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Heater] No message received within the timeout.")
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
            desired_temp_range = (self.agent.desired_temperature - 1,
                                  self.agent.desired_temperature + 1)
            if inside_temp < desired_temp_range[0] and outside_temp > inside_temp:
                # Abrir janelas para aquecer a casa
                print("[WindowAgent] Opening windows to heat the house.")
                window_status = "open"
            elif inside_temp > desired_temp_range[1] and outside_temp < inside_temp:
                # Abrir janelas para resfriar a casa
                print("[WindowAgent] Opening windows to cool the house.")
                window_status = "open"
            else:
                # Fechar janelas
                print("[WindowAgent] Closing windows.")
                window_status = "closed"

            # Enviar status das janelas para outros agentes
            for agent_id in ["heater@localhost", "aircon@localhost", "environment@localhost"]:
                msg = Message(to=agent_id)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "window_status")
                msg.body = window_status
                await self.send(msg)

            await asyncio.sleep(1)

    async def setup(self):
        print("[WindowAgent] Agent starting...")
        behaviour = self.WindowBehaviour()
        self.add_behaviour(behaviour)

