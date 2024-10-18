from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import pandas as pd
import asyncio

class SolarPanelAgent(Agent):
    def __init__(self, jid, password, solar_battery):
        super().__init__(jid, password)
        self.solar_battery = solar_battery  # SolarBattery associada a este agente
        self.energy_data = pd.read_csv("energy_dataset.csv", parse_dates=['time'])  # Lê o CSV e parseia as datas
        self.current_index = 0  # Índice para controlar a linha atual

    class SolarBehaviour(CyclicBehaviour):
        async def run(self):
            # Acessa o agente externo (SolarPanelAgent) para obter os dados de geração solar
            solar_energy = self.agent.get_solar_generation()
            print(f"[Painel Solar] Gerando {solar_energy} kWh de energia")

            # Carregar a SolarBattery com a energia gerada
            self.agent.solar_battery.charge(solar_energy)

            # Espera 10 segundos até gerar nova energia
            await asyncio.sleep(10)

    async def setup(self):
        print(f"[Painel Solar] Agente Solar inicializado.")
        self.add_behaviour(self.SolarBehaviour())

    def get_solar_generation(self):
        """Retorna a geração solar da linha atual do DataFrame."""
        if self.current_index < len(self.energy_data):
            solar_generation = self.energy_data.iloc[self.current_index]['generation solar']
            self.current_index += 1  # Avança para a próxima linha
            return solar_generation
        else:
            print("[Painel Solar] Todos os dados foram processados.")
            return 0  # Se não houver mais dados, retorna 0
