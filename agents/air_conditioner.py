from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio

class AirconAgent(Agent):
    def __init__(self, jid, password, environment, energy_agent):
        super().__init__(jid, password)
        self.environment = environment  # Refere-se ao Environment
        self.energy_agent = energy_agent  # EnergyAgent para consultar sobre energia
        self.heating_power_per_degree = 1.0 # Exemplo: 1000 kWatts por grau de aquecimento
        self.cooling_power_per_degree = 2.0
        self.base_priority = 1.0 # Prioridade base do Aircon
        

    class AirconBehaviour(CyclicBehaviour):
        def __init__(self, environment, energy_agent, heating_power_per_degree,cooling_power_per_degree, base_priority):
            super().__init__()
            self.environment = environment
            self.energy_agent = energy_agent
            self.heating_power_per_degree = heating_power_per_degree
            self.cooling_power_per_degree = cooling_power_per_degree
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

            print(f"[Aircon] Grau de insatisfação: {dissatisfaction}°C. Prioridade dinâmica: {dynamic_priority}.")

            if dissatisfaction != 0:
                # Solicita ao EnergyAgent a energia necessária, baseado na prioridade dinâmica
                energy_needed = self.calculate_energy_consumption(dissatisfaction)
                print("need",energy_needed)
                energy_power = await self.energy_agent.decide_power(energy_needed, dynamic_priority)

                print(f"[Aircon] Potência recomendada pelo EnergyAgent: {energy_power} LWatts.")

                if energy_power > 0 and dissatisfaction > 0:
                    degrees_heated = energy_power / self.heating_power_per_degree
                    self.environment.update_room_temperature(degrees_heated)
                    print(f"[Aircon] A temperatura da sala foi aumentada em {degrees_heated}°C.")
                else:
                    print(f"[Aircon] Sem energia disponível para aquecimento.")
                if energy_power > 0 and dissatisfaction < 0:
                    degrees_cooled = energy_power / self.cooling_power_per_degree
                    self.environment.update_room_temperature(degrees_cooled)
                    print(f"[Aircon] A temperatura da sala foi aumentada em {degrees_cooled}°C.")
                else:
                    print(f"[Aircon] Sem energia disponível para aquecimento.")
            else :
                    print(f"Temperatura confortavel.")
                    self.environment.decrease_temperature()       # neeeeeeeeeeeeeed to change

            await asyncio.sleep(10)

        def calculate_priority(self, dissatisfaction):
            """
            Calcula a prioridade dinâmica baseada na insatisfação e na prioridade base.
            """
            if dissatisfaction < 0:
                return self.base_priority - dissatisfaction
            else :
                return self.base_priority + dissatisfaction  # Exemplo simples de cálculo de prioridade

        def calculate_energy_consumption(self, dissatisfaction):
            """
            Calcula o gasto de energia (Watts) por hora para compensar o grau de insatisfação.
             """
            if(dissatisfaction<0):
                kwh = self.cooling_power_per_degree *- dissatisfaction
            else:
                kwh =  self.heating_power_per_degree * dissatisfaction
                
            print("disati",kwh)
            return kwh   # Exemplo: 1000 LWatts por grau de insatisfação

    async def setup(self):
        print(f"[Aircon] Agente Aircon inicializado.")
        self.add_behaviour(self.AirconBehaviour(self.environment, self.energy_agent, self.heating_power_per_degree,self.cooling_power_per_degree, self.base_priority))
