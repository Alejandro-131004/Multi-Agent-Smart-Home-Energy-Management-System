# agents/initialize_agents.py
from fridge import FridgeAgent
from heater import HeaterAgent
from solar_panel import SolarPanelAgent
import time
import asyncio

# Função para iniciar os agentes
async def start_agents():
    heater_agent = HeaterAgent("heater@localhost", "password")
    fridge_agent = FridgeAgent("fridge@localhost", "password")
    solar_agent = SolarPanelAgent("solar@localhost", "password")

    # Adiciona os comportamentos aos agentes
    heater_agent.add_behaviour(HeaterAgent.HeaterBehaviour())
    fridge_agent.add_behaviour(FridgeAgent.FridgeBehaviour())
    solar_agent.add_behaviour(SolarPanelAgent.SolarBehaviour())

    # Inicia os agentes
    await heater_agent.start()
    await fridge_agent.start()
    await solar_agent.start()

    # Controla o tempo de execução do sistema
    start_time = time.time()  # Marca o tempo de início

    while True:
        if time.time() - start_time > 60:  # Para após 60 segundos
            print("Encerrando agentes após 60 segundos.")
            await heater_agent.stop()
            await fridge_agent.stop()
            await solar_agent.stop()
            break
        await asyncio.sleep(1)  # Espera 1 segundo antes de verificar novamente
