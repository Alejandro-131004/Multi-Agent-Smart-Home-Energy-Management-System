import pandas as pd
import asyncio
from queue import PriorityQueue
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from typing import Dict, Optional

class SystemState(Agent):
    def __init__(self, jid, password):
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
                self.agent.state = 1
            elif self.agent.state == 1 and self.agent.solar_confirm == 1 and self.agent.energy_confirm == 1:
                await self.agent.process_messages()
                self.agent.state = 0
                self.agent.solar_confirm = 0
                self.agent.energy_confirm = 0
            
            await asyncio.sleep(.1)

        async def request_energy_price(self):
            energy_agent_id = "energy_agent@local"
            msg = Message(to=energy_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "energy_price_request")
            
            await self.send(msg)
            print("[SystemState] Sent energy price request to energy agent.")

        async def request_solar_production(self):
            solar_agent_id = "solar_agent@localhost"
            msg = Message(to=solar_agent_id)
            msg.set_metadata("performative", "request")
            msg.set_metadata("type", "solar_production_request")
            
            await self.send(msg)
            print("[SystemState] Sent solar production request to solar agent.")

        async def process_messages(self):
            print("[SystemState] Collecting priority messages...")
            
            # Collect all incoming messages
            while True:
                try:
                    msg = await self.receive(timeout=1)
                    if msg:
                        self.receive_message(msg)
                except asyncio.TimeoutError:
                    print("[SystemState] No more messages received within timeout. Processing queue...")
                    break

            # Process agents in the priority queue with confirmation check
            while not self.priority_queue.empty():
                _, agent_id = self.priority_queue.get()
                await self.notify_agent(agent_id)

                # Wait for confirmation from the agent
                print(f"[SystemState] Waiting for confirmation from {agent_id}...")
                while self.agents_ready == 0:
                    try:
                        msg = await self.receive(timeout=1)
                        if msg:
                            self.receive_message(msg)
                    except asyncio.TimeoutError:
                        continue

                # Reset confirmation flag for next agent
                self.agents_ready = 0

        async def notify_agent(self, agent_id: str):
            if agent_id in self.agent_priorities:
                print(f"[SystemState] Notifying {agent_id} to execute with available solar energy.")
                msg = Message(to=f"{agent_id}@localhost")
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "priority_notification")
                msg.body = f"Available solar energy: {self.solar_energy}, Priority level: {self.agent_priorities[agent_id]}"
                
                await self.send(msg)
                print(f"[SystemState] Sent notification message to {agent_id}.")
                

        def receive_message(self, xmpp_message: Message):
            """Route incoming messages based on type."""
            msg_type = xmpp_message.get_metadata("type")
            data = float(xmpp_message.body)

            if msg_type == "energy_price":
                self.update_energy_price(data)
                self.energy_confirm = 1
            elif msg_type == "solar_energy":
                self.update_solar_energy(data)
                self.solar_confirm = 1
            elif msg_type == "battery_charge":
                self.update_battery_charge(data)
            elif msg_type == "priority":
                self.update_priority(xmpp_message.sender, data)
            elif msg_type == "confirmation":
                self.handle_confirmation(xmpp_message.sender, data)
                self.agents_ready = 1  # Set confirmation flag

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
            self.agent_priorities[agent_id] = priority
            self.priority_queue.put((-priority, agent_id))
            print(f"[SystemState] Priority for agent {agent_id} set to {priority}.")