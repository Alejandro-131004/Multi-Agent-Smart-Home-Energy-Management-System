from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
from spade.message import Message

class AirconAgent(Agent):
    def __init__(self, jid, password,desired_temperature):
        super().__init__(jid, password)
        self.cooling_power_per_degree = 2.0  # Cooling power in kW per degree
        self.base_priority = 1.0  # Base priority of the Aircon
        self.desired_temperature=desired_temperature
        self.response_sent = False

    class AirconBehaviour(CyclicBehaviour):
        async def run(self):
            env_agent_id = "environment@localhost"
            msg = Message(to=env_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "inside_temperature")  # Must match the receiver's check
            await self.send(msg)
            
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "inside_temperature":
                    current_room_temp = float(msg.body)
                    if current_room_temp is None:
                        print("[Aircon] Failed to get current room temperature.")
                        return
                    break
            desired_temp_range = (self.agent.desired_temperature - 1, 
                                  self.agent.desired_temperature + 1)

            # Calculate dissatisfaction level for cooling
            if current_room_temp > desired_temp_range[1]:
                dissatisfaction = current_room_temp - desired_temp_range[1]
            else:
                dissatisfaction = 0

            dynamic_priority = self.calculate_priority(dissatisfaction)
            print(f"[Aircon] f: {dissatisfaction}°C. Priority: {dynamic_priority}.")

            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "solar_auction_started":
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[Aircon] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Aircon] No message received within the timeout.")


            if dissatisfaction > 0:
                while True:
                    msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                    if msg and msg.get_metadata("type") == "window_status":
                        if(msg.body == "open"):
                            self.window_open = True
                        elif(msg.body == "closed"):
                            self.window_open = False
                            break  # Saia do loop após processar a mensagem
                        elif msg:
                            print(f"[Aircon] Ignored message with metadata type: {msg.get_metadata('type')}")
                    else:
                        print("[Aircon] No message received within the timeout.")
                if(not self.window_open):
                    # Calculate required energy
                    energy_needed = self.calculate_energy_consumption(dissatisfaction)
                    print(f"Energy needed for Aircon: {energy_needed} kWh.")

                    # Request solar energy from SystemState
                    energy_request_msg = Message(to="system@localhost")
                    energy_request_msg.set_metadata("performative", "request")
                    energy_request_msg.set_metadata("type", "priority")
                    energy_request_msg.body = str(dissatisfaction)
                    await self.send(energy_request_msg)

                    while True:
                        try: 
                            # Recebe a mensagem com informações sobre energia disponível
                            energy_response = await self.receive(timeout=10)
                            print("[Aircon] Received message from system")

                            if energy_response and energy_response.get_metadata("type") == "energy_availability":
                                solar_energy, battery_status, energy_price = map(float, energy_response.body.split(","))
                                print(f"[Aircon] Solar energy available: {solar_energy} kWh.")

                                # Caso haja energia solar disponível
                                if solar_energy > 0:
                                    energy_power = min(solar_energy, energy_needed)
                                    print(f"[Aircon] Using {energy_power} kWh of solar energy.")

                                    degrees_cooled = energy_power / self.agent.cooling_power_per_degree
                                    
                                    break
                            
                                
                                else:
                                    # Caso não haja energia solar
                                    print("[Aircon] No solar energy available.")
                                    energy_power=0
                                    break

                            else:
                                print ("nao entrei no if...")
                        except asyncio.TimeoutError:
                                print("[Aircon] Timeout while waiting for SystemState agent response. Retrying...")

                    # Update the heating based on available energy
                    if energy_power > 0:
                        degrees_cooled = energy_power / self.agent.cooling_power_per_degree
                        msg = Message(to=env_agent_id)
                        msg.set_metadata("performative", "request")
                        msg.set_metadata("type", "room_temperature_update")  # Deve coincidir com a verificação do receiver
                        msg.body = str(degrees_cooled)
                        await self.send(msg)
                        
                        print(f"[Aircon] Sent room temperature update: {degrees_cooled}°C.")
                        

                        # Aguarda confirmação do EnvAgent
                        confirmation = await self.receive(timeout=10)  # Espera por até 10 segundos
                        if confirmation and confirmation.get_metadata("type") == "temperature_update_confirmed":
                            print("[Aircon] Received confirmation from EnvAgent.")
                        else:
                            print("[Aircon] No confirmation received from EnvAgent. Retrying or ignoring...")

                        # Envia mensagem de "inform" para o sistema com informações do custo
                        cost = 0  # Substitua por lógica para calcular o custo real
                        system_msg = Message(to="system@localhost")
                        system_msg.set_metadata("performative", "inform")
                        system_msg.set_metadata("type", "confirmation")
                        system_msg.body = f"{energy_power},{0},{cost}"  # Inclui custo calculado
                        await self.send(system_msg)
                        print(f"[Aircon] Room temperature decreased by {degrees_cooled}°C and system informed.")
                    else:
                        print("[Aircon] No energy available for heating.")
                else:
                     print("[Aircon] window open")
            else:
                print("[Aircon] Comfortable temperature, no cooling needed.")

            await asyncio.sleep(0.1)  # Wait before the next iteration

        def calculate_priority(self, dissatisfaction):
            """Calculate dynamic priority based on dissatisfaction."""
            return self.agent.base_priority + dissatisfaction

        def calculate_energy_consumption(self, dissatisfaction):
            """Calculate energy needed based on dissatisfaction."""
            return dissatisfaction * self.agent.cooling_power_per_degree

    