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
            energy_price = None

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
            elif current_room_temp > desired_temp_range[1]:
                dissatisfaction = (current_room_temp - desired_temp_range[1])
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
                        print("[Heater] Received message from system.")

                        if response and response.get_metadata("type") == "energy_availablility":
                            # Extract solar energy, battery status, and energy price from the message body
                            solar_energy_available, battery_status, energy_price = map(float, response.body.split(","))
                            print(f"[Heater] Solar energy available: {solar_energy_available} kWh.")

                            if solar_energy_available > 0:
                                energy_power = min(solar_energy_available, energy_needed)
                                print(f"[Heater] Using {energy_power} kWh of solar energy.")
                                break  # Exit the loop once a valid match is found
                            else:
                                print("[Heater] No solar energy available.")
                                energy_power = 0
                                break
                    except asyncio.TimeoutError:
                        print("[Heater] Timeout while waiting for SystemState agent response. Retrying...")


                # Update the heating based on available energy
                if energy_power > 0:
                    degrees_heated = energy_power / self.agent.heating_power_per_degree
                    msg = Message(to=env_agent_id)
                    msg.set_metadata("performative", "request")
                    msg.set_metadata("type", "room_temperature_update")  # Must match the receiver's check
                    msg.body = str(degrees_heated)
                    await self.send(msg)
                    msg = Message(to="system@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("type", "confirmation")
                    msg.body = f"{energy_power},{0},{0}" # 0 needs to be replaced with the actual cost
                    await self.send(msg)
                    print(f"[Heater] Room temperature increased by {degrees_heated}°C.")
                else:
                    print("[Heater] No energy available for heating.")
            else:
                print("[Heater] Comfortable temperature, no heating needed.")

            await asyncio.sleep(0.1)  # Wait before the next iteration

        def calculate_priority(self, dissatisfaction):
            """Calculates dynamic priority based on dissatisfaction and base priority."""
            return self.agent.base_priority + dissatisfaction  # Example of priority calculation

        def calculate_energy_consumption(self, dissatisfaction):
            """Calculates energy consumption (kWh) based on dissatisfaction level."""
            return dissatisfaction  # Example: 1 kWh per degree of dissatisfaction
