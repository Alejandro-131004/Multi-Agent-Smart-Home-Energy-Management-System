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
            while True:
                msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
                print("window states")
                
                if msg:
                    msg_type = msg.get_metadata("type")
                    if msg_type == "state_request":
                        # Handle state request and reply with the window status
                        response = Message(to="system@localhost")
                        response.set_metadata("performative", "inform")
                        response.set_metadata("type", "state_response")
                        response.body = window_status  # Assume window_status is defined elsewhere
                        await self.send(response)
                        break
                    else:
                        print(f"[Window] Ignored message with metadata type: {msg_type}.")
                else:
                    print("[Window] No message received within the timeout.")
                    break
            msg = await self.receive(timeout=10)  # Aguarda até 10 segundos
            if msg:
                msg_type = msg.get_metadata("type")  # Obtém o tipo da mensagem
                if msg_type == "preference_update":
                    # Processar atualização de preferências
                    self.agent.desired_temperature = float(msg.body)
                    print(f"[Windows] Preferência atualizada recebida: Temperatura desejada = {desired_temperature}.")
                    # Aqui você pode adicionar a lógica para ajustar o estado do agente, se necessário.
                elif msg_type == "no_changes":
                    # Nenhuma alteração na preferência
                    print(f"[Windows] Mensagem recebida: Nenhuma mudança nas preferências.")
                else:
                    # Tipo de mensagem não reconhecido
                    print(f"[Windows] Mensagem ignorada. Tipo desconhecido: {msg_type}.")
            else:
                print("[Windows] Nenhuma mensagem recebida dentro do tempo limite.")

                     
    async def setup(self):
        print("[WindowAgent] Agent starting...")
        behaviour = self.WindowBehaviour()
        self.add_behaviour(behaviour)

