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
        self.battery_confirm = 0
        self.total_cost = 0
        self.agents = agents

    class CyclicStateBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.state == 0:
                await self.request_energy_price()  # Call directly in run
                await self.request_solar_production()  # Call directly in run
                await self.request_batery_status()      
                await self.process_messages1()
                self.agent.state = 1  
            elif self.agent.state == 1 and self.agent.solar_confirm == 1 and self.agent.energy_confirm == 1 and self.agent.battery_confirm == 1:
                await self.broadcast()
                await self.process_messages2()
                self.agent.state = 0
                self.agent.solar_confirm = 0
                self.agent.battery_confirm = 0
                self.agent.energy_confirm = 0
            
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
            if self.solar_energy > 0:
                # Check if the agent is in the priority list
                if agent_id in self.agent.agent_priorities:
                    print(f"[SystemState] Notifying {agent_id} to execute with available solar energy.")
                    
                    # Create a message to send to the agent
                    msg = Message(to=str(agent_id))
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("type", "energy_availablility")
                    
                    # Include solar energy, battery charge, and energy price as comma-separated values
                    msg.body = f"{self.solar_energy},{self.battery_charge},{self.energy_price}"
                    
                    await self.send(msg)  # Send the message
                    print(f"[SystemState] Sent solar energy notification to {agent_id} with details: {msg.body}.")


        async def process_messages1(self):
            print("[SystemState] Collecting  messages1...")
            
            # Collect all incoming messages
            for _ in range(3):
                try:
                    msg = await self.receive(timeout=3)
                    if msg:
                        if(self.agent.state == 0):
                            await self.receive_message1(msg)   
                except asyncio.TimeoutError:
                    print("[SystemState] No more messages received within timeout. Processing queue...")
                    break
        
        async def process_messages2(self):
            print("[SystemState] Collecting messages2...")
            self.battery_used = 0

            # Process incoming messages
            while True:  
                print("Checking for incoming messages...")
                msg = await self.receive(timeout=5)
                if msg:
                    if self.agent.state == 1:
                        await self.receive_message2(msg)
                else:
                    print("[SystemState] No message received within timeout. Breaking loop.")
                    break

            # Process the priority queue
            while not self.agent.priority_queue.empty():
                if self.agent.agents_left == 0:
                    print("[SystemState] All agents have responded. Moving to the next cycle.")
                    break

                _, agent_id = self.agent.priority_queue.get()
                await self.notify_agent(agent_id)

                # Wait for confirmation
                print(f"[SystemState] Waiting for confirmation from {agent_id}...")
                try:
                    msg = await self.receive(timeout=3)
                    if msg and self.agent.state == 1:
                        await self.receive_message2(msg)
                except asyncio.TimeoutError:
                    print(f"[SystemState] Timeout waiting for confirmation from {agent_id}. Continuing...")

            # Send energy differential to battery agent
            energy_left = self.solar_energy - self.battery_used
            battery_agent_id = "solar_battery@localhost"
            msg = Message(to=battery_agent_id)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "energy_differential")
            msg.body = str(energy_left)
            await self.send(msg)
            print("[SystemState] Sent energy differential update to battery agent.")
   
                
                        
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
            """Route incoming messages based on type."""
            
            # Get the message type
            msg_type = xmpp_message.get_metadata("type")
            
            # Check if the message type is "confirmation" and handle comma-separated values
            if msg_type == "confirmation":
                try:
                    # Split and unpack the body directly into solar_used, battery_used, and cost
                    solar_used, battery_used, cost = map(float, xmpp_message.body.split(","))
                    print(f"[SystemState] Confirmation received. Solar used: {solar_used} kWh, Battery used: {battery_used} kWh, Cost: {cost} €.")
                    self.handle_confirmation(xmpp_message.sender, solar_used, battery_used, cost)
                except ValueError:
                    self.agent.agents_left -= 1
                    print("[SystemState] Error parsing confirmation message body.")

            else:
                try:
                    # For other message types, assume a single value
                    data = float(xmpp_message.body)
                    if msg_type == "priority":
                        self.update_priority(xmpp_message.sender, data)
                        self.agent.agents_left += 1
                    else:
                        print(f"[SystemState] Unknown message type: {msg_type}.")
                except ValueError:
                    print(f"[SystemState] Error parsing message body for type {msg_type}.")


        def handle_confirmation(self, sender: str, energy_used: float,battery_used: float,cost: float):
            """Handle confirmation of energy usage and update solar energy."""
            print(f"[SystemState] Received confirmation from {sender} for {energy_used} kWh energy used, and a total cost of {cost}€")
            self.agent.total_cost += cost
            # Update solar energy after confirmed usage
            self.solar_energy = max(0.0, self.solar_energy - energy_used) #evita valores negativos
            self.battery_charge -= battery_used
            self.battery_used = battery_used
            self.agent.agents_left -= 1
            
            print(f"[SystemState] Solar energy after usage by {sender}: {self.solar_energy} kWh.")

        def update_energy_price(self, new_price: float):
            self.energy_price = new_price
            print(f"[SystemState] Energy price updated to {self.energy_price} €/kWh.")

        def update_battery_charge(self, amount: float):
            self.battery_charge = amount
            self.battery_used = 0
            print(f"[SystemState] Battery charge updated to {self.battery_charge} kWh.")

        def update_solar_energy(self, amount: float):
            self.solar_energy = amount
            print(f"[SystemState] Solar energy updated to {self.solar_energy} kWh.")

        def update_priority(self, agent_id: str, priority: float):
            self.agent.agent_priorities[agent_id] = priority
            self.agent.priority_queue.put((-priority, agent_id))
            print(f"[SystemState] Priority for agent {agent_id} set to {priority}.")