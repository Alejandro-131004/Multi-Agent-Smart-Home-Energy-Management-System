from agents.fridge import FridgeAgent
from agents.heater import HeaterAgent
from agents.solar_panel import SolarPanelAgent
from agents.solar_battery import SolarBattery
import time
import asyncio

# Função para iniciar os agentes
async def start_agents():
    # Cria a instância da SolarBattery
    solar_battery = SolarBattery(capacity_kwh=1000)

    # Inicializa os agentes com a solar_battery
    heater_agent = HeaterAgent("heater@localhost", "password", solar_battery)
    fridge_agent = FridgeAgent("fridge@localhost", "password")
    solar_agent = SolarPanelAgent("solar@localhost", "password", solar_battery)

    # Adiciona os comportamentos aos agentes, passando a solar_battery para o comportamento do Heater
    heater_agent.add_behaviour(HeaterAgent.HeaterBehaviour(solar_battery))
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
