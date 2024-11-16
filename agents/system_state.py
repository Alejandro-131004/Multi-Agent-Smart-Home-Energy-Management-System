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
        self.agents_ready = 0
        self.state = 0
        self.energy_confirm = 0
        self.solar_confirm = 0
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
                while self.agent.agents_ready == 0:
                    try:
                        msg = await self.receive(timeout=1)
                        if msg:
                            await self.receive_message2(msg)
                    except asyncio.TimeoutError:
                        continue

                # Reset confirmation flag for next agent
                self.agent.agents_ready = 0

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
            print("message recived !!!!!!!!!!!!!!!")
            """Route incoming messages based on type."""
            msg_type = xmpp_message.get_metadata("type")  # Get the message type
            data = float(xmpp_message.body)  # The message body should contain a float (e.g., dissatisfaction value)
            
            if msg_type == "battery_charge":
                self.update_battery_charge(data)  # Call method to update battery charge
            elif msg_type == "priority":
                self.update_priority(xmpp_message.sender, data)  # Update priority based on sender and dissatisfaction value
            elif msg_type == "confirmation":
                self.handle_confirmation(xmpp_message.sender, data)  # Handle confirmation
                self.agent.agents_ready = 1  # Set confirmation flag

        def handle_confirmation(self, sender: str, energy_used: float):
            """Handle confirmation of energy usage and update solar energy."""
            print(f"[SystemState] Received confirmation from {sender} for {energy_used} kWh energy used.")
            
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