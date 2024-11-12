from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import pandas as pd
from spade.message import Message

class EnergyAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment  # Refers to the Environment
        
        self.current_price = 3000  # Initial energy price
        self.threshold_price = 0.20  # Price threshold for using grid energy

        # Load energy data from CSV
        try:
            self.energy_data = pd.read_csv("energy_dataset.csv", parse_dates=['time'])
            if 'generation solar' not in self.energy_data.columns:
                raise ValueError("[Error] Column 'generation solar' not found in CSV.")
            print("[EnergyAgent] CSV loaded successfully. Solar generation data available.")
        except FileNotFoundError:
            print("[Error] File 'energy_dataset.csv' not found.")
            self.energy_data = None
        except pd.errors.EmptyDataError:
            print("[Error] CSV file is empty or invalid.")
            self.energy_data = None
        except Exception as e:
            print(f"[Error] Problem reading CSV: {e}")
            self.energy_data = None
            
        self.current_index = 0  # Initialize current index for energy data

    class EnergyBehaviour(CyclicBehaviour):
        def __init__(self, environment, energy_data):
            super().__init__()
            self.environment = environment
            self.energy_data = energy_data

        async def update_price(self):
            """Updates the energy price from the environment."""
            self.agent.current_price = self.environment.get_price_for_current_hour()
            print(f"{self.agent.name}: Updated energy price to {self.agent.current_price} €/kWh.")

        async def run(self):
            """Cyclic behavior that listens for requests and updates the price accordingly."""
            print(f"[EnergyAgent] Waiting for requests...")

            # Listen for incoming requests
            msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
            if msg:
                if msg.get_metadata("type") == "energy_price_request":  # Check if the message is a price request
                    await self.update_price()  # Update the price

                    # Send the updated energy price to the SystemState agent
                    price_msg = Message(to="system@localhost")  # Corrected line
                    price_msg.set_metadata("performative", "inform")
                    price_msg.set_metadata("type", "energy_price")
                    price_msg.body = str(self.agent.current_price)

                    await self.send(price_msg)  # Send the updated price message
                    print(f"[EnergyAgent] Sent energy price update: {self.agent.current_price} €/kWh.")

                    # Example of accessing the current index
                    if self.agent.energy_data is not None and self.agent.current_index < len(self.agent.energy_data):
                        # Process the energy data if available
                        solar_generation = self.agent.energy_data.iloc[self.agent.current_index]['generation solar']
                        print(f"[EnergyAgent] Processing solar generation: {solar_generation} kWh.")
                        self.agent.current_index += 1  # Move to the next index
                    else:
                        print("[EnergyAgent] No more energy data to process or data not loaded.")
            else:
                solar_generation = 0
                self.current_index += 1
                print("[EnergyAgent] Error when reciving message")

    async def setup(self):
        print(f"[EnergyAgent] Agent {self.name} is starting...")
        # Create the behaviour with the required parameters
        energy_behaviour = self.EnergyBehaviour(self.environment, self.energy_data)
        self.add_behaviour(energy_behaviour)  # Add the behaviour to the agent
