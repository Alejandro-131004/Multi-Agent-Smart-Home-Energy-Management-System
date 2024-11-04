from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class FridgeAgent(Agent):
    def __init__(self, jid, password, system_state):
        super().__init__(jid, password)
        self.system_state = system_state  # Reference to the SystemState dataclass
        self.consumption = 0.0  # Total energy consumption initialized to 0

    class FridgeBehaviour(CyclicBehaviour):
        def __init__(self, system_state):
            super().__init__()
            self.system_state = system_state  # Reference to the SystemState dataclass

        async def run(self):
            # Request the current energy price from the SystemState
            energy_price = self.system_state.energy_price
            print(f"[Fridge] Current electricity price: {energy_price} €/kWh")

            # Simulate the fridge consuming a constant amount of energy
            consumption_amount = 0.5  # Fixed consumption for this cycle
            self.consumption += consumption_amount  # Update total consumption

            # Report energy consumption to the SystemState
            self.system_state.receive_message(sender="fridge", msg_type="confirmation", data=consumption_amount)
            print(f"[Fridge] Consuming energy... Total: {self.consumption} kWh")

            # Simulate waiting time before the next cycle
            await asyncio.sleep(10)  # Adjust the sleep duration as needed

    async def setup(self):
        print(f"[Fridge] Fridge Agent initialized.")
        self.add_behaviour(self.FridgeBehaviour(self.system_state))
