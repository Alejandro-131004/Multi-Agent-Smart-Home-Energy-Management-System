
class SolarBattery:
    def __init__(self, capacity_kwh, charge_efficiency=0.9, discharge_efficiency=0.9):
        self.capacity_kwh = capacity_kwh
        self.current_charge_kwh = 0
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency

    def charge(self, solar_energy_kwh):
        energy_to_store = solar_energy_kwh * self.charge_efficiency
        available_space = self.capacity_kwh - self.current_charge_kwh
        energy_stored = min(energy_to_store, available_space)
        self.current_charge_kwh += energy_stored
        return energy_stored

    def discharge(self, energy_needed_kwh):
        available_energy = self.current_charge_kwh * self.discharge_efficiency
        energy_provided = min(energy_needed_kwh, available_energy)
        self.current_charge_kwh -= energy_provided / self.discharge_efficiency
        return energy_provided

    def get_state_of_charge(self):
        return self.current_charge_kwh