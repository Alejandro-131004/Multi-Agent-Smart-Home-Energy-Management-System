import asyncio

import pandas as pd

class EnergyAgent():
    def __init__(self, name, password, environment):
        self.name = name
        self.password = password
        self.environment = environment  # O ambiente é um atributo da classe
        self.current_price = 3000  # Preço atual da energia da rede
        self.energy_consumption_needed = 0.0  # Energia que os outros agentes vão precisar (em kWh)
        self.threshold_price = 0.20# Preço limiar para o uso da energia da rede
        self.solar_energy = 0
        
        try:
            self.energy_data = pd.read_csv("energy_dataset.csv", parse_dates=['time'])
            if 'generation solar' not in self.energy_data.columns:
                raise ValueError("[Erro] Coluna 'generation solar' não encontrada no CSV.")
            print("[SolarPanelAgent] CSV carregado com sucesso. Dados de geração solar disponíveis.")
        except FileNotFoundError:
            print("[Erro] Arquivo 'energy_dataset.csv' não encontrado.")
            self.energy_data = None
        except pd.errors.EmptyDataError:
            print("[Erro] Arquivo CSV está vazio ou inválido.")
            self.energy_data = None
        except Exception as e:
            print(f"[Erro] Problema ao ler o CSV: {e}")
            self.energy_data = None
            
        self.current_index = 0

    async def decide_power(self, energy_needed, priority):
        """
        Decide a quantidade de energia a ser alocada para o aquecedor com base na
        disponibilidade de energia solar, preço da rede e prioridade do agente.
        """
        solar_energy_available = self.update_solar()
        print(f"{self.name}: Energia solar disponível: {solar_energy_available} kWh.")
        if solar_energy_available is not None:
            print(f"[Painel Solar] Gerando {solar_energy_available} kWh de energia")
            # Carregar a SolarBattery com a energia gerada, se válida
            if solar_energy_available > 0:
                self.environment.solar_battery.charge(solar_energy_available)
            else:
                print("[Painel Solar] Sem energia solar para carregar.")
        else:
            print("[Painel Solar] Não foi possível gerar energia solar.")
        # Ajusta a quantidade de energia alocada com base na prioridade
        print(energy_needed)
        adjusted_energy_needed = energy_needed #* priority

        # Se houver energia solar suficiente, aloca energia solar
        if solar_energy_available > 0:
            energy_to_use = min(solar_energy_available, adjusted_energy_needed)
            print(f"{self.name}: Vai usar {energy_to_use} kWh de energia solar.")
            self.environment.solar_battery.discharge(energy_to_use)
            return energy_to_use  # Convertendo para LWatts
        else:
            print(f"{self.name}: Não há energia solar disponível.")
        self.update_price()
        # Verifica o preço da rede e ajusta o fornecimento
        if self.current_price is not None and self.current_price <= self.threshold_price:
            print(f"{self.name}: Preço da rede aceitável ({self.current_price} €/kWh).")
            return adjusted_energy_needed * 1000  # Aloca energia da rede
        else:
            print(f"{self.name}: Preço da rede alto ({self.current_price} €/kWh), fornecimento reduzido.")
            return 0  # Não aloca energia da rede

    def update_price(self):
        """Atualiza o preço da energia da rede a partir do environment."""
        self.current_price = self.environment.get_price_for_current_hour()
        print(f"{self.name}: Atualizou o preço da energia para {self.current_price} €/kWh.")
    
    def update_solar(self):
        if self.current_index < len(self.energy_data):
            solar_generation = self.energy_data.iloc[self.current_index]['generation solar']
            print(f"[SolarPanelAgent] Linha {self.current_index}, Geração Solar: {solar_generation} kWh.")
            self.current_index += 1  # Avança para a próxima linha
            return solar_generation
        else:
            print("[Painel Solar] Todos os dados foram processados.")
            return 0  # Se não houver mais dados, retorna 0

