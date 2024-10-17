from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time

class HeaterAgent(Agent):
    class HeaterBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.temperature_setting = 22  # Temperatura desejada
            self.current_price = 0.1  # Preço inicial da eletricidade
            self.consumption = 0  # Consumo total de energia

        async def run(self):
            # Simula o preço dinâmico da eletricidade
            self.current_price = round(random.uniform(0.05, 0.2), 2)
            print(f"[Aquecedor] Preço da eletricidade: {self.current_price} por kWh")

            # Comportamento do aquecedor baseado no preço
            if self.current_price < 0.15:  # Se o preço for baixo
                self.consumption += 1  # Consome mais energia
                print(f"[Aquecedor] Consumindo energia... Total: {self.consumption} kWh")
            else:
                print("[Aquecedor] Esperando...")

            # Enviar mensagem para o painel solar sobre o consumo
            msg = Message(to="solar@localhost")  # Supondo que o solar seja um agente
            msg.body = str(self.consumption)  # Enviando o consumo
            await self.send(msg)

            await asyncio.sleep(5)  # Corrigido para usar asyncio.sleep