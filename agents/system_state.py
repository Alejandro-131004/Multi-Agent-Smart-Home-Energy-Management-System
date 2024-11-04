from dataclasses import dataclass, field
from queue import PriorityQueue
import asyncio
from typing import Dict, Optional
from spade.message import Message

@dataclass
class SystemState:
    energy_price: float = 0.0                       # Current energy price
    battery_charge: float = 0.0                     # Current battery charge in kWh
    solar_energy: float = 0.0                       # Solar energy produced in kWh
    priority_queue: PriorityQueue = field(default_factory=PriorityQueue)  # (priority, agent_id) tuples
    current_agent: Optional[str] = None             # Track the currently executing agent
    agent_priorities: Dict[str, float] = field(default_factory=dict)      # Stores dynamic priorities for each agent
    agents_ready: int = 0                           # Counter for how many agents have sent their data

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

    async def next_in_queue(self):
        """Set the next agent in the queue as the current agent."""
        if not self.priority_queue.empty():
            _, agent_id = self.priority_queue.get()
            self.current_agent = agent_id
            print(f"[SystemState] Agent {agent_id} is now the active agent.")
            return agent_id
        return None

    async def process_messages(self):
        """
        Continuously process the priority queue and notify the next agent to execute.
        Resets `current_agent` to None once an agent completes its task.
        """
        while True:
            if self.agents_ready == len(self.agent_priorities):
                # All agents have sent their messages, process the queue
                self.agents_ready = 0  # Reset for the next cycle
                await self.execute_agents()  # Process the agents in the queue
            await asyncio.sleep(1)  # Adjust frequency as needed

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
                # Construct the message to the agent
                msg = Message(to=f"{agent_id}@localhost")  # Adjust domain if necessary
                msg.set_metadata("performative", "inform")
                msg.set_metadata("type", "priority_notification")
                msg.body = f"Priority level: {self.agent_priorities[agent_id]}"

                # Send the message
                await self.send(msg)
                print(f"[SystemState] Sent notification message to {agent_id}.")

                # Simulate waiting for the agent to respond, if needed
                await asyncio.sleep(2)  # Simulate interaction time or remove for actual responses

                # Reset the current agent after task completion
                self.current_agent = None

            except Exception as e:
                print(f"[SystemState] Error notifying {agent_id}: {e}")
        else:
            print(f"[SystemState] Warning: Agent {agent_id} not found in priorities.")
    async def handle_price_request(self, agent_id: str):
        """Handle a request from an agent for the current energy price."""
        print(f"[SystemState] Received energy price request from {agent_id}.")
        msg = Message(to=f"{agent_id}@localhost")
        msg.set_metadata("performative", "inform")
        msg.set_metadata("type", "energy_price_response")
        msg.body = str(self.energy_price)
        
        await self.send(msg)
        print(f"[SystemState] Sent energy price {self.energy_price} to {agent_id}.")

    def receive_message(self, sender: str, msg_type: str, data: float):
        """
        Handle incoming messages with updates on energy price, solar energy, battery status, or priority.
        """
        if msg_type == "energy_price":
            self.update_energy_price(data)
        elif msg_type == "solar_energy":
            self.update_solar_energy(data)
        elif msg_type == "battery_charge":
            self.update_battery_charge(data)
        elif msg_type == "priority":
            self.update_priority(sender, data)
        elif msg_type == "confirmation":
            print(f"[SystemState] Received confirmation from {sender} for {data} kWh energy used.")
            self.update_solar_energy(-data)  # Deduct energy used only in this method
            self.agents_ready += 1  # Increment agent processed count

        print(f"[SystemState] Received '{msg_type}' message from {sender} with data: {data}")
