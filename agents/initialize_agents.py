from agents.fridge import FridgeAgent
from agents.heater import HeaterAgent
from agents.solar_panel import SolarPanelAgent
from agents.solar_battery import SolarBattery
from agents.energy_control import EnergyAgent
import time
import asyncio


async def start_agents(env):
    # Cria a instância da SolarBattery no ambiente
    solar_battery = SolarBattery(capacity_kwh=1000)
    env.solar_battery = solar_battery  # Associando a solar_battery ao ambiente
    energy_agent = EnergyAgent("energy_agent@localhost", "password", env)  # Adicione aqui o nome e a senha adequados
   
    # Inicializa os agentes passando o ambiente para todos eles
    heater_agent = HeaterAgent("heater@localhost", "password", env, energy_agent)  # Passa o ambiente
    fridge_agent = FridgeAgent("fridge@localhost", "password", env)  # Passa o ambiente
    solar_agent = SolarPanelAgent("solar@localhost", "password", env)  # Passa o ambiente

    # Adiciona os comportamentos aos agentes, passando os parâmetros necessários
    heater_power_per_degree = 10  # Exemplo de valor, ajuste conforme necessário
    weight_dissatisfaction = 1.0  # Exemplo de valor, ajuste conforme necessário

    heater_agent.add_behaviour(
        HeaterAgent.HeaterBehaviour(env, energy_agent, heater_power_per_degree, weight_dissatisfaction)
    )
    fridge_agent.add_behaviour(FridgeAgent.FridgeBehaviour())
    solar_agent.add_behaviour(SolarPanelAgent.SolarBehaviour())

    # Inicia os agentes
    await heater_agent.start()
    await fridge_agent.start()
    await solar_agent.start()

    # Controla o tempo de execução do sistema
    start_time = time.time()

    while True:
        if time.time() - start_time > 60:  # Para após 60 segundos
            print("Encerrando agentes após 60 segundos.")
            await heater_agent.stop()
            await fridge_agent.stop()
            await solar_agent.stop()
            break
        await asyncio.sleep(1)  # Pausa para simulação
