from agents.fridge import FridgeAgent
from agents.heater import HeaterAgent
from agents.solar_panel import SolarPanelAgent
from agents.solar_battery import SolarBattery
from agents.energy_control import EnergyAgent
from agents.system_state import SystemState
from agents.charger_EV import CarChargerAgent
import time
import asyncio

async def start_agents(env):
    # Cria a instância da SolarBattery no ambiente
    solar_battery = SolarBattery("solar_battery@localhost", "password", capacity_kwh=1000)

    env.solar_battery = solar_battery  # Associando a solar_battery ao ambiente
    print("[DEBUG] SolarBattery foi criada e associada ao ambiente.")
    
    # Inicializa os agentes passando o ambiente para todos eles
    energy_agent = EnergyAgent("energy_agent@localhost", "password", env,["system@localhost","heater@localhost","solar@localhost","fridge@localhost"])
    heater_agent = HeaterAgent("heater@localhost", "password", env, energy_agent)
    
    fridge_agent = FridgeAgent("fridge@localhost", "password")
    solar_agent = SolarPanelAgent("solar@localhost", "password")

    car_charger_agent = CarChargerAgent("car_charger@localhost", "password")
    print("[DEBUG] CarChargerAgent foi criado.")

    
    system_state = SystemState("system@localhost", "password",["energy_agent@localhost","heater@localhost","solar@localhost","fridge@localhost"])
    print("[DEBUG] Todos os agentes foram inicializados.")

    

    #car_charger_agent.add_behaviour(CarChargerAgent.CarChargerBehaviour())  # Adiciona o comportamento ao CarChargerAgent
    print("[DEBUG] CarChargerBehaviour foi adicionado ao CarChargerAgent.")
        

    system_state.add_behaviour(SystemState.CyclicStateBehaviour())
    heater_agent.add_behaviour(
        HeaterAgent.HeaterBehaviour(env, energy_agent)
    )
    print("[DEBUG] HeaterBehaviour foi adicionado ao HeaterAgent.")

    fridge_agent.add_behaviour(FridgeAgent.FridgeBehaviour())
    print("[DEBUG] FridgeBehaviour foi adicionado ao FridgeAgent.")
    #solar_agent.add_behaviour(SolarPanelAgent.SolarBehaviour())
    # Inicia os agentes
    
    await energy_agent.start()
    await solar_agent.start()
    await solar_battery.start()
    await system_state.start()
    await heater_agent.start()
    await fridge_agent.start()
    #await car_charger_agent.start()
    
    
    print("[DEBUG] Todos os agentes foram iniciados.")

    # Controla o tempo de execução do sistema
    start_time = time.time()

    while True:
        if time.time() - start_time > 60:  # Para após 60 segundos
            print("Encerrando agentes após 60 segundos.")
            await heater_agent.stop()
            await fridge_agent.stop()
            await system_state.stop()
            await solar_agent.stop()
            await car_charger_agent.stop()
            break
        await asyncio.sleep(1)  # Pausa para simulação
