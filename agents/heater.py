from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class HeaterAgent(Agent):
    def __init__(self, jid, password,desired_temperature):
        super().__init__(jid, password)
        self.desired_temperature =  desired_temperature 
        
        self.heating_power_per_degree = 1.0  # Example: 1 kW per degree of heating
        self.base_priority = 1.0  # Base priority of the heater

    class HeaterBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.energy_price = None
            
            self.window_open = False

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
                    break
            desired_temp_range = (self.agent.desired_temperature - 1, 
                                  self.agent.desired_temperature + 1)

            # Calculate dissatisfaction level
            if current_room_temp < desired_temp_range[0]:
                dissatisfaction = (desired_temp_range[0] - current_room_temp)
        
            else:
                dissatisfaction = 0  # Within range, no dissatisfaction

            # Calculate priority based on dissatisfaction
            dynamic_priority = self.calculate_priority(dissatisfaction)
            print(f"[Heater] Dissatisfaction level: {dissatisfaction}°C. Dynamic priority: {dynamic_priority}.")

            
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "solar_auction_started":
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[Heater] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Heater] No message received within the timeout.")

            if dissatisfaction > 0:
                while True:
                    msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                    if msg and msg.get_metadata("type") == "window_status":
                        if(msg.body == "open"):
                            self.window_open = True
                            print("open heater")
                            break
                        elif(msg.body == "closed"):
                            print("closed heater")
                            self.window_open = False
                            break
                          # Saia do loop após processar a mensagem
                    elif msg:
                        print(f"[Heater] Ignored message with metadata type: {msg.get_metadata('type')}")
                    else:
                        print("[Heater] No message received within the timeout.")
                if(not self.window_open):
                    
                    # Request the necessary energy from the EnergyAgent
                    energy_needed = self.calculate_energy_consumption(dissatisfaction)
                    print(f"Energy needed: {energy_needed} kWh.")
                    # Send a message to the SystemState agent to get available solar energy
                    # Sending the priority request message
                    request_msg = Message(to="system@localhost")  # You are sending to a specific agent
                    request_msg.set_metadata("performative", "request")
                    request_msg.set_metadata("type", "priority")
                    request_msg.body = str(dissatisfaction)  # The message body contains dissatisfaction value
                    await self.send(request_msg)

                    while True:  # Keep checking until a valid response is received
                        try:
                            # Wait for the response from the SystemState agent
                            response = await self.receive(timeout=10)
                            print(f"[Heater] Received message from system. {response.get_metadata('type')}")



                            
                            if response and response.get_metadata("type") == "energy_availablility":
                                # Extract solar energy, battery status, and energy price from the message body
                                solar_energy_available, battery_status, energy_price = map(float, response.body.split(","))

                                max_grid_energy = self.calculate_max_grid_energy(price_actual=energy_price, 
                                                              dynamic_priority=dynamic_priority)
            
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
                
                                    print(f"[Heater] Using {solar_used} kWh of solar energy.")
                                    energy_needed -= solar_used  # Reduz a necessidade restante

                                # Use battery energy next
                                if energy_needed > 0 and battery_status > 0:
                                    battery_used = min(battery_status, energy_needed)
                                    energy_power += battery_used
                                    print(f"[Heater] Using {battery_used} kWh of battery energy.")
                                    energy_needed -= battery_used

                                # Use grid energy as a last resort
                                if energy_needed > 0 and max_grid_energy > 0:
                                    grid_used = min(energy_needed, max_grid_energy)  # nao ultrapassa o limite
                                    energy_power += grid_used
                                    print(f"[Heater] Using {grid_used:.2f} kWh of grid energy at cost {grid_used * energy_price:.2f}.")


                                if energy_needed <= 0:
                                    print("[Heater] Energy need satisfied.")
                                    break  # Exit the loop when energy need is met

                                if energy_needed > max_grid_energy:
                                    print(f"[Heater] Unable to fully satisfy energy need with grid. {energy_needed - max_grid_energy:.2f} kWh left unmet.")
                                    break
                        except asyncio.TimeoutError:
                            print("[Heater] Timeout while waiting for SystemState agent response. Retrying...")


                    # Update the heating based on available energy
                    
                    degrees_heated = energy_power / self.agent.heating_power_per_degree
                    msg = Message(to="environment@localhost")
                    msg.set_metadata("performative", "request")
                    msg.set_metadata("type", "room_temperature_update_heat")  # Must match the receiver's check
                    msg.body = str(degrees_heated)
                    await self.send(msg)
                    
                    msg = Message(to="system@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("type", "confirmation")
                    msg.body = f"{solar_used},{battery_used},{grid_used}" # 0 needs to be replaced with the actual cost
                    await self.send(msg)
                else:
                     print("[Heater] window open")
            else:
                print("[Heater] Comfortable temperature, no heating needed.")

            await asyncio.sleep(0.1)  # Wait before the next iteration

        def calculate_priority(self, dissatisfaction):
            """Calculates dynamic priority based on dissatisfaction and base priority."""
            return self.agent.base_priority + dissatisfaction  # Efmaxample of priority calculation

        def calculate_energy_consumption(self, dissatisfaction):
            """Calculates energy consumption (kWh) based on dissatisfaction level."""
            return dissatisfaction  # Example: 1 kWh per degree of dissatisfaction
        
        def calculate_max_grid_energy(self,price_actual, dynamic_priority, max_possible_energy=100):
            """
            Calcula a energia máxima utilizável da rede com base no preço atual da energia e na prioridade dinâmica.
            
            Args:
                price_actual (float): O preço atual da energia em €/MWh.
                dynamic_priority (float): Prioridade dinâmica para o uso de energia.
                max_possible_energy (float): Limite máximo de energia utilizável (default = 100 kWh).
                
            Returns:
                float: Quantidade máxima de energia (kWh) que pode ser utilizada da rede.
            """
            # Definir limites com base nos quartis
            low_price_threshold = 49.35  # 1º quartil
            high_price_threshold = 68.01  # 3º quartil

            if price_actual < low_price_threshold:
                # Preço baixo: permitir uso total
                max_energy = max_possible_energy
            elif price_actual <= high_price_threshold:
                # Preço médio: uso proporcional à prioridade
                max_energy = max_possible_energy * (dynamic_priority / 10)  # Exemplo de escala de prioridade
            else:
                # Preço alto: limitar uso com base na prioridade
                max_energy = max_possible_energy * (dynamic_priority / 20)  # Reduzido devido ao preço alto

            # Garantir que a energia máxima não ultrapasse o limite máximo
            return min(max_possible_energy, max(0, max_energy))
