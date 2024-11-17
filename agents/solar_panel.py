from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import pandas as pd
import asyncio
from spade.message import Message

class SolarPanelAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        
        
        
        # Try to read the CSV and check if the 'generation solar' column exists
        try:
            self.energy_data = pd.read_csv("energy_dataset.csv", parse_dates=['time'])
            print(self.energy_data)
            if 'generation solar' not in self.energy_data.columns:
                raise ValueError("[Error] Column 'generation solar' not found in the CSV.")
            print("[SolarPanelAgent] CSV loaded successfully. Solar generation data available.")
        except FileNotFoundError:
            print("[Error] 'energy_dataset.csv' file not found.")
            self.energy_data = None
        except pd.errors.EmptyDataError:
            print("[Error] CSV file is empty or invalid.")
            self.energy_data = None
        except Exception as e:
            print(f"[Error] Problem reading the CSV: {e}")
            self.energy_data = None
        
        self.current_index = 0  # Index to control the current row

    class SolarBehaviour(CyclicBehaviour):
        async def run(self):
            solar_energy = None
            print("[SolarBehaviour] Starting cyclic behaviour...")  # Debugging

            if self.agent.energy_data is None:
                print("[SolarPanelAgent] No solar generation data available. Behaviour suspended.")
                return  # Exit if data has not been loaded correctly

            # Listen for incoming requests
            msg = await self.receive(timeout=15)  # Wait for a message for up to 10 seconds
            if not msg:
                print("[SolarPanelAgent] No messages received within timeout period.")
            if msg:
                if msg.get_metadata("type") == "price_request":  # Check if the message is a price request
                    solar_energy = self.agent.get_solar_generation()
            
            if solar_energy is not None:
                print(f"[SolarPanel] Generating {solar_energy} kWh of energy.")
                
                # Send the energy production update to the system state
                msg = Message(to="system@localhost")
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "solar_energy")
                msg.body = str(solar_energy)
                
                await self.send(msg)  # Send the solar energy message
                print("[SolarPanel] Sent energy production message.")
            else:
                print("[SolarPanel] Unable to generate solar energy.")

            # Wait for 10 seconds until generating new energy
            await asyncio.sleep(10)

    async def setup(self):
        print(f"[SolarPanel] Solar Agent initialized.")
        behaviour = self.SolarBehaviour()
        self.add_behaviour(behaviour)  # Add the cyclic behaviour
        print(f"[SolarPanelAgent] SolarBehaviour added.")

    def get_solar_generation(self):
        """Return the solar generation from the current row of the DataFrame."""
        if self.energy_data is None:
            print("[SolarPanelAgent] Solar energy data not loaded.")
            return None
        if self.current_index >= len(self.energy_data):
            print("[Solar Panel] All data has been processed.")
            return 0

        if self.current_index < len(self.energy_data):
            solar_generation = self.energy_data.iloc[self.current_index]['generation solar']
            print(f"[SolarPanelAgent] Row {self.current_index}, Solar Generation: {solar_generation} kWh.")
            self.current_index += 1  # Move to the next row
            return solar_generation
        else:
            print("[Solar Panel] All data has been processed.")
            return 0  # If there is no more data, return 0


