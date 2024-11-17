from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import pandas as pd
import asyncio

class SolarBattery(Agent):  # Nome original restaurado
    def __init__(self, jid, password, capacity_kwh, charge_efficiency=0.9, discharge_efficiency=0.9):
        super().__init__(jid, password)
        self.capacity_kwh = capacity_kwh
        self.current_charge_kwh = 0
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency

    class BatteryBehaviour(CyclicBehaviour):
        async def run(self):
            state_of_charge = self.agent.get_state_of_charge()
            print(f"[SolarBattery] Current charge: {state_of_charge} kWh.")
            
            msg = Message(to="system@localhost")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("type", "battery_charge")
            msg.body = str(self.agent.get_state_of_charge()) #mudei para n haver erros desatualizados
            
            await self.send(msg)
            print("[SolarBattery] Sent state of charge to system.")
            
            await asyncio.sleep(1)

    async def setup(self):
        print(f"[SolarBattery] Battery Agent initialized.")
        behaviour = self.BatteryBehaviour()
        self.add_behaviour(behaviour)
        print(f"[SolarBattery] BatteryBehaviour added.")

    def charge(self, solar_energy_kwh):
        if solar_energy_kwh <= 0:
            return 0
        energy_to_store = solar_energy_kwh * self.charge_efficiency
        available_space = self.capacity_kwh - self.current_charge_kwh
        energy_stored = min(energy_to_store, available_space)
        self.current_charge_kwh += energy_stored
        return energy_stored

    def discharge(self, energy_needed_kwh):
        if energy_needed_kwh <= 0:
            return 0
        available_energy = self.current_charge_kwh * self.discharge_efficiency
        energy_provided = min(energy_needed_kwh, available_energy)
        self.current_charge_kwh -= energy_provided / self.discharge_efficiency
        return energy_provided

    def get_state_of_charge(self):
        return self.current_charge_kwh
