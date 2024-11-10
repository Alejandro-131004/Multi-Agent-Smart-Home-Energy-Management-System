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
        self.cycle_task = self.loop.create_task(self.cycle_states())

    async def cycle_states(self):
        while True:
            if self.state == 0:
                await self.request_energy_price_and_solar_production()
                self.state = 1
            elif self.state == 1 and self.solar_confirm == 1 and self.energy_confirm == 1:
                await self.process_messages()
                self.state = 0
                self.solar_confirm = 0
                self.energy_confirm = 0
            
            await asyncio.sleep(1)

    async def request_energy_price_and_solar_production(self):
        await self.request_energy_price()
        await self.request_solar_production()
        print("[SystemState] Requested updates for energy price and solar production.")

    async def request_energy_price(self):
        energy_agent_id = "energy_agent@localhost"
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
        while not self.priority_queue.empty():
            agent_id = await self.next_in_queue()
            await self.notify_agent(agent_id)

    async def notify_agent(self, agent_id: str):
        if agent_id in self.agent_priorities:
            print(f"[SystemState] Notifying {agent_id} to execute.")
            msg = Message(to=f"{agent_id}@localhost")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "priority_notification")
            msg.body = f"Priority level: {self.agent_priorities[agent_id]}"
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
        elif msg_type == "energy_price_request":
            asyncio.create_task(self.handle_price_request(xmpp_message.sender))
        elif msg_type == "solar_production_request":
            asyncio.create_task(self.handle_solar_request(xmpp_message.sender))

        print(f"[SystemState] Received '{msg_type}' message from {xmpp_message.sender} with data: {data}")

    async def handle_price_request(self, sender: str):
        """Handle a request for the current energy price."""
        print(f"[SystemState] Received energy price request from {sender}.")
        msg = Message(to=sender)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("type", "energy_price_response")
        msg.body = str(self.energy_price)
        
        await self.send(msg)
        print(f"[SystemState] Sent energy price {self.energy_price} to {sender}.")

    async def handle_solar_request(self, sender: str):
        """Handle a request for the current solar energy production."""
        print(f"[SystemState] Received solar production request from {sender}.")
        msg = Message(to=sender)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("type", "solar_energy_response")
        msg.body = str(self.solar_energy)

        await self.send(msg)
        print(f"[SystemState] Sent solar energy {self.solar_energy} to {sender}.")

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
        self.agents_ready += 1
        print(f"[SystemState] Priority for agent {agent_id} set to {priority}.")

    def handle_confirmation(self, sender: str, data: float):
        print(f"[SystemState] Received confirmation from {sender} for {data} kWh energy used.")
        self.update_solar_energy(-data)  # Deduct energy used
        self.agents_ready += 1  # Increment agents processed count
