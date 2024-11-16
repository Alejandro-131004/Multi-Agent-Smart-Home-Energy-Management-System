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
            self.solar_energy = 0
            self.energy_needed = 0
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
                msg = await self.receive(timeout=1)  # Wait for a message for up to 10 seconds
                if msg:
                    if msg.get_metadata("type") == "energy_price":
                        energy_price = float(msg.body)
                        print("[heateragent] recived energy price")
                # Request solar energy with the given priority
                self.solar_energy = await self.request_solar_energy(dynamic_priority)
                
                # Calculate the energy needed based on dissatisfaction
                self.energy_needed = self.calculate_energy_consumption(dissatisfaction)
                print("Energy needed:", self.energy_needed)
                solar_used,cost = self.change_temperature()
                msg = Message(to="system@localhost")
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "confirmation")
                msg.body = f"{solar_used},{cost}"
                await self.send(msg)
                
            else:
                print(f"[Aircon] Comfortable temperature.")

            await asyncio.sleep(10)  # Wait before the next iteration
        async def change_temperature():
            return 0,0
        async def request_solar_energy(self, priority):
            request_msg = Message(to="system@localhost")  # You are sending to a specific agent
            request_msg.set_metadata("performative", "request")
            request_msg.set_metadata("type", "priority")
            request_msg.body = str(priority)  # The message body contains dissatisfaction value
            await self.send(request_msg)
            print(f"[Aircon] Requested solar energy with priority {priority}.")

            response = await self.receive(timeout=10)  # Wait for a response (with a 10-second timeout)
            if response and response.get_metadata("type") == "solar_energy_available":
                print("[Aircon] Received solar energy message from system.")
                print(f"[Aircon] Solar energy available: {response.body} kWh.")
                return float(response.body)  # Return the solar energy value from the message
            else:
                print("[Aircon] No valid solar energy message received within timeout.")
                return 0  # Return 0 if no message or an invalid message is received


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
