import asyncio

class EnergyAgent:
    def __init__(self, name, password, environment):
        self.name = name
        self.password = password
        self.environment = environment  # O ambiente é um atributo da classe
        self.current_price = None  # Preço atual da energia da rede
        self.energy_consumption_needed = 0.0  # Energia que os outros agentes vão precisar (em kWh)
        self.threshold_price = 0.20  # Preço limiar para o uso da energia da rede

    async def decide_power(self, energy_needed, priority):
        """
        Decide a quantidade de energia a ser alocada para o aquecedor com base na
        disponibilidade de energia solar, preço da rede e prioridade do agente.
        """
        solar_energy_available = self.environment.solar_battery.get_state_of_charge()
        print(f"{self.name}: Energia solar disponível: {solar_energy_available} kWh.")

        # Ajusta a quantidade de energia alocada com base na prioridade
        adjusted_energy_needed = energy_needed * priority

        # Se houver energia solar suficiente, aloca energia solar
        if solar_energy_available > 0:
            energy_to_use = min(solar_energy_available, adjusted_energy_needed)
            print(f"{self.name}: Vai usar {energy_to_use} kWh de energia solar.")
            self.environment.solar_battery.discharge(energy_to_use)
            return energy_to_use * 1000  # Convertendo para LWatts
        else:
            print(f"{self.name}: Não há energia solar disponível.")

        # Verifica o preço da rede e ajusta o fornecimento
        if self.current_price is not None and self.current_price <= self.threshold_price:
            print(f"{self.name}: Preço da rede aceitável ({self.current_price} €/kWh).")
            return adjusted_energy_needed * 1000  # Aloca energia da rede
        else:
            print(f"{self.name}: Preço da rede alto ({self.current_price} €/kWh), fornecimento reduzido.")
            return 0  # Não aloca energia da rede

    def update_price(self):
        """Atualiza o preço da energia da rede a partir do environment."""
        self.current_price = self.environment.get_energy_prices()
        print(f"{self.name}: Atualizou o preço da energia para {self.current_price} €/kWh.")
