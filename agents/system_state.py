from dataclasses import dataclass, field
from queue import PriorityQueue
import asyncio
from typing import Dict, Optional
from spade import Agent
from spade.message import Message

@dataclass
class SystemState(Agent):
    energy_price: float = 0.0
    battery_charge: float = 0.0
    solar_energy: float = 0.0
    priority_queue: PriorityQueue = field(default_factory=PriorityQueue)
    current_agent: Optional[str] = None
    agent_priorities: Dict[str, float] = field(default_factory=dict)
    agents_ready: int = 0
    state: int = 0
    energy_confirm: int = 0
    solar_confirm: int = 0

    async def setup(self):
        print("[SystemState] Agent is running.")
        # Start the state management cycle
        self.cycle_task = self.loop.create_task(self.cycle_states())

    async def cycle_states(self):
        """Continuously manage states for requesting data and processing messages."""
        while True:
            if self.state == 0:
                await self.request_energy_price_and_solar_production()
                self.state = 1  # Switch to state 1 after requesting data
            elif self.state == 1 and self.solar_confirm == 1 and self.energy_confirm == 1:
                await self.process_messages()  # Process the received messages
                self.state = 0  # Reset to state 0 after processing
                self.solar_confirm = 0  # Reset solar confirmation
                self.energy_confirm = 0  # Reset energy confirmation
            
            await asyncio.sleep(1)  # Adjust cycle frequency as needed

    async def request_energy_price_and_solar_production(self):
        """Request the current energy price and solar production data from respective agents."""
        await self.request_energy_price()
        await self.request_solar_production()
        print("[SystemState] Requested updates for energy price and solar production.")

    async def request_energy_price(self):
        """Send request for energy price update to the energy agent."""
        energy_agent_id = "energy_agent@localhost"
        msg = Message(to=energy_agent_id)
        msg.set_metadata("performative", "request")
        msg.set_metadata("type", "energy_price_request")
        
        await self.send(msg)
        print("[SystemState] Sent energy price request to energy agent.")

    async def request_solar_production(self):
        """Send request for solar energy production update to the solar agent."""
        solar_agent_id = "solar_agent@localhost"
        msg = Message(to=solar_agent_id)
        msg.set_metadata("performative", "request")
        msg.set_metadata("type", "solar_production_request")
        
        await self.send(msg)
        print("[SystemState] Sent solar production request to solar agent.")

    async def process_messages(self):
        """Process the priority queue and notify the next agent to execute if all messages have been received."""
        if self.agents_ready == len(self.agent_priorities):
            self.agents_ready = 0  # Reset for the next cycle
            await self.execute_agents()  # Process the agents in the queue

    async def execute_agents(self):
        """Execute agents in order of priority."""
        while not self.priority_queue.empty():
            agent_id = await self.next_in_queue()  # Get the next agent
            await self.notify_agent(agent_id)  # Notify agent to execute their task

    async def notify_agent(self, agent_id: str):
        """Notify the specified agent that it is their turn to execute and wait for a response."""
        if agent_id in self.agent_priorities:
            print(f"[SystemState] Notifying {agent_id} to execute.")
            
            try:
                msg = Message(to=f"{agent_id}@localhost")
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "priority_notification")
                msg.body = f"Priority level: {self.agent_priorities[agent_id]}"
                await self.send(msg)
                print(f"[SystemState] Sent notification message to {agent_id}.")
                await asyncio.sleep(2)  # Simulate interaction time or remove for actual responses
                self.current_agent = None

            except Exception as e:
                print(f"[SystemState] Error notifying {agent_id}: {e}")
        else:
            print(f"[SystemState] Warning: Agent {agent_id} not found in priorities.")

    async def handle_price_request(self, sender: str):
        """Handle a request from an agent for the current energy price."""
        print(f"[SystemState] Received energy price request from {sender}.")
        msg = Message(to=sender)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("type", "energy_price_response")
        msg.body = str(self.energy_price)
        
        await self.send(msg)
        print(f"[SystemState] Sent energy price {self.energy_price} to {sender}.")

    def receive_message(self, xmpp_message: Message):
        """
        Handle incoming XMPP messages with updates on energy price, solar energy, battery status, or priority.
        """
        msg_type = xmpp_message.get_metadata("type")
        data = float(xmpp_message.body)  # Convert message body to float

        if msg_type == "energy_price":
            self.update_energy_price(data)
            self.energy_confirm = 1  # Set confirmation flag for energy price
        elif msg_type == "solar_energy":
            self.update_solar_energy(data)
            self.solar_confirm = 1  # Set confirmation flag for solar energy
        elif msg_type == "battery_charge":
            self.update_battery_charge(data)
        elif msg_type == "priority":
            self.update_priority(xmpp_message.sender, data)
        elif msg_type == "confirmation":
            print(f"[SystemState] Received confirmation from {xmpp_message.sender} for {data} kWh energy used.")
            self.update_solar_energy(-data)  # Deduct energy used only in this method
            self.agents_ready += 1  # Increment agent processed count

        print(f"[SystemState] Received '{msg_type}' message from {xmpp_message.sender} with data: {data}")

    def update_energy_price(self, new_price: float):
        """Update the current energy price and notify agents if necessary."""
        self.energy_price = new_price
        print(f"[SystemState] Energy price updated to {self.energy_price} €/kWh.")

    def update_battery_charge(self, amount: float):
        """Update the battery charge by a specified amount."""
        self.battery_charge += amount
        self.battery_charge = max(0.0, self.battery_charge)  # Ensure non-negative charge
        print(f"[SystemState] Battery charge updated to {self.battery_charge} kWh.")

    def update_solar_energy(self, amount: float):
        """Set or adjust the solar energy produced for the current cycle."""
        self.solar_energy = amount
        print(f"[SystemState] Solar energy updated to {self.solar_energy} kWh.")

    def update_priority(self, agent_id: str, priority: float):
        """Update an agent's priority in the queue."""
        self.agent_priorities[agent_id] = priority
        self.priority_queue.put((-priority, agent_id))  # Negative for highest-priority first
        self.agents_ready += 1  # Increment agents ready count
        print(f"[SystemState] Priority for agent {agent_id} set to {priority}.")
