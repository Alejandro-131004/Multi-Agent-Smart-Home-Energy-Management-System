from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import asyncio
import time

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
import random
from datetime import datetime


class CarChargerAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    class CarChargerBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.consumption = 0.0  # Total energy consumption initialized to 0
            self.priority = 0
            self.energy_per_cycle = 1.0

        async def run(self):
            energy_price = None
            solar_energy_available = 0  # Inicialize com um valor padrão
            car_battery = 0.0  # Estado inicial da bateria do carro

            # Solicite o preço da energia atual ao SystemState
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "energy_price":
                    try:
                        energy_price = float(msg.body)
                        print(f"[CarCharger] Current electricity price: {energy_price} €/kWh")
                    except ValueError:
                        print("[CarCharger] Received invalid energy price.")
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[CarCharger] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[CarCharger] No message received within the timeout.")
                    break

            # Configurar prioridade
            self.priority = self.calculate_dynamic_priority(energy_price=energy_price, solar_energy_available=solar_energy_available, car_battery=car_battery)

            request_msg = Message(to="system@localhost")  # Enviar para um agente específico
            request_msg.set_metadata("performative", "request")
            request_msg.set_metadata("type", "priority")
            request_msg.body = str(self.priority)  # Corpo da mensagem contém o valor de prioridade
            await self.send(request_msg)

            # Aguarde a resposta do agente SystemState
            while True:
                response = await self.receive(timeout=10)
                if response and response.get_metadata("type") == "solar_energy_available":
                    try:
                        solar_energy_available, battery_status, energy_price = map(float, response.body.split(","))
                        print(
                            f"[CarCharger] Energy conditions received: Solar={solar_energy_available} kWh, Battery={battery_status} kWh, Price={energy_price} €/kWh")
                        max_grid_energy = self.calculate_max_grid_energy(price_actual=energy_price,
                                                                         dynamic_priority=self.priority)
                        print({max_grid_energy}, "max grid energy de CarCharger")
                        solar_used = 0
                        battery_used = 0
                        grid_used = 0
                        energy_power = 0
                        energy_needed = self.energy_per_cycle
                        # Use solar energy first
                        if solar_energy_available > 0:
                            solar_used = min(solar_energy_available, energy_needed)
                            energy_power = solar_used

                            print(f"[CarCharger] Using {solar_used} kWh of solar energy.")
                            energy_needed -= solar_used  # Reduz a necessidade restante

                        # Use battery energy next
                        if energy_needed > 0 and battery_status > 0:
                            battery_used = min(battery_status, energy_needed)
                            energy_power += battery_used
                            print(f"[CarCharger] Using {battery_used} kWh of battery energy.")
                            energy_needed -= battery_used

                        # Use grid energy as a last resort
                        if energy_needed > 0 and max_grid_energy > 0:
                            grid_used = min(energy_needed, max_grid_energy)  # nao ultrapassa o limite
                            energy_power += grid_used
                            print(
                                f"[CarCharger] Using {grid_used:.2f} kWh of grid energy at cost {grid_used * energy_price:.2f}.")

                        if energy_needed <= 0:
                            print("[CarChargerter] Energy need satisfied.")
                            break  # Exit the loop when energy need is met

                        if energy_needed > max_grid_energy:
                            print(
                                f"[CarCharger] Unable to fully satisfy energy need with grid. {energy_needed - max_grid_energy:.2f} kWh left unmet.")
                            break
                        break
                    except ValueError:
                        print("[CarCharger] Received invalid energy data.")
                else:
                    print("[CarCharger] No response from SystemState or invalid message.")

            # Verificar se o carro está em casa (probabilidade dependente da hora do dia)
            current_hour = datetime.now().hour
            home_probability = self.get_home_probability(current_hour)

            # Gerar número aleatório para decidir se o carro está em casa
            random_number = random.randint(0, 99)
            is_home = random_number < home_probability
            print(f"[CarCharger] Car is {'home' if is_home else 'not home'} (Probability: {home_probability}%)")

            if is_home:
                # Consumo do carregador do carro (exemplo)
                consumption_amount = 3.0

                if energy_price is not None:
                    print(
                        f"[CarCharger] Washing started. Solar: {solar_used} kWh, Battery: {battery_used} kWh, Grid: {grid_used}")

                    msg = Message(to="system@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("type", "confirmation")
                    msg.body = f"{solar_used},{battery_used},{grid_used * energy_price:.2f}"
                    await self.send(msg)
                else:
                    print("[CarCharger] Energy price unavailable. Cannot calculate cost.")

            msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
            if msg:
                msg_type = msg.get_metadata("type")
                if msg_type == "state_request":
                    # Handle state request and reply with the CarCharger status
                    response = Message(to="system@localhost")
                    response.set_metadata("performative", "inform")
                    response.set_metadata("type", "state_response")
                    if energy_power > 0:
                        response.body = "on"
                    else:
                        response.body = "off"
                    await self.send(response)
                    print(f"[CarCharger] Sent state response:  to {msg.sender}.")
                else:
                    print(f"[CarCharger] Ignored message with metadata type: {msg_type}.")
            else:
                print("[CarCharger] No message received within the timeout.")

            # Simular espera de uma hora antes do próximo ciclo
            await asyncio.sleep(1)

        def get_home_probability(self, hour):
            # Definir a probabilidade de o carro estar em casa em função da hora do dia
            if 6 <= hour < 9:
                return 30  # 30% chance de estar em casa pela manhã
            elif 9 <= hour < 18:
                return 10  # 10% chance de estar em casa durante o dia
            elif 18 <= hour < 22:
                return 70  # 80% chance de estar em casa à noite
            else:
                return 80  # 50% chance de estar em casa de madrugada

        def calculate_dynamic_priority(self, energy_price, solar_energy_available, car_battery):
            """
            Calcula a prioridade dinâmica do carregador de carro com base em vários fatores.

            Parâmetros:
                energy_price (float): Preço atual da energia em €/kWh.
                solar_energy_available (float): Energia solar disponível em kWh.
                car_battery (float): Percentual da bateria do carro (0.0 a 100.0).

            Retorna:
                int: Prioridade dinâmica (0-100).
            """
            # Peso dos fatores na determinação da prioridade
            weight_energy_price = 0.4  # Peso para o preço da energia
            weight_solar_energy = 0.3  # Peso para a energia solar disponível
            weight_car_battery = 0.3  # Peso para o estado da bateria do carro

            # Normalizar os valores para a escala de 0 a 100
            normalized_energy_price = 100 - min(100, energy_price * 10)  # Quanto menor o preço, maior a prioridade
            normalized_solar_energy = min(100, solar_energy_available * 10)  # Mais energia solar, maior a prioridade
            normalized_car_battery = 100 - car_battery  # Menos bateria, maior a prioridade

            # Calcular a prioridade ponderada
            priority = (
                    weight_energy_price * normalized_energy_price +
                    weight_solar_energy * normalized_solar_energy +
                    weight_car_battery * normalized_car_battery
            )

            return int(priority)  # Garantir que a prioridade seja um inteiro

        def calculate_max_grid_energy(self, price_actual, dynamic_priority, max_possible_energy=3):

            # Definir limites com base nos quartis
            low_price_threshold = 49.35  # 1º quartil
            high_price_threshold = 68.01  # 3º quartil

            if price_actual < low_price_threshold:
                # Preço baixo: permitir uso total
                max_energy = max_possible_energy
            elif price_actual <= high_price_threshold:
                # Preço médio: uso proporcional à prioridade
                max_energy = max_possible_energy * (dynamic_priority / 10)  # Exemplo de escala de prioridade
            else:
                # Preço alto: limitar uso com base na prioridade
                max_energy = max_possible_energy * (dynamic_priority / 20)  # Reduzido devido ao preço alto

            # Garantir que a energia máxima não ultrapasse o limite máximo
            return min(max_possible_energy, max(0, max_energy))

