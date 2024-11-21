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
        self.run = 0
    class AirconBehaviour(CyclicBehaviour):
        async def run(self):
            if(self.agent.run == 2):
                while True:
                    msg = await self.receive(timeout=10)  # Aguarda até 10 segundos
                    if msg:
                        msg_type = msg.get_metadata("type")  # Obtém o tipo da mensagem
                        if msg_type == "preference_update":
                            # Processar atualização de preferências
                            self.agent.desired_temperature = msg.body
                            print(f"[{self.agent.__class__.__name__}] Preferência atualizada recebida: Temperatura desejada = {self.agent.desired_temperature}.")
                            # Aqui você pode adicionar a lógica para ajustar o estado do agente, se necessário.
                            break  # Sai do loop após processar a atualização
                        elif msg_type == "no_changes":
                            # Nenhuma alteração na preferência
                            print(f"[{self.agent.__class__.__name__}] Mensagem recebida: Nenhuma mudança nas preferências.")
                            break  # Sai do loop após processar a mensagem
                        else:
                            # Tipo de mensagem não reconhecido
                            print(f"[{self.agent.__class__.__name__}] Mensagem ignorada. Tipo desconhecido: {msg_type}.")
                            # Sai do loop após processar a mensagem desconhecida
                    else:
                        print(f"[{self.agent.__class__.__name__}] Nenhuma mensagem recebida dentro do tempo limite.")
                        break  # Sai do loop caso o tempo limite seja atingido
            energy_power = 0
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
            print(f"[Aircon] Dissatisfaction: {dissatisfaction}°C. Priority: {dynamic_priority}.")

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
                            break
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
                         
                        # Recebe a mensagem com informações sobre energia disponível
                        energy_response = await self.receive(timeout=10)
                        print("[Aircon] Received message from system. {response.get_metadata('type')}")

                        if energy_response and energy_response.get_metadata("type") == "energy_availability":
                            solar_energy_available, battery_status, energy_price = map(float, energy_response.body.split(","))
                            print(f"[Aircon] Solar energy available: {solar_energy_available} kWh.")

                            max_grid_energy = self.calculate_max_grid_energy(price_actual=energy_price, dynamic_priority=dynamic_priority)
                            
                            print ({max_grid_energy},"max grid energy")
                            print(f"[Heater] Solar energy available: {solar_energy_available} kWh.")
                            solar_used = 0
                            battery_used = 0
                            grid_used = 0
                            energy_power = 0
                            # Use solar energy first
                            if solar_energy_available > 0:
                                solar_used = min(solar_energy_available, energy_needed)
                                energy_power = solar_used
            
                                print(f"[Aircon] Using {solar_used} kWh of solar energy.")
                                energy_needed -= solar_used  # Reduz a necessidade restante

                            # Use battery energy next
                            if energy_needed > 0 and battery_status > 0:
                                battery_used = min(battery_status, energy_needed)
                                energy_power += battery_used
                                print(f"[Aircon] Using {battery_used} kWh of battery energy.")
                                energy_needed -= battery_used

                            # Use grid energy as a last resort
                            if energy_needed > 0 and max_grid_energy > 0:
                                grid_used = min(energy_needed, max_grid_energy)  # nao ultrapassa o limite
                                energy_power += grid_used
                                print(f"[Aircon] Using {grid_used:.2f} kWh of grid energy at cost {grid_used * energy_price:.2f}.")


                            if energy_needed <= 0:
                                print("[Aircon] Energy need satisfied.")
                                break  # Exit the loop when energy need is met

                            if energy_needed > max_grid_energy:
                                print(f"[Aircon] Unable to fully satisfy energy need with grid. {energy_needed - max_grid_energy:.2f} kWh left unmet.")
                                break
                        break

                    # Update the heating based on available energy
                    if energy_power > 0:
                        degrees_cooled = energy_power / self.agent.cooling_power_per_degree
                        msg = Message(to=env_agent_id)
                        msg.set_metadata("performative", "request")
                        msg.set_metadata("type", "room_temperature_update_cold")  
                        msg.body = str(degrees_cooled)
                        await self.send(msg)
                        print(f"[Aircon] Sent room temperature update: {degrees_cooled}°C.")

                        system_msg = Message(to="system@localhost")
                        system_msg.set_metadata("performative", "inform")
                        system_msg.set_metadata("type", "confirmation")
                        system_msg.body = f"{solar_used},{battery_used},{grid_used}" 
                        await self.send(system_msg)
                        print(f"[Aircon] Room temperature decreased by {degrees_cooled}°C")
                    else:
                        print("[Aircon] No energy available for cooling.")
                else:
                     print("[Aircon] window open")
            else:
                print("[Aircon] Comfortable temperature, no cooling needed.")
            while True:
                msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
                if msg:
                    msg_type = msg.get_metadata("type")
                    if msg_type == "state_request":
                        # Handle state request and reply with the status
                        response = Message(to="system@localhost")
                        response.set_metadata("performative", "inform")
                        response.set_metadata("type", "state_response")
                        if energy_power > 0:
                            response.body = "on"
                        else:
                            response.body = "off"
                        await self.send(response)
                        print(f"[{self.agent.__class__.__name__}] Sent state response: {response.body} to {msg.sender}.")
                        break
                    else:
                        print(f"[{self.agent.__class__.__name__}] Ignored message with metadata type: {msg_type}.")
                else:
                    print(f"[{self.agent.__class__.__name__}] No message received within the timeout.")
                    break
                break
            self.agent.run = 2
            await asyncio.sleep(0.1)  # Wait before the next iteration

        def calculate_priority(self, dissatisfaction):
            """Calculate dynamic priority based on dissatisfaction."""
            return self.agent.base_priority + dissatisfaction

        def calculate_energy_consumption(self, dissatisfaction):
            """Calculate energy needed based on dissatisfaction."""
            return dissatisfaction * self.agent.cooling_power_per_degree

    