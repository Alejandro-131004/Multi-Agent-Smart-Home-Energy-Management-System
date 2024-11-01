from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time


# Agente do Refrigerador
class FridgeAgent(Agent):
    def __init__(self, jid, password, environment, energy_agent):
            super().__init__(jid, password)
            self.environment = environment  # Refere-se ao Environment
            self.energy_agent = energy_agent
            self.current_price = None  # Preço inicial da eletricidade
            self.consumption = None # Consumo total de energia
    class FridgeBehaviour(CyclicBehaviour):
        def __init__(self, environment, energy_agent, current_price, consumption):
            super().__init__()
            self.environment = environment
            self.energy_agent = energy_agent
            self.current_price = current_price  # Preço inicial da eletricidade
            self.consumption = consumption # Consumo total de energia

        async def run(self):
            # Simula o preço dinâmico da eletricidade
            self.current_price = round(random.uniform(0.05, 0.2), 2)
            print(f"[Refrigerador] Preço da eletricidade: {self.current_price} por kWh")

            # Comportamento do refrigerador (consome energia constante)
            self.consumption += 0.5  # Consumo constante
            print(f"[Refrigerador] Consumindo energia... Total: {self.consumption} kWh")

            # Enviar mensagem para o painel solar sobre o consumo
            #msg = Message(to="solar@localhost")
            #msg.body = str(self.consumption)
            #await self.send(msg)

            await asyncio.sleep(10)  # Corrigido para usar asyncio.sleep
    
    async def setup(self):
        print(f"[Aquecedor] Agente Aquecedor inicializado.")
        self.add_behaviour(self.FridgeBehaviour(self.environment, self.energy_agent,self.current_price, self.consumption))