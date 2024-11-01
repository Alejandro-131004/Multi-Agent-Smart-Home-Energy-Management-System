from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import pandas as pd
import asyncio
from spade.message import Message
from agents.system_state import SystemState

class EnergyAgent(Agent):
    def __init__(self, jid, password, environment, system_state):
        super().__init__(jid, password)
        self.environment = environment# Refers to the Environment
        self.system_state = system_state
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
            
        self.current_index = 0

    class EnergyBehaviour(CyclicBehaviour):
        def __init__(self, environment, energy_data, current_index,system_state):
            super().__init__()
            self.environment = environment
            self.system_state = system_state
            self.energy_data = energy_data
            self.current_index = current_index

        async def update_price(self):
            """Updates the energy price from the environment."""
            self.agent.current_price = self.environment.get_price_for_current_hour()
            print(f"{self.agent.name}: Updated energy price to {self.agent.current_price} €/kWh.")
    
        async def run(self):
            
            """Cyclic behavior that updates price and solar energy periodically."""
            await self.update_price()
            self.agent.system_state.update_energy_price(self.agent.currentprice)
            msg = Message(to="heater_agent@localhost")  
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "energy_price")   
            msg.body = float(self.currentprice) # posible error
            await self.send(msg)
            print("[Energy agent] Sent energy price message.")
            
            # Wait for a specified period before the next update (e.g., 1 hour in simulation time)
            await asyncio.sleep(10)  # 10 seconds here as an example for testing

    async def setup(self):
        print(f"[EnergyAgent] Agent {self.name} is starting...")
        # Add and start the cyclic behavior
        energy_behaviour = self.EnergyBehaviour(self.environment, self.energy_data, self.current_index,self.system_state)
        self.add_behaviour(energy_behaviour)
