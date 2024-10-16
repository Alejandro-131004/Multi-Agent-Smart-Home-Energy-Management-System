from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time

# Agente do Aquecedor
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

# Executando o código
if __name__ == "__main__":
    asyncio.run(start_agents())
