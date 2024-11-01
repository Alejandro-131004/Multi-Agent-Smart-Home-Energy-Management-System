from dataclasses import dataclass, field
from queue import PriorityQueue
import asyncio
from typing import Dict, Optional

@dataclass
class SystemState:
    energy_price: float = 0.0                       # Current energy price
    battery_charge: float = 0.0                     # Current battery charge in kWh
    solar_energy: float = 0.0                       # Solar energy produced in kWh
    priority_queue: PriorityQueue = field(default_factory=PriorityQueue)  # (priority, agent_id) tuples
    current_agent: Optional[str] = None             # Track the currently executing agent
    agent_priorities: Dict[str, float] = field(default_factory=dict)      # Stores dynamic priorities for each agent

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
        """Set the solar energy produced for the current cycle."""
        self.solar_energy = amount
        print(f"[SystemState] Solar energy updated to {self.solar_energy} kWh.")

    def update_priority(self, agent_id: str, priority: float):
        """
        Update an agent's priority in the queue.
        Higher priority values mean the agent will execute sooner.
        """
        self.agent_priorities[agent_id] = priority
        self.priority_queue.put((-priority, agent_id))  # Negative for highest-priority first
        print(f"[SystemState] Priority for agent {agent_id} set to {priority}.")

    async def next_in_queue(self):
        """Set the next agent in the queue as the current agent."""
        if not self.priority_queue.empty():
            _, agent_id = self.priority_queue.get()
            self.current_agent = agent_id
            print(f"[SystemState] Agent {agent_id} is now the active agent.")
            return agent_id
        return None

    async def wait_for_turn(self, agent_id: str):
        """Method for agents to wait until it's their turn to execute."""
        while self.current_agent != agent_id:
            await asyncio.sleep(1)  # Wait before checking again

    async def process_messages(self):
        """
        Continuously process the priority queue and notify the next agent to execute.
        Resets `current_agent` to None once an agent completes its task.
        """
        while True:
            if self.current_agent is None:
                await self.next_in_queue()  # Fetch the next agent in the queue if available
            await asyncio.sleep(1)  # Adjust frequency as needed

    def receive_message(self, sender: str, msg_type: str, data: float):
        """
        Handle incoming messages with updates on energy price, solar energy, battery status, or priority.
        This centralizes message management.
        """
        if msg_type == "energy_price":
            self.update_energy_price(data)
        elif msg_type == "solar_energy":
            self.update_solar_energy(data)
        elif msg_type == "battery_charge":
            self.update_battery_charge(data)
        elif msg_type == "priority":
            self.update_priority(sender, data)
        print(f"[SystemState] Received '{msg_type}' message from {sender} with data: {data}")
