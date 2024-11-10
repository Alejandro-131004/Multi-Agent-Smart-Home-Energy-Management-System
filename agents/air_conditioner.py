from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
from spade.message import Message

class AirconAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment  # Refers to the Environment
        self.heating_power_per_degree = 1.0  # Example: 1 kW per degree of heating
        self.cooling_power_per_degree = 2.0
        self.base_priority = 1.0  # Base priority of the Aircon

    class AirconBehaviour(CyclicBehaviour):
        def __init__(self, environment, heating_power_per_degree, cooling_power_per_degree, base_priority):
            super().__init__()
            self.environment = environment
            self.heating_power_per_degree = heating_power_per_degree
            self.cooling_power_per_degree = cooling_power_per_degree
            self.base_priority = base_priority

        async def run(self):
            # Get the current indoor temperature
            current_room_temp = self.environment.get_indoor_temperature()
            desired_temp_range = (self.environment.desired_temperature - 1, 
                                  self.environment.desired_temperature + 1)

            # Calculate dissatisfaction level
            if current_room_temp < desired_temp_range[0]:
                dissatisfaction = (desired_temp_range[0] - current_room_temp)
            elif current_room_temp > desired_temp_range[1]:
                dissatisfaction = (desired_temp_range[1] - current_room_temp)
            else:
                dissatisfaction = 0  # Within range, no dissatisfaction

            # Calculate priority based on dissatisfaction
            dynamic_priority = self.calculate_priority(dissatisfaction)

            print(f"[Aircon] Dissatisfaction level: {dissatisfaction}°C. Dynamic priority: {dynamic_priority}.")

            if dissatisfaction != 0:
                # Request necessary energy price from the SystemState agent
                energy_price = await self.request_energy_price()

                if energy_price is not None:
                    # Calculate the energy needed based on dissatisfaction
                    energy_needed = self.calculate_energy_consumption(dissatisfaction)
                    print("Energy needed:", energy_needed)

                    # Request solar energy with the given priority
                    await self.request_solar_energy(energy_needed, dynamic_priority)
                else:
                    print("[Aircon] Could not retrieve energy price; skipping solar energy request.")
            else:
                print(f"[Aircon] Comfortable temperature.")

            await asyncio.sleep(10)  # Wait before the next iteration

        async def request_energy_price(self):
            # Create a message to request the energy price
            request_msg = Message(to="system_state_agent_jid")  # Replace with actual SystemState agent JID
            request_msg.set_metadata("performative", "request")
            request_msg.set_metadata("type", "energy_price_request")

            await self.send(request_msg)
            print("[Aircon] Requested energy price.")

            # Wait for the response
            response = await self.receive(timeout=10)
            if response and response.get_metadata("type") == "energy_price":
                price = float(response.body)
                print(f"[Aircon] Received energy price: {price} LWatts.")
                return price
            else:
                print("[Aircon] No valid response received for energy price request.")
                return None

        async def request_solar_energy(self, energy_needed, priority):
            # Create a message to request solar energy
            request_msg = Message(to="system_state_agent_jid")  # Replace with actual SystemState agent JID
            request_msg.set_metadata("performative", "request")
            request_msg.set_metadata("type", "solar_production_request")
            request_msg.body = str(energy_needed)

            # Add priority to the message
            request_msg.set_metadata("priority", str(priority))

            await self.send(request_msg)
            print(f"[Aircon] Requested {energy_needed} LWatts of solar energy with priority {priority}.")

            # Wait for confirmation
            response = await self.receive(timeout=10)
            if response and response.get_metadata("type") == "confirmation":
                print(f"[Aircon] Confirmation received for solar energy request from {response.sender}.")
            else:
                print("[Aircon] No valid confirmation received.")

        def calculate_priority(self, dissatisfaction):
            """Calculates dynamic priority based on dissatisfaction and base priority."""
            if dissatisfaction < 0:
                return self.base_priority - dissatisfaction
            else:
                return self.base_priority + dissatisfaction  # Example of priority calculation

        def calculate_energy_consumption(self, dissatisfaction):
            """Calculates energy consumption (Watts) per hour to compensate for dissatisfaction level."""
            if dissatisfaction < 0:
                kwh = self.cooling_power_per_degree * -dissatisfaction
            else:
                kwh = self.heating_power_per_degree * dissatisfaction
                
            print("Calculated energy consumption:", kwh)
            return kwh  # Example: 1000 LWatts per degree of dissatisfaction

    async def setup(self):
        print(f"[Aircon] Aircon agent initialized.")
        self.add_behaviour(self.AirconBehaviour(self.environment, 
                                                 self.heating_power_per_degree, 
                                                 self.cooling_power_per_degree, 
                                                 self.base_priority))
