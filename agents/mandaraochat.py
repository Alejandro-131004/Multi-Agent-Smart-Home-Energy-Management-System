quero que me ajudes a mudar o meu codigo.

O solar panel tem de passar também a enviar os valores da bateria para o system state
Atualmente só envia energia solar
Outra coisa atualmente o agente battery é um sub agente de solar panel pode ser uma boa ideia torna-los independentes
Assim um agente guarda energia e o outro produz não faz sentido estarem ligados
A ideia era tornar a bateria independente e ser um agente normal com cyclic behavior e depois o agente solar panel e battery cada um envia a sua informação para o system state e recebe informação de forma independente


from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import pandas as pd
import asyncio
from spade.message import Message

class SolarPanelAgent(Agent):
    def __init__(self, jid, password, solar_battery):
        super().__init__(jid, password)
        self.solar_battery = solar_battery  # SolarBattery associated with this agent
        
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
            if self.agent.energy_data is None:
                print("[SolarPanelAgent] No solar generation data available. Behaviour suspended.")
                return  # Exit if data has not been loaded correctly

            # Listen for incoming requests
            msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
            if msg:
                if msg.get_metadata("type") == "solar_production_request":
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
            await asyncio.sleep(.1)

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

        if self.current_index < len(self.energy_data):
            solar_generation = self.energy_data.iloc[self.current_index]['generation solar']
            print(f"[SolarPanelAgent] Row {self.current_index}, Solar Generation: {solar_generation} kWh.")
            self.current_index += 1  # Move to the next row
            return solar_generation
        else:
            print("[Solar Panel] All data has been processed.")
            return 0  # If there is no more data, return 0

            '''if solar_energy is not None:
                print(f"[Painel Solar] Gerando {solar_energy} kWh de energia")
                # Carregar a SolarBattery com a energia gerada, se válida
                if solar_energy > 0:
                    self.agent.solar_battery.charge(solar_energy)
                else:
                    print("[Painel Solar] Sem energia solar para carregar.")
            else:
                print("[Painel Solar] Não foi possível gerar energia solar.")

            # Espera 10 segundos até gerar nova energia
            await asyncio.sleep(10)'''

class SolarBattery:
    def __init__(self, capacity_kwh, charge_efficiency=0.9, discharge_efficiency=0.9):
        self.capacity_kwh = capacity_kwh
        self.current_charge_kwh = 0  # Inicialmente a bateria está vazia
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency

    def charge(self, solar_energy_kwh):
        # Verificar se há energia suficiente para carregar
        if solar_energy_kwh <= 0:
            print("[SolarBattery] Energia solar inválida para carregar. Nenhuma ação realizada.")
            return 0

        print(f"[SolarBattery] Tentando carregar com {solar_energy_kwh:.2f} kWh de energia solar.")
        energy_to_store = solar_energy_kwh * self.charge_efficiency
        available_space = self.capacity_kwh - self.current_charge_kwh

        print(f"[SolarBattery] Energia a armazenar: {energy_to_store:.2f} kWh")
        print(f"[SolarBattery] Espaço disponível: {available_space:.2f} kWh")

        # Verifica o quanto de energia pode ser realmente armazenado sem ultrapassar a capacidade
        energy_stored = min(energy_to_store, available_space)
        self.current_charge_kwh += energy_stored
        print(f"[SolarBattery] Armazenou {energy_stored:.2f} kWh de energia solar. Energia atual armazenada: {self.current_charge_kwh:.2f} kWh.")
        return energy_stored

    def discharge(self, energy_needed_kwh):
        # Verificar se a energia solicitada é válida
        if energy_needed_kwh <= 0:
            print("[SolarBattery] Valor de energia solicitado inválido. Nenhuma ação realizada.")
            return 0

        print(f"[SolarBattery] Verificando se há energia solar disponível...")
        
        # Verifica se há carga suficiente na bateria
        if self.current_charge_kwh > 0:
            available_energy = self.current_charge_kwh * self.discharge_efficiency
            print(f"[SolarBattery] Há {available_energy:.2f} kWh de energia solar disponível.")
        else:
            print("[SolarBattery] Não há energia solar disponível.")
            return 0  # Se não há energia, retorna 0 imediatamente

        # Fornece a quantidade de energia necessária ou o máximo disponível
        energy_provided = min(energy_needed_kwh, available_energy)
        self.current_charge_kwh -= energy_provided / self.discharge_efficiency
        print(f"[SolarBattery] Forneceu {energy_provided:.2f} kWh de energia solar. Energia restante: {self.current_charge_kwh:.2f} kWh.")
        return energy_provided

    def get_state_of_charge(self):
        print(f"[SolarBattery] Estado atual da carga: {self.current_charge_kwh:.2f} kWh.")
        return self.current_charge_kwh

