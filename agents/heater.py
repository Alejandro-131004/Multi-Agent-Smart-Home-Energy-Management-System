from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class HeaterAgent(Agent):
    def __init__(self, jid, password, environment, energy_agent):
        super().__init__(jid, password)
        self.environment = environment  # Refers to the Environment
        self.energy_agent = energy_agent  # EnergyAgent to consult about energy
        self.heating_power_per_degree = 1.0  # Example: 1 kW per degree of heating
        self.base_priority = 1.0  # Base priority of the heater

    class HeaterBehaviour(CyclicBehaviour):
        def __init__(self, environment, energy_agent):
            super().__init__()
            self.environment = environment
            self.energy_agent = energy_agent

        async def run(self):
            # Get the current indoor temperature
            current_room_temp = self.environment.get_indoor_temperature()
            desired_temp_range = (self.environment.desired_temperature - 1, 
                                  self.environment.desired_temperature + 1)

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

            if dissatisfaction > 0:
                # Request the necessary energy from the EnergyAgent
                energy_needed = self.calculate_energy_consumption(dissatisfaction)
                print(f"Energy needed: {energy_needed} kWh.")

                # Send a message to the SystemState agent to get available solar energy
                request_msg = Message(to="system_state@localhost")  # Assuming you know the JID
                request_msg.set_metadata("performative", "request")
                request_msg.set_metadata("type", "solar_energy_request")
                await self.send(request_msg)

                # Wait for the response from the SystemState agent
                response = await self.receive(timeout=10)
                if response and response.get_metadata("type") == "solar_energy_response":
                    solar_energy_available = float(response.body)
                    print(f"[Heater] Solar energy available: {solar_energy_available} kWh.")
                    
                    if solar_energy_available > 0:
                        energy_power = min(solar_energy_available, energy_needed)
                        print(f"[Heater] Using {energy_power} kWh of solar energy.")
                    else:
                        print("[Heater] No solar energy available.")
                        energy_power = 0
                else:
                    print("[Heater] No response from SystemState agent or invalid message.")
                    energy_power = 0

                # Update the heating based on available energy
                if energy_power > 0:
                    degrees_heated = energy_power / self.agent.heating_power_per_degree
                    self.environment.update_room_temperature(degrees_heated)
                    print(f"[Heater] Room temperature increased by {degrees_heated}°C.")
                else:
                    print("[Heater] No energy available for heating.")
            else:
                print("[Heater] Comfortable temperature, no heating needed.")

            await asyncio.sleep(10)  # Wait before the next iteration

        def calculate_priority(self, dissatisfaction):
            """Calculates dynamic priority based on dissatisfaction and base priority."""
            return self.agent.base_priority + dissatisfaction  # Example of priority calculation

        def calculate_energy_consumption(self, dissatisfaction):
            """Calculates energy consumption (kWh) based on dissatisfaction level."""
            return dissatisfaction  # Example: 1 kWh per degree of dissatisfaction

    async def setup(self):
        print(f"[Heater] Heater agent initialized.")
        self.add_behaviour(self.HeaterBehaviour(self.environment, self.energy_agent))
