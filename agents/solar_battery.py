class SolarBattery:
    def __init__(self, capacity_kwh, charge_efficiency=0.9, discharge_efficiency=0.9):
        self.capacity_kwh = capacity_kwh
        self.current_charge_kwh = 0  # Inicialmente a bateria está vazia
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency

    def charge(self, solar_energy_kwh):
        # Verificar se há energia suficiente para carregar
        if solar_energy_kwh <= 0:
            print("[SolarBattery] Energia solar inválida para carregar. Nenhuma ação realizada.")
            return 0

        print(f"[SolarBattery] Tentando carregar com {solar_energy_kwh:.2f} kWh de energia solar.")
        energy_to_store = solar_energy_kwh * self.charge_efficiency
        available_space = self.capacity_kwh - self.current_charge_kwh

        print(f"[SolarBattery] Energia a armazenar: {energy_to_store:.2f} kWh")
        print(f"[SolarBattery] Espaço disponível: {available_space:.2f} kWh")

        # Verifica o quanto de energia pode ser realmente armazenado sem ultrapassar a capacidade
        energy_stored = min(energy_to_store, available_space)
        self.current_charge_kwh += energy_stored
        print(f"[SolarBattery] Armazenou {energy_stored:.2f} kWh de energia solar. Energia atual armazenada: {self.current_charge_kwh:.2f} kWh.")
        return energy_stored

    def discharge(self, energy_needed_kwh):
        # Verificar se a energia solicitada é válida
        if energy_needed_kwh <= 0:
            print("[SolarBattery] Valor de energia solicitado inválido. Nenhuma ação realizada.")
            return 0

        print(f"[SolarBattery] Verificando se há energia solar disponível...")
        
        # Verifica se há carga suficiente na bateria
        if self.current_charge_kwh > 0:
            available_energy = self.current_charge_kwh * self.discharge_efficiency
            print(f"[SolarBattery] Há {available_energy:.2f} kWh de energia solar disponível.")
        else:
            print("[SolarBattery] Não há energia solar disponível.")
            return 0  # Se não há energia, retorna 0 imediatamente

        # Fornece a quantidade de energia necessária ou o máximo disponível
        energy_provided = min(energy_needed_kwh, available_energy)
        self.current_charge_kwh -= energy_provided / self.discharge_efficiency
        print(f"[SolarBattery] Forneceu {energy_provided:.2f} kWh de energia solar. Energia restante: {self.current_charge_kwh:.2f} kWh.")
        return energy_provided

    def get_state_of_charge(self):
        print(f"[SolarBattery] Estado atual da carga: {self.current_charge_kwh:.2f} kWh.")
        return self.current_charge_kwh
