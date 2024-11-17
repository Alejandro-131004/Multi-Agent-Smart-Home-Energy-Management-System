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
            print("[SolarBehaviour] Starting cyclic behaviour...")  # Debugging
            solar_energy = None
            msg = None
            
            # Verifica se os dados de geração solar estão carregados corretamente
            if self.agent.energy_data is None:
                print("[SolarPanel] No solar generation data available. Behaviour suspended.")
                return  # Exit if data has not been loaded correctly

            # Espera por uma mensagem por até 10 segundos
            msg = await self.receive(timeout=10)  # Recebe uma mensagem ou espera por 10 segundos

            if msg:  # Se uma mensagem foi recebida
                # Verifica o tipo da mensagem e, se for "solar_production_request", gera energia solar
                if msg.get_metadata("type") == "solar_production_request":
                    solar_energy = self.agent.get_solar_generation()

            if solar_energy is not None:
                # Se a energia solar foi gerada com sucesso, envia a quantidade para o sistema
                print(f"[SolarPanel] Generating {solar_energy} kWh of energy.")
                
                # Envia uma mensagem informando o sistema sobre a produção de energia solar
                msg = Message(to="system@localhost")
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "solar_energy")
                msg.body = str(solar_energy)
                
                await self.send(msg)  # Envia a mensagem de produção de energia
                print("[SolarPanel] Sent energy production message.")
            else:
                print("[SolarPanel] Unable to generate solar energy.")

            # Espera 10 segundos antes de tentar gerar nova energia
            await asyncio.sleep(10)


    async def setup(self):
        print(f"[SolarPanel] Solar Agent initialized.")
        behaviour = self.SolarBehaviour()
        self.add_behaviour(behaviour)  # Add the cyclic behaviour
        print(f"[SolarPanel] SolarBehaviour added.")

    def get_solar_generation(self):
        """Return the solar generation from the current row of the DataFrame."""
        if self.energy_data is None:
            print("[SolarPanel] Solar energy data not loaded.")
            return None
        if self.current_index >= len(self.energy_data):
            print("[Solar Panel] All data has been processed.")
            return 0

        if self.current_index < len(self.energy_data):
            solar_generation = self.energy_data.iloc[self.current_index]['generation solar']
            print(f"[SolarPanel] Row {self.current_index}, Solar Generation: {solar_generation} kWh.")
            self.current_index += 1  # Move to the next row
            return solar_generation
        else:
            print("[Solar Panel] All data has been processed.")
            return 0  # If there is no more data, return 0


