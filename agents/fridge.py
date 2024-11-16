from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class FridgeAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    class FridgeBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.consumption = 0.0  # Total energy consumption initialized to 0
            self.priority = 0
        async def run(self):
            energy_price = None
            # Request the current energy price from the SystemState
            while True:
                msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
                if msg and msg.get_metadata("type") == "energy_price":
                    energy_price = float(msg.body)
                    print(f"[Fridge] Current electricity price: {energy_price} €/kWh")
                    break  # Exit the loop once the desired message is processed
                elif msg:
                    print(f"[Fridge] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Fridge] No message received within the timeout.")
                    break

            self.priority = 10
            # Sending the priority request message
            request_msg = Message(to="system@localhost")  # You are sending to a specific agent
            request_msg.set_metadata("performative", "request")
            request_msg.set_metadata("type", "priority")
            request_msg.body = str(self.priority)  # The message body contains dissatisfaction value
            await self.send(request_msg)


            # Wait for the response from the SystemState agent
            response = await self.receive(timeout=10)
            print("[heater] recived solar from system")
            if response and response.get_metadata("type") == "solar_energy_available":
                solar_energy_available = float(response.body)
            # Simulate the fridge consuming a constant amount of energy
            consumption_amount = 0.5  # Fixed consumption for this cycle

            solar_energy_consumed,cost = self.calculate_comsumption(consumption_amount,solar_energy_available,energy_price)
            print(f"[Fridge] Consuming energy... Total: solar{solar_energy_consumed} kWh, cost {cost}")
            msg = Message(to="system@localhost")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "confirmation")
            msg.body = f"{solar_energy_consumed},{cost}" 
            await self.send(msg)
            # Simulate waiting time before the next cycle
            await asyncio.sleep(.1)  # Adjust the sleep duration as needed
        def calculate_comsumption(self,consumption_amount,solar_energy_available,energy_price):
            # If solar energy can fully cover the consumption
            if solar_energy_available >= consumption_amount:
                solar_used = consumption_amount
                cost = 0  # No additional cost since solar covers all
            else:
                # Use as much solar energy as available
                solar_used = solar_energy_available
                # Calculate cost for the remaining energy
                remaining_energy = consumption_amount - solar_energy_available
                cost = remaining_energy * energy_price

            return solar_used, cost
                
        
