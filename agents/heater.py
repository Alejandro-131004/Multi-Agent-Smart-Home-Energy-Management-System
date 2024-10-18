from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio

class HeaterAgent(Agent):
    def __init__(self, jid, password, solar_battery):
        super().__init__(jid, password)
        self.solar_battery = solar_battery  # SolarBattery associada a este agente

    class HeaterBehaviour(CyclicBehaviour):
        def __init__(self, solar_battery):
            super().__init__()
            self.solar_battery = solar_battery  # Armazena a referência à SolarBattery

        async def run(self):
            # Definir a quantidade de energia necessária
            energy_needed = 3  # kWh
            print(f"[Aquecedor] Solicitando {energy_needed} kWh de energia solar...")

            # Tenta descarregar energia da SolarBattery
            energy_provided = self.solar_battery.discharge(energy_needed)

            if energy_provided > 0:
                print(f"[Aquecedor] Recebeu {energy_provided:.2f} kWh de energia solar.")
            else:
                print("[Aquecedor] Sem energia solar suficiente, consumindo da rede.")

            await asyncio.sleep(5)  # Espera 5 segundos antes de solicitar mais energia

    async def setup(self):
        print(f"[Aquecedor] Agente Aquecedor inicializado.")
        self.add_behaviour(self.HeaterBehaviour(self.solar_battery))  # Passa solar_battery para o comportamento
