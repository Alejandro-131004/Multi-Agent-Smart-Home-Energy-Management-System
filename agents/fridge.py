from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time


# Agente do Refrigerador
class FridgeAgent(Agent):
    class FridgeBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.current_price = 0.1  # Preço inicial da eletricidade
            self.consumption = 0  # Consumo total de energia

        async def run(self):
            # Simula o preço dinâmico da eletricidade
            self.current_price = round(random.uniform(0.05, 0.2), 2)
            print(f"[Refrigerador] Preço da eletricidade: {self.current_price} por kWh")

            # Comportamento do refrigerador (consome energia constante)
            self.consumption += 0.5  # Consumo constante
            print(f"[Refrigerador] Consumindo energia... Total: {self.consumption} kWh")

            # Enviar mensagem para o painel solar sobre o consumo
            msg = Message(to="solar@localhost")
            msg.body = str(self.consumption)
            await self.send(msg)

            await asyncio.sleep(10)  # Corrigido para usar asyncio.sleep