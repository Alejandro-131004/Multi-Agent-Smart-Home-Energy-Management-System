from agents.fridge import FridgeAgent
from agents.heater import HeaterAgent
from agents.solar_panel import SolarPanelAgent
from agents.solar_battery import SolarBattery
from agents.energy_control import EnergyAgent
from agents.system_state import SystemState
import time
import asyncio

async def start_agents(env):
    # Cria a instância da SolarBattery no ambiente
    solar_battery = SolarBattery(capacity_kwh=1000)
    env.solar_battery = solar_battery  # Associando a solar_battery ao ambiente
    print("[DEBUG] SolarBattery foi criada e associada ao ambiente.")
    system_state = SystemState("system@localhost", "password")
    # Inicializa os agentes passando o ambiente para todos eles
    energy_agent = EnergyAgent("energy_agent@localhost", "password", env)
    heater_agent = HeaterAgent("heater@localhost", "password", env, energy_agent)
    
    #fridge_agent = FridgeAgent("fridge@localhost", "password", env)
    solar_agent = SolarPanelAgent("solar@localhost", "password", env.solar_battery)
    print("[DEBUG] Todos os agentes foram inicializados.")

    # Adiciona os comportamentos aos agentes, passando os parâmetros necessários
    

    system_state.add_behaviour(SystemState.CyclicStateBehaviour())
    heater_agent.add_behaviour(
        HeaterAgent.HeaterBehaviour(env, energy_agent)
    )
    print("[DEBUG] HeaterBehaviour foi adicionado ao HeaterAgent.")

    #fridge_agent.add_behaviour(FridgeAgent.FridgeBehaviour())
    print("[DEBUG] FridgeBehaviour foi adicionado ao FridgeAgent.")

    solar_agent.add_behaviour(SolarPanelAgent.SolarBehaviour())
    print("[DEBUG] SolarBehaviour foi adicionado ao SolarPanelAgent.")

    # Inicia os agentes
    await heater_agent.start()
    #await fridge_agent.start()
    await solar_agent.start()
    await system_state.start()
    print("[DEBUG] Todos os agentes foram iniciados.")

    # Controla o tempo de execução do sistema
    start_time = time.time()

    while True:
        if time.time() - start_time > 60:  # Para após 60 segundos
            print("Encerrando agentes após 60 segundos.")
            await heater_agent.stop()
            #wait fridge_agent.stop()
            await system_state.stop()
            await solar_agent.stop()
            break
        await asyncio.sleep(1)  # Pausa para simulação
