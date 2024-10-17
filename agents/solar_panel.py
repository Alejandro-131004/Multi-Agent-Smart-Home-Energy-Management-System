from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time

# Agente do Painel Solar
class SolarPanelAgent(Agent):
    class SolarBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.energy_generated = 5  # Energia gerada (kWh)

        async def run(self):
            print(f"[Painel Solar] Gerando {self.energy_generated} kWh de energia")

            # Recebe mensagens de outros dispositivos
            msg = await self.receive(timeout=10)
            if msg:
                print(f"[Painel Solar] Recebeu consumo de {msg.sender}: {msg.body} kWh")

            await asyncio.sleep(10)  # Corrigido para usar asyncio.sleep