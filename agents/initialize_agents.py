from agents.fridge import FridgeAgent
from agents.heater import HeaterAgent
from agents.solar_panel import SolarPanelAgent
from agents.solar_battery import SolarBattery

from agents.system_state import SystemState
from agents.charger_EV import CarChargerAgent
from environment import EnvironmentAgent
from agents.washing_machine import WashingMachineAgent
from agents.windows import WindowAgent
from agents.air_conditioner import AirconAgent
import time
import asyncio

async def start_agents(date, city, num_divisions, desired_temperature):
    """
    Initializes and starts agents with the given parameters.
    
    Args:
        date (str): Simulation start date in 'YYYY-MM-DD HH:MM:SS' format.
        city (str): The city for weather simulation.
        num_divisions (int): Number of divisions for the simulation.
        desired_temperature (float): Desired indoor temperature.
    """
    # Initialize the EnvironmentAgent with the provided parameters
    env_agent = EnvironmentAgent(
        jid="environment@localhost",
        password="password",
        date=date,
        city=city,
        num_divisions=num_divisions,
        desired_temperature=desired_temperature,
    )

    print("[DEBUG] EnvironmentAgent initialized with parameters:")
    print(f"       Date: {date}, City: {city}, Divisions: {num_divisions}, Desired Temperature: {desired_temperature}")

    # Initialize other agents
    solar_battery = SolarBattery("solar_battery@localhost", "password", capacity_kwh=10)
    heater_agent = HeaterAgent("heater@localhost", "password", desired_temperature)
    fridge_agent = FridgeAgent("fridge@localhost", "password")
    solar_agent = SolarPanelAgent("solar@localhost", "password")
    washing_agent = WashingMachineAgent("washing@localhost", "password")
    windows_agent = WindowAgent("windows@localhost", "password", desired_temperature)
    aircon_agent = AirconAgent("aircon@localhost", "password", desired_temperature)
    system_state = SystemState("system@localhost", "password", ["energy_agent@localhost", "heater@localhost", "solar@localhost", "fridge@localhost", "washing@localhost", "windows@localhost", "aircon@localhost"])

    print("[DEBUG] All agents have been initialized.")

    # Add behaviours to agents
    system_state.add_behaviour(SystemState.CyclicStateBehaviour())
    heater_agent.add_behaviour(HeaterAgent.HeaterBehaviour())
    fridge_agent.add_behaviour(FridgeAgent.FridgeBehaviour())
    aircon_agent.add_behaviour(AirconAgent.AirconBehaviour())
    washing_agent.add_behaviour(WashingMachineAgent.WashingMachineBehaviour())
    #print("[DEBUG] WashingMachineBehaviour foi adicionado ao WashingMachineAgent.")
    windows_agent.add_behaviour(WindowAgent.WindowBehaviour())


    # Start agents
    await env_agent.start()
    await solar_battery.start()
    await heater_agent.start()
    await aircon_agent.start()
    await windows_agent.start()
    await fridge_agent.start()
    await solar_agent.start()
    await washing_agent.start()
    await system_state.start()
    #await car_charger_agent.start()
    
    print("[DEBUG] Todos os agentes foram iniciados.")

    # Controla o tempo de execução do sistema
    start_time = time.time()

    while True:
        if time.time() - start_time > 60:  # Para após 60 segundos
            print("Encerrando agentes após 60 segundos.")
            await env_agent.stop()
            await heater_agent.stop()
            await aircon_agent.stop()
            await windows_agent.stop()
            await fridge_agent.stop()
            await system_state.stop()
            await washing_agent.stop()
            await solar_agent.stop()
            #await car_charger_agent.stop()
            break
        await asyncio.sleep(1)  # Pausa para simulação
