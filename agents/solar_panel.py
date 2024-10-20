from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import pandas as pd
import asyncio

class SolarPanelAgent(Agent):
    def __init__(self, jid, password, solar_battery):
        super().__init__(jid, password)
        self.solar_battery = solar_battery  # SolarBattery associada a este agente
        
        # Tenta ler o CSV e verifica se a coluna 'generation solar' existe
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
        
        self.current_index = 0  # Índice para controlar a linha atual

    class SolarBehaviour(CyclicBehaviour):
        async def run(self):
            print("[SolarBehaviour] Iniciando comportamento cíclico...")  # Depuração

            if self.agent.energy_data is None:
                print("[SolarPanelAgent] Sem dados de geração solar disponíveis. Comportamento suspenso.")
                return  # Sai se os dados não foram carregados corretamente

            # Acessa o agente externo (SolarPanelAgent) para obter os dados de geração solar
            solar_energy = self.agent.get_solar_generation()
            if solar_energy is not None:
                print(f"[Painel Solar] Gerando {solar_energy} kWh de energia")
                # Carregar a SolarBattery com a energia gerada, se válida
                if solar_energy > 0:
                    self.agent.solar_battery.charge(solar_energy)
                else:
                    print("[Painel Solar] Sem energia solar para carregar.")
            else:
                print("[Painel Solar] Não foi possível gerar energia solar.")

            # Espera 10 segundos até gerar nova energia
            await asyncio.sleep(10)

    async def setup(self):
        print(f"[Painel Solar] Agente Solar inicializado.")
        behaviour = self.SolarBehaviour()
        self.add_behaviour(behaviour)  # Adiciona o comportamento cíclico
        print(f"[SolarPanelAgent] Comportamento SolarBehaviour adicionado.")

    def get_solar_generation(self):
        """Retorna a geração solar da linha atual do DataFrame."""
        if self.energy_data is None:
            print("[SolarPanelAgent] Dados de energia solar não carregados.")
            return None

        if self.current_index < len(self.energy_data):
            solar_generation = self.energy_data.iloc[self.current_index]['generation solar']
            print(f"[SolarPanelAgent] Linha {self.current_index}, Geração Solar: {solar_generation} kWh.")
            self.current_index += 1  # Avança para a próxima linha
            return solar_generation
        else:
            print("[Painel Solar] Todos os dados foram processados.")
            return 0  # Se não houver mais dados, retorna 0
