from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio

class HeaterAgent(Agent):
    def __init__(self, jid, password, environment, energy_agent):
        super().__init__(jid, password)
        self.environment = environment  # Refere-se ao Environment
        self.energy_agent = energy_agent  # EnergyAgent para consultar sobre energia
        self.heating_power_per_degree = 1000  # Exemplo: 1000 LWatts por grau de aquecimento
        self.weight_dissatisfaction = 0.8  # Peso alto devido à importância do aquecimento

    class HeaterBehaviour(CyclicBehaviour):
        def __init__(self, environment, energy_agent, heating_power_per_degree, weight_dissatisfaction):
            super().__init__()
            self.environment = environment
            self.energy_agent = energy_agent
            self.heating_power_per_degree = heating_power_per_degree
            self.weight_dissatisfaction = weight_dissatisfaction

        async def run(self):
            # Obtenção da temperatura interior atual
            current_room_temp = self.environment.get_indoor_temperature()
            desired_temp_range = (self.environment.desired_temperature - 1, 
                                  self.environment.desired_temperature + 1)

            # Calcular grau de insatisfação ponderada
            if current_room_temp < desired_temp_range[0]:
                dissatisfaction = (desired_temp_range[0] - current_room_temp) * self.weight_dissatisfaction
            elif current_room_temp > desired_temp_range[1]:
                dissatisfaction = (current_room_temp - desired_temp_range[1]) * self.weight_dissatisfaction
            else:
                dissatisfaction = 0  # Dentro da faixa, sem insatisfação

            print(f"[Aquecedor] Grau de insatisfação ponderada: {dissatisfaction}°C.")

            if dissatisfaction > 0:
                # Função que calcula o gasto energético necessário (LWatts) por grau de insatisfação
                energy_needed = self.calculate_energy_consumption(dissatisfaction)

                # Solicita ao EnergyAgent a potência necessária
                energy_power = await self.energy_agent.decide_power(energy_needed)

                print(f"[Aquecedor] Potência recomendada pelo EnergyAgent: {energy_power} LWatts.")

                if energy_power > 0:
                    # Calcula quantos graus podem ser aquecidos com a energia disponível
                    degrees_heated = energy_power / self.heating_power_per_degree

                    # Atualiza a temperatura interna com base na energia recebida
                    self.environment.update_room_temperature(degrees_heated)
                    print(f"[Aquecedor] A temperatura da sala foi aumentada em {degrees_heated}°C.")
                else:
                    print(f"[Aquecedor] Sem energia disponível para aquecimento.")

            # Simula uma hora de operação
            await asyncio.sleep(3600)

        def calculate_energy_consumption(self, dissatisfaction):
            """
            Calcula o gasto de energia (LWatts) por hora para compensar o grau de insatisfação.
            """
            return dissatisfaction * self.heating_power_per_degree  # Exemplo: 1000 LWatts por grau de insatisfação

    async def setup(self):
        print(f"[Aquecedor] Agente Aquecedor inicializado.")
        self.add_behaviour(self.HeaterBehaviour(self.environment, self.energy_agent, self.heating_power_per_degree, self.weight_dissatisfaction))

