import pandas as pd
import asyncio
import csv
import os
from math import isnan
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime, timedelta
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
        self.solar_energy_left: float = 0.0
        self.priority_queue = PriorityQueue()
        self.current_agent: Optional[str] = None
        self.agent_priorities = {}
        self.agents_left = 0
        self.state = -1
        self.energy_confirm = 0
        self.solar_confirm = 0
        self.battery_confirm = 0
        self.total_cost = 0
        self.agents = agents
        self.total_energy_wasted = 0
        self.total_energy_revenue = 0
        self.maxdisatisfaction = 0
        self.totaldisatisfaction = 0
        self.totalrequests = 0

        
    
    class CyclicStateBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.current_timestamp = datetime(2015, 1, 1, 0, 0, 0)  # Start at 01-01-2015 00:00:00
            self.solar_energy_left = 0.0
            self.solar_energy_used = 0.0
            self.cost = 0.0
            self.energy_bought = 0.0
            self.battery_charge = 0.0
            self.battery_used = 0.0
            self.energy_price = 0.0 
            self.agent_states = {}
            self.system_state = {
            "inside_temperature": 22.5,  # Default value
            "outside_temperature": 15.0,  # Default value
            "energy_price": 0.12,  # Default price per kWh
            "solar_production": 5.0,  # Default solar production in kW
            "battery_charge " : 0
        }
    
        
        async def run(self):
            if self.agent.state == -1:
                  self.initialize_agent_states()
                  self.agent.state = 0
            if self.agent.state == 0:
                await self.request_energy_price()  # Call directly in run
                await self.request_solar_production()  # Call directly in run
                await self.request_batery_status()      
                await self.process_messages1()
                self.agent.state = 1  
            elif self.agent.state == 1 and self.agent.solar_confirm == 1 and self.agent.energy_confirm == 1 and self.agent.battery_confirm == 1:
                await self.broadcast()
                await self.process_messages2()
                self.log_system_metrics()
                await self.update_agent_states()
                env_agent_id = "environment@localhost"
                msg = Message(to=env_agent_id)
                msg.set_metadata("performative", "request")
                msg.set_metadata("type", "temperature_data")
                await self.send(msg)

                # Receber temperaturas externa e interna
                while True:
                    response = await self.receive(timeout=10)
                    if response and response.get_metadata("type") == "temperature_data":
                        inside_temp, outside_temp = map(float, response.body.split(","))
                        self.system_state["inside_temperature"] = inside_temp
                        self.system_state["outside_temperature"] = outside_temp
                        break
                await self.display_agent_states_gui()
                self.agent.state = 0
                self.agent.solar_confirm = 0
                self.agent.battery_confirm = 0
                self.agent.energy_confirm = 0
                self.solar_energy_left = 0.0
                self.solar_energy_used = 0.0
                self.cost = 0.0
                self.energy_bought = 0.0
                self.battery_charge = 0.0
                self.battery_used = 0.0
                self.energy_price = 0.0 
            await asyncio.sleep(.1)

        async def request_energy_price(self):
            energy_agent_id = "environment@localhost"
            msg = Message(to=energy_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "energy_price_update")  # Must match the receiver's check
            await self.send(msg)
            print("[SystemState] Sent energy price request to env agent.")


        async def request_solar_production(self):
            solar_agent_id = "solar@localhost"
            msg = Message(to=solar_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "solar_production_request")
            
            await self.send(msg)
            print("[SystemState] Sent solar production request to solar agent.")
        
        async def request_batery_status(self):
            battery_agent_id = "solar_battery@localhost"
            msg = Message(to=battery_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "battery_status_request")
            
            await self.send(msg)
            print("[SystemState] Sent battery status request to battery agent.")
        async def broadcast(self):
            for agent_id in self.agent.agents:  # Loop through the list of agent IDs
                # Create a message to send to the agent
                msg = Message(to=str(agent_id))
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "solar_auction_started")
                await self.send(msg)  # Send the message
                print(f"[SystemState] Sent solar energy notification to {agent_id}.")

        
        async def notify_agent(self, agent_id: str):
            # Check if there is available solar energy
           
            # Check if the agent is in the priority list
            if agent_id in self.agent.agent_priorities:
                print(f"[SystemState] Notifying {agent_id} to execute with available solar energy.")
                
                # Create a message to send to the agent
                msg = Message(to=str(agent_id))
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "energy_availablility")
                
                # Include solar energy, battery charge, and energy price as comma-separated values
                msg.body = f"{self.solar_energy_left},{self.battery_charge},{self.energy_price}"
                
                await self.send(msg)  # Send the message
                print(f"[SystemState] Sent solar energy notification to {agent_id} with details: {msg.body}.")


        async def process_messages1(self):
            print("[SystemState] Collecting  messages1...")
            
            # Collect all incoming messages
            for _ in range(3):
                try:
                    msg = await self.receive(timeout=1)
                    if msg:
                        if(self.agent.state == 0):
                            await self.receive_message1(msg)   
                except asyncio.TimeoutError:
                    print("[SystemState] No more messages received within timeout. Processing queue...")
                    break
        
        async def process_messages2(self):
            print("[SystemState] Collecting messages2...")
            self.battery_used = 0  # Reset battery_used for each loop iteration

            while True:
                print("Checking for incoming messages...")
                msg = await self.receive(timeout=2)
                if msg:
                    if self.agent.state == 1:
                        await self.receive_message2(msg)
                else:
                    print("[SystemState] No message received within timeout. Breaking loop.")
                    break

            while not self.agent.priority_queue.empty():
                if self.agent.agents_left == 0:
                    print("[SystemState] All agents have responded. Moving to the next cycle.")
                    break

                _, agent_id = self.agent.priority_queue.get()
                await self.notify_agent(agent_id)

                # Wait for confirmation
                while True:
                    print(f"[SystemState] Waiting for confirmation from {agent_id}...")
                    msg = await self.receive(timeout=5)
                    if msg:
                        await self.receive_message2(msg)
                        break
                    else:
                        break  # Exit loop once the message is processed

            # Send energy differential to battery agent
            energy_left = self.solar_energy_left - self.battery_used
            print(f"[System] energy left {energy_left}")
            battery_agent_id = "solar_battery@localhost"
            msg = Message(to=battery_agent_id)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "energy_differencial")
            msg.body = str(energy_left)
            await self.send(msg)
            print("[SystemState] Sent energy differential update to battery agent.")
            self.energy_to_sell = 0
            msg = await self.receive(timeout=1)
            if msg and msg.get_metadata("type") == "energy_to_sell":
                self.energy_to_sell = float(msg.body)
            self.agent.total_energy_wasted += self.energy_to_sell
            self.agent.total_energy_revenue += self.energy_to_sell * self.energy_price * 0.5

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
            elif msg_type == "battery_charge":
                self.agent.battery_confirm = 1
                self.update_battery_charge(data)    

        async def receive_message2(self, xmpp_message: Message):
            print("Message received!")
            msg_type = xmpp_message.get_metadata("type")

            if msg_type == "confirmation":
                try:
                    solar_used, battery_used, cost = map(float, xmpp_message.body.split(","))
                    print(f"[SystemState] Confirmation received. Solar used: {solar_used} kWh, Battery used: {battery_used} kWh, Cost: {cost} €.")
                    self.update_agent_usage(xmpp_message.sender, battery_used, solar_used, cost)
                    self.handle_confirmation(xmpp_message.sender, solar_used, battery_used, cost)
                except ValueError:
                    self.agent.agents_left -= 1
                    print("[SystemState] Error parsing confirmation message body.")
            else:
                try:
                    data = float(xmpp_message.body)
                    if msg_type == "priority":
                        self.update_priority(xmpp_message.sender, data)
                        self.agent.agents_left += 1
                        self.agent.totalrequests += 1
                        self.agent.totaldisatisfaction += 1
                        if data > self.agent.maxdisatisfaction:
                            self.agent.maxdisatisfaction = data
                    else:
                        print(f"[SystemState] Unknown message type: {msg_type}.")
                except ValueError:
                    print(f"[SystemState] Error parsing message body for type {msg_type}.")


        def handle_confirmation(self, sender: str, energy_used: float, battery_used: float, cost: float):
            if battery_used < 0 or energy_used < 0 or cost < 0:
                print("[SystemState] Invalid values received in confirmation.")
                return

            print(f"[SystemState] Received confirmation from {sender} for {energy_used} kWh energy used, and a total cost of {cost}€")
            self.agent.total_cost += cost
            self.solar_energy_left = max(0.0, self.solar_energy_left - energy_used)
            self.solar_energy_used += energy_used
            self.cost += cost
            self.energy_bought += cost / self.energy_price
            self.battery_charge -= battery_used
            self.battery_used += battery_used
            self.agent.agents_left -= 1


        def update_energy_price(self, new_price: float):
            self.system_state["energy_price"] = new_price
            self.energy_price = new_price
            print(f"[SystemState] Energy price updated to {self.energy_price} €/kWh.")

        def update_battery_charge(self, amount: float):
            self.battery_charge = amount
            self.system_state["battery_charge"] = amount
            self.battery_used = 0
            print(f"[SystemState] Battery charge updated to {self.battery_charge} kWh.")

        def update_solar_energy(self, amount: float):
            self.solar_energy_left = amount
            self.system_state["solar_production"] = amount
            print(f"[SystemState] Solar energy updated to {self.solar_energy_left} kWh.")

        def update_priority(self, agent_id: str, priority: float):
            self.agent.agent_priorities[agent_id] = priority
            self.agent.priority_queue.put((-priority, agent_id))
            print(f"[SystemState] Priority for agent {agent_id} set to {priority}.")
            
        def log_system_metrics(self):
            """
            Logs the agent's performance metrics to a CSV file.

            Assumes the following attributes exist in the agent:
            - self.total_energy_wasted
            - self.total_energy_revenue
            - self.energy_used
            - self.battery_used
            - self.cost
            - self.total_cost
            - self.solar_energy_left
            - self.solar_energy_used
            - self.energy_bought
            - self.battery_charge
            - self.battery_used
            """
            # Ensure the directory exists
            output_dir = "metrics_logs"
            os.makedirs(output_dir, exist_ok=True)

            # Define the CSV file path
            csv_file = os.path.join(output_dir, "system_metrics.csv")

            
            metrics_data = {
                "timestamp": self.current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "soalr_energy_wasted": self.energy_to_sell,
                "total_solar_energy_wasted": self.agent.total_energy_wasted,
                "solar_energy_revenue": self.energy_to_sell*self.energy_price,
                "total_solar_energy_revenue": self.agent.total_energy_revenue,
                "battery_used": self.battery_used,
                "cost": self.cost,
                "total_cost": self.agent.total_cost,
                "solar_energy_left": self.solar_energy_left,
                "solar_energy_used": self.solar_energy_used,
                "energy_bought": self.energy_bought,
                "battery_charge": self.battery_charge,
                "battery_used": self.battery_used,  # Added again to ensure all references are included
            }

            # Write metrics to CSV
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=metrics_data.keys())

                if not file_exists:
                    writer.writeheader()  # Write header only once

                writer.writerow(metrics_data)
            self.current_timestamp += timedelta(hours=1)

            print(f"[SystemState] Metrics logged to {csv_file}: {metrics_data}")
            
    
        def initialize_agent_states(self):
            """
            Initializes self.agent_states for all agents with default values.
            """
            for agent_id in self.agent.agents:
                normalized_id = self.normalize_agent_id(agent_id)
                if normalized_id not in self.agent_states:
                    self.agent_states[normalized_id] = {
                        "state": "Pending",  # Default placeholder for state
                        "battery_used": "Pending",  # Placeholder for battery usage
                        "solar_used": "Pending",  # Placeholder for solar usage
                        "cost": "Pending",  # Placeholder for cost
                        "is_complete": False,  # Indicates if all data has been received
                    }

        def normalize_agent_id(self, agent_id):
            """
            Ensures the agent ID is consistently formatted.
            """
            # Ensure that agent_id is a string and print the type for debugging
            agent_id = str(agent_id)  # Convert to string to ensure consistency
            print(f"Normalized agent_id (type: {type(agent_id)}): {agent_id}")  # Debugging output
            return agent_id.replace(" ", "").lower()


        def update_agent_usage(self, agent, battery_used=None, solar_used=None, cost=None):
            """
            Updates the battery, solar, and cost data for an agent.
            """
            agent = self.normalize_agent_id(agent)
            if agent not in self.agent_states:
                self.agent_states[agent] = {
                    "state": "Pending",
                    "battery_used": "Pending",
                    "solar_used": "Pending",
                    "cost": "Pending",
                    "is_complete": False,
                }
            # Update usage fields
            if battery_used is not None:
                self.agent_states[agent]["battery_used"] = float(battery_used)
            if solar_used is not None:
                self.agent_states[agent]["solar_used"] = float(solar_used)
            if cost is not None:
                self.agent_states[agent]["cost"] = float(cost)


        async def update_agent_states(self):
            """
            Sends state request messages to all agents and updates the state of the ones that respond.
            """
            # Send requests to all agents
            for agent_id in self.agent.agents:
                msg = Message(to=agent_id)  # Create a message
                msg.set_metadata("performative", "request")  # Set the type of message
                msg.set_metadata("type", "state_request")  # Add a custom metadata
                msg.body = "Requesting current state"  # Add a body message
                await self.send(msg)  # Send the message
                print(f"State request sent to {agent_id}")

            # Wait for responses
            pending_agents = set(self.agent.agents)  # Track agents that are pending responses

            while pending_agents:
                response = await self.receive(timeout=5)  # Wait for a response with a timeout
                if response:
                    sender_id = self.normalize_agent_id(str(response.sender))  # Normalize sender ID
                    if sender_id in pending_agents:
                        # Update state from response
                        self.agent_states[sender_id]["state"] = response.body
                        print(f"Updated state for {sender_id}: {response.body}")
                        pending_agents.remove(sender_id)

                        # Check completeness
                        if self.agent_states[sender_id]["state"] != "Pending" and \
                        self.agent_states[sender_id]["battery_used"] != "Pending" and \
                        self.agent_states[sender_id]["solar_used"] != "Pending" and \
                        self.agent_states[sender_id]["cost"] != "Pending":
                            self.agent_states[sender_id]["is_complete"] = True
                    else:
                        print(f"Unexpected response from {sender_id}, ignoring.")
                else:
                    # If no response, log a timeout and stop waiting
                    print("No response received within timeout.")
                    break





        async def display_agent_states_gui(self):
            """
            Creates a GUI to display agent states and system-wide states, and allows resetting states and updating preferences.
            """

            def reset_states():
                """Resets 'battery_used', 'solar_used', 'cost', and 'battery_charge' fields to 'N/A'."""
                for agent in self.agent_states:
                    if isinstance(self.agent_states[agent], dict):
                        self.agent_states[agent]["battery_used"] = "N/A"
                        self.agent_states[agent]["solar_used"] = "N/A"
                        self.agent_states[agent]["cost"] = "N/A"
                self.system_state["battery_charge"] = "N/A"
                root.destroy()

            def update_preferences():
                """Abre uma janela para atualizar apenas as preferências de divisões e temperatura desejada."""

                def save_preferences():
                    try:
                        # Obter os valores de entrada ou usar os padrões
                        num_divisions = int(divisions_entry.get() or 5)  # Default is 5
                        desired_temperature = float(temp_entry.get() or 40.0)  # Default is 40.0

                        # Enviar as mudanças para a função notify_agents_changes
                        asyncio.create_task(self.notify_agents_changes(num_divisions=num_divisions, desired_temperature=desired_temperature))

                        # Fechar a janela de preferências
                        preferences_window.destroy()
                    except ValueError as e:
                        messagebox.showerror("Error", f"Entrada inválida: {e}")

                # Criar uma nova janela para preferências
                preferences_window = tk.Toplevel(root)
                preferences_window.title("Update Preferences")

                # Entrada para o número de divisões
                tk.Label(preferences_window, text="Number of Divisions:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
                divisions_entry = tk.Entry(preferences_window, width=25)
                divisions_entry.grid(row=0, column=1, padx=10, pady=5)

                # Entrada para a temperatura desejada
                tk.Label(preferences_window, text="Desired Temperature:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
                temp_entry = tk.Entry(preferences_window, width=25)
                temp_entry.grid(row=1, column=1, padx=10, pady=5)

                # Botão para salvar as alterações
                save_button = tk.Button(preferences_window, text="Save Preferences", command=save_preferences)
                save_button.grid(row=2, column=0, columnspan=2, pady=10)

            root = tk.Tk()
            root.title("Agent States and System State")

            # Create Treeview with system state
            tree = ttk.Treeview(root, columns=("Agent", "State", "Battery Used", "Solar Used", "Cost", 
                                                "Inside Temp", "Outside Temp", "Energy Price", "Solar Production", "Battery Charge"), 
                                show="headings")
            tree.heading("Agent", text="Agent")
            tree.heading("State", text="State")
            tree.heading("Battery Used", text="Battery Used")
            tree.heading("Solar Used", text="Solar Used")
            tree.heading("Cost", text="Cost")
            tree.heading("Inside Temp", text="Inside Temp")
            tree.heading("Outside Temp", text="Outside Temp")
            tree.heading("Energy Price", text="Energy Price")
            tree.heading("Solar Production", text="Solar Production")
            tree.heading("Battery Charge", text="Battery Charge")
            tree.pack(fill=tk.BOTH, expand=True)

            # Fill Treeview
            for agent, state in self.agent_states.items():
                battery_charge = self.system_state.get("battery_charge", "N/A")
                if isinstance(state, dict):
                    tree.insert("", tk.END, values=(agent, state.get("state", "N/A"), state.get("battery_used", "N/A"),
                                                    state.get("solar_used", "N/A"), state.get("cost", "N/A"),
                                                    self.system_state.get("inside_temperature", "N/A"), 
                                                    self.system_state.get("outside_temperature", "N/A"),
                                                    self.system_state.get("energy_price", "N/A"),
                                                    self.system_state.get("solar_production", "N/A"), 
                                                    battery_charge))
                else:
                    tree.insert("", tk.END, values=(agent, state, "N/A", "N/A", "N/A",
                                                    self.system_state.get("inside_temperature", "N/A"), 
                                                    self.system_state.get("outside_temperature", "N/A"),
                                                    self.system_state.get("energy_price", "N/A"),
                                                    self.system_state.get("solar_production", "N/A"), 
                                                    battery_charge))

            tk.Button(root, text="Close", command=reset_states).pack(pady=5)
            tk.Button(root, text="Update Preferences", command=update_preferences).pack(pady=5)

            root.mainloop()

        async def notify_agents_changes(self, num_divisions, desired_temperature):
            """Função que processa as mudanças nas preferências e notifica os agentes."""
            
            # Verifica se a temperatura desejada foi alterada
            if desired_temperature == self.system_state.get("desired_temperature", None):
                # Caso não haja alterações
                print(f"Nenhuma mudança detectada na temperatura desejada. Notificando agentes com 'no_changes'.")
                msg_metadata = "no_changes"
                msg_body = "No changes to desired temperature."
            else:
                # Caso a temperatura seja alterada
                print(f"Temperatura desejada alterada para {desired_temperature}. Notificando agentes.")
                msg_metadata = "preference_update"
                msg_body = f"{desired_temperature}"

                # Atualiza o estado do sistema com a nova temperatura
                self.system_state["desired_temperature"] = desired_temperature

            # Lista de agentes a serem notificados
            agents = ["heater@localhost", "windows@localhost", "aircon@localhost", "environment@localhost"]

            for agent in agents:
                # Criar a mensagem
                msg = Message(to=agent)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", msg_metadata)
                msg.body = msg_body

                # Enviar a mensagem (método assíncrono)
                try:
                    await self.send(msg)
                    print(f"Mensagem enviada para {agent}: {msg.body}")
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {agent}: {e}")

