from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
from agents.system_state import SystemState

class HeaterAgent(Agent):
    def __init__(self, jid, password, environment, energy_agent, system_state):
        super().__init__(jid, password)
        self.system_state = system_state
        self.environment = environment  # Refere-se ao Environment
        self.energy_agent = energy_agent  # EnergyAgent para consultar sobre energia
        self.heating_power_per_degree = 1.0  # Exemplo: 1000 LWatts por grau de aquecimento
        self.base_priority = 1.0 # Prioridade base do aquecedor
        

    class HeaterBehaviour(CyclicBehaviour):
        def __init__(self, environment, energy_agent, heating_power_per_degree, base_priority,system_state):
            super().__init__()
            self.environment = environment
            self.system_state = system_state
            self.energy_agent = energy_agent
            self.heating_power_per_degree = heating_power_per_degree
            self.base_priority = base_priority

        async def run(self):
            # Obtenção da temperatura interior atual
            current_room_temp = self.environment.get_indoor_temperature()
            desired_temp_range = (self.environment.desired_temperature - 1, 
                                  self.environment.desired_temperature + 1)

            # Calcular grau de insatisfação
            if current_room_temp < desired_temp_range[0]:
                dissatisfaction = (desired_temp_range[0] - current_room_temp)
            elif current_room_temp > desired_temp_range[1]:
                dissatisfaction = (desired_temp_range[1] - current_room_temp)
            else:
                dissatisfaction = 0  # Dentro da faixa, sem insatisfação

            # Calcular prioridade baseada na insatisfação e base_priority
            dynamic_priority = self.calculate_priority(dissatisfaction)

            print(f"[Aquecedor] Grau de insatisfação: {dissatisfaction}°C. Prioridade dinâmica: {dynamic_priority}.")
            
            if dissatisfaction > 0:
                # Solicita ao EnergyAgent a energia necessária, baseado na prioridade dinâmica
                energy_needed = self.calculate_energy_consumption(dissatisfaction)
                print("neeeeeeeeeeeeeeeeeeeeeeeed",energy_needed)
                solar_energy_available = self.agent.system_state.solar_energy_produced
                
                if solar_energy_available > 0:
                    energy_power = min(solar_energy_available, energy_needed)
                    print(f" Vai usar {energy_power} kWh de energia solar.")
                else:
                    print(f" Não há energia solar disponível.")
                    energy_power = 0
                self.update_price()

                print(f"[Aquecedor] Potência recomendada pelo EnergyAgent: {energy_power} LWatts.")

                if energy_power > 0:
                    degrees_heated = energy_power / self.heating_power_per_degree
                    self.environment.update_room_temperature(degrees_heated)
                    print(f"[Aquecedor] A temperatura da sala foi aumentada em {degrees_heated}°C.")
                else:
                    print(f"[Aquecedor] Sem energia disponível para aquecimento.")
            else :
                    print(f"Temperatura confortavel.")
                    self.environment.decrease_temperature();        

            await asyncio.sleep(10)

        def calculate_priority(self, dissatisfaction):
            """
            Calcula a prioridade dinâmica baseada na insatisfação e na prioridade base.
            """
            return self.base_priority + dissatisfaction  # Exemplo simples de cálculo de prioridade

        def calculate_energy_consumption(self, dissatisfaction):
            """
            Calcula o gasto de energia (Watts) por hora para compensar o grau de insatisfação.
            """
            print("disati",dissatisfaction)
            return dissatisfaction   # Exemplo: 1000 LWatts por grau de insatisfação

    async def setup(self):
        print(f"[Aquecedor] Agente Aquecedor inicializado.")
        self.add_behaviour(self.HeaterBehaviour(self.environment, self.energy_agent, self.heating_power_per_degree, self.base_priority,self.system_state))