import pandas as pd
import asyncio
from queue import PriorityQueue
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from typing import Dict, Optional

class SystemState(Agent):
    def __init__(self, jid, password,agents):
        super().__init__(jid, password)
        self.energy_price: float = 0.0
        self.battery_charge: float = 0.0
        self.solar_energy: float = 0.0
        self.priority_queue = PriorityQueue()
        self.current_agent: Optional[str] = None
        self.agent_priorities = {}
        self.agents_left = 0
        self.state = 0
        self.energy_confirm = 0
        self.solar_confirm = 0
        self.total_cost = 0
        self.agents = agents
    async def setup(self):
        print("[SystemState] Agent is running.")
        # Add CyclicStateBehaviour as behavior to this agent
        self.add_behaviour(self.CyclicStateBehaviour())
        print("[SystemState] CyclicStateBehaviour added.")

    class CyclicStateBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.state == 0:
                await self.request_energy_price()  # Call directly in run
                await self.request_solar_production()  # Call directly in run
                                   
                await self.process_messages1()
                self.agent.state = 1  
            elif self.agent.state == 1 and self.agent.solar_confirm == 1 and self.agent.energy_confirm == 1:
                await self.process_messages2()
                self.agent.state = 0
                self.agent.solar_confirm = 0
                self.agent.energy_confirm = 0
            
            await asyncio.sleep(.1)

        async def request_energy_price(self):
            energy_agent_id = "energy_agent@localhost"
            msg = Message(to=energy_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "energy_price_request")  # Must match receiver's check
            await self.send(msg)
            print("[SystemState] Sent energy price request to energy agent.")

        async def request_solar_production(self):
            solar_agent_id = "solar@localhost"
            msg = Message(to=solar_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "solar_production_request")
            
            await self.send(msg)
            print("[SystemState] Sent solar production request to solar agent.")
        async def process_messages1(self):
            print("[SystemState] Collecting  messages1...")
            
            # Collect all incoming messages
            for _ in range(2):
                try:
                    msg = await self.receive(timeout=1)
                    if msg:
                        if(self.agent.state == 0):
                            await self.receive_message1(msg)   
                except asyncio.TimeoutError:
                    print("[SystemState] No more messages received within timeout. Processing queue...")
                    break
        
        async def process_messages2(self):
            print("[SystemState] Collecting  messages2...")
            
            # Collect all incoming messages
            while True:  # Continuous loop
                print("Checking for incoming messages...")
                try:
                    msg = await self.receive(timeout=1)  # Wait for a message with a 1-second timeout
                    if msg:  # If a message is received
                        if self.agent.state == 1:  # Only process the message if the agent's state is 1
                            await self.receive_message2(msg)  # Process the message
                    else:  # If no message is received within the timeout
                        print("[SystemState] No message received within the timeout. Processing the queue...")
                        break  # Exit the loop to avoid indefinite waiting
                except asyncio.TimeoutError:
                    print("[SystemState] Timeout occurred, no message received.")

            # After the loop, process any pending messages or tasks

            
            # Process agents in the priority queue with confirmation check
            while not self.agent.priority_queue.empty():
                _, agent_id = self.agent.priority_queue.get()
                await self.notify_agent(agent_id)

                # Wait for confirmation from the agent
                print(f"[SystemState] Waiting for confirmation from {agent_id}...")
                while self.agent.agents_left > 0:
                    try:
                        msg = await self.receive(timeout=1)
                        if msg:
                            await self.receive_message2(msg)
                    except asyncio.TimeoutError:
                        continue
                self.agent.agents_left = 0
        async def notify_agent(self, agent_id: str):
            if agent_id in self.agent.agent_priorities:
                print(f"[SystemState] Notifying {agent_id} to execute with available solar energy.")
                msg = Message(to=str(agent_id))
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "solar_energy_available")
                msg.body = str(self.solar_energy)
                
                await self.send(msg)
                print(f"[SystemState] Sent notification message to {agent_id}.")
        async def receive_message1(self, xmpp_message: Message):
            """Route incoming messages based on type."""
            msg_type = xmpp_message.get_metadata("type")
            data = float(xmpp_message.body)

            if msg_type == "energy_price":
                self.update_energy_price(data)
                print("energy price recived")
                self.agent.energy_confirm = 1
            elif msg_type == "solar_energy":
                self.update_solar_energy(data)
                print("solar production recived")
                self.agent.solar_confirm = 1      

        async def receive_message2(self, xmpp_message: Message):
            print("Message received!")
            """Route incoming messages based on type."""
            
            # Get the message type
            msg_type = xmpp_message.get_metadata("type")
            
            # Check if the message type is "confirmation" and handle comma-separated values
            if msg_type == "confirmation":
                try:
                    # Split the body by commas and convert to floats
                    values = [float(val) for val in xmpp_message.body.split(",")]
                    if len(values) == 2:
                        solar_used, cost = values
                        print(f"[SystemState] Confirmation received. Solar used: {solar_used} kWh, Cost: {cost} €.")
                        self.handle_confirmation(xmpp_message.sender, solar_used, cost)  # Pass both values
                    else:
                        print("[SystemState] Invalid confirmation message format.")
                except ValueError:
                    print("[SystemState] Error parsing confirmation message body.")
            else:
                try:
                    # For other message types, assume a single value
                    data = float(xmpp_message.body)
                    if msg_type == "battery_charge":
                        self.update_battery_charge(data)
                    elif msg_type == "priority":
                        self.update_priority(xmpp_message.sender, data)
                        self.agent.agents_left += 1
                    else:
                        print(f"[SystemState] Unknown message type: {msg_type}.")
                except ValueError:
                    print(f"[SystemState] Error parsing message body for type {msg_type}.")


        def handle_confirmation(self, sender: str, energy_used: float,cost: float):
            """Handle confirmation of energy usage and update solar energy."""
            print(f"[SystemState] Received confirmation from {sender} for {energy_used} kWh energy used, and a total cost of {cost}€")
            self.agent.total_cost += cost
            # Update solar energy after confirmed usage
            self.solar_energy -= energy_used
            print(f"[SystemState] Solar energy after usage by {sender}: {self.solar_energy} kWh.")

        def update_energy_price(self, new_price: float):
            self.energy_price = new_price
            print(f"[SystemState] Energy price updated to {self.energy_price} €/kWh.")

        def update_battery_charge(self, amount: float):
            self.battery_charge += amount
            self.battery_charge = max(0.0, self.battery_charge)
            print(f"[SystemState] Battery charge updated to {self.battery_charge} kWh.")

        def update_solar_energy(self, amount: float):
            self.solar_energy = amount
            print(f"[SystemState] Solar energy updated to {self.solar_energy} kWh.")

        def update_priority(self, agent_id: str, priority: float):
            self.agent.agent_priorities[agent_id] = priority
            self.agent.priority_queue.put((-priority, agent_id))
            print(f"[SystemState] Priority for agent {agent_id} set to {priority}.")
            