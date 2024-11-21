from itertools import cycle

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
import random

class WashingMachineAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    class WashingMachineBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.clothes_count = 0  # Número atual de peças na caixa
            self.box_capacity = 10  # Capacidade máxima antes de lavar
            self.energy_per_cycle = 1.0  # Consumo de energia por ciclo (kWh)
            self.cycle_washtime = 2
            self.priority = 15  # Prioridade da máquina de lavar
            self.cycle_hour = 0

        async def run(self):
            energy_price = None
            energy_power = 0
            solar_energy_available = 0  # Valor inicial de energia solar disponível
            battery_status = 0  # Valor inicial de status da bateria
            # Solicite o preço da energia atual ao SystemState
            while True:
                msg = await self.receive(timeout=10)  # Aguarde uma mensagem por até 10 segundos
                if msg and msg.get_metadata("type") == "solar_auction_started":
                    break  # Saia do loop após processar a mensagem
                elif msg:
                    print(f"[Washing Machine] Ignored message with metadata type: {msg.get_metadata('type')}")
                else:
                    print("[Washing Machine] No message received within the timeout.")

            # Adicionar roupas por hora
            self.add_clothes()

            self.priority = self.calculate_dynamic_priority()

            # Se a caixa está cheia, preparar para lavar
            if (self.clothes_count >= self.box_capacity*0.8) or (self.cycle_hour == 1):
                if self.cycle_hour == 0:
                    print(f"[Washing Machine] Box full with {self.clothes_count} clothes. Ready to wash.")
                self.cycle_hour+=1
                # Configurar prioridade e enviar ao `SystemState`
                request_msg = Message(to="system@localhost")
                request_msg.set_metadata("performative", "request")
                request_msg.set_metadata("type", "priority")
                request_msg.body = str(self.priority)
                await self.send(request_msg)

                # Aguardar resposta com condições de energia
                while True:
                    response = await self.receive(timeout=30)
                    if response and response.get_metadata("type") == "energy_availablility":
                        try:
                            solar_energy_available, battery_status, energy_price = map(float, response.body.split(","))
                            print(f"[Washing Machine] Energy conditions received: Solar={solar_energy_available} kWh, Battery={battery_status} kWh, Price={energy_price} €/kWh")
                            max_grid_energy = self.calculate_max_grid_energy(price_actual=energy_price, dynamic_priority=self.priority)
                            print ({max_grid_energy},"max grid energy de washing machine")
                            solar_used = 0
                            battery_used = 0
                            grid_used = 0
                            energy_power = 0
                            energy_needed=self.energy_per_cycle
                            # Use solar energy first
                            if solar_energy_available > 0:
                                solar_used = min(solar_energy_available, energy_needed)
                                energy_power = solar_used
            
                                print(f"[Washing Machine] Using {solar_used} kWh of solar energy.")
                                energy_needed -= solar_used  # Reduz a necessidade restante

                            # Use battery energy next
                            if energy_needed > 0 and battery_status > 0:
                                battery_used = min(battery_status, energy_needed)
                                energy_power += battery_used
                                print(f"[Washing Machine] Using {battery_used} kWh of battery energy.")
                                energy_needed -= battery_used

                            # Use grid energy as a last resort
                            if energy_needed > 0 and max_grid_energy > 0:
                                grid_used = min(energy_needed, max_grid_energy)  # nao ultrapassa o limite
                                energy_power += grid_used
                                print(f"[Washing Machine] Using {grid_used:.2f} kWh of grid energy at cost {grid_used * energy_price:.2f}.")


                            if energy_needed <= 0:
                                print("[Washing Machineter] Energy need satisfied.")
                                break  # Exit the loop when energy need is met

                            if energy_needed > max_grid_energy:
                                print(f"[Washing Machine] Unable to fully satisfy energy need with grid. {energy_needed - max_grid_energy:.2f} kWh left unmet.")
                                break
                            break
                        except ValueError:
                            print("[Washing Machine] Received invalid energy data.")
                    else:
                        print("[Washing Machine] No response from SystemState.")
                        return

                if energy_price is not None:
                    
                    print(f"[Washing Machine] Washing started. Solar: {solar_used} kWh, Battery: {battery_used} kWh, Grid: {grid_used}")

                    if self.cycle_hour == 1:
                        # Resetar o número de roupas após lavar
                        self.clothes_count = 0

                    # Enviar mensagem de confirmação ao SystemState
                    confirmation_msg = Message(to="system@localhost")
                    confirmation_msg.set_metadata("performative", "inform")
                    confirmation_msg.set_metadata("type", "confirmation")
                    confirmation_msg.body = f"{solar_used},{battery_used},{grid_used * energy_price:.2f}"
                    await self.send(confirmation_msg)
                else:
                    print("[Washing Machine] Energy price unavailable. Cannot start washing.")

            elif self.cycle_hour == 2:
                self.cycle_hour = 0
                print(f"[Washing Machine] Waiting for more clothes. Current count: {self.clothes_count}/{self.box_capacity}")
            else:
                print(f"[Washing Machine] Waiting for more clothes. Current count: {self.clothes_count}/{self.box_capacity}")
            
            msg = await self.receive(timeout=10)  # Wait for a message for up to 10 seconds
            if msg:
                msg_type = msg.get_metadata("type")
                if msg_type == "state_request":
                    # Handle state request and reply with the washing machine status
                    response = Message(to="system@localhost")
                    response.set_metadata("performative", "inform")
                    response.set_metadata("type", "state_response")
                    if energy_power > 0:
                        response.body = "on"
                    else:
                        response.body = "off"
                    await self.send(response)
                    print(f"[Washing Machine] Sent state response:  to {msg.sender}.")
                else:
                    print(f"[Washing Machine] Ignored message with metadata type: {msg_type}.")
            else:
                print("[Washing Machine] No message received within the timeout.")

            # Simular espera de uma hora antes do próximo ciclo
            await asyncio.sleep(1)

        def add_clothes(self):
            """Adiciona roupas de forma aleatória à máquina de lavar."""
            new_clothes = random.randint(1, 5)  # Adiciona de 1 a 5 peças de roupa
            self.clothes_count += new_clothes
            if self.clothes_count <= self.box_capacity:
                print(f"[Washing Machine] Added {new_clothes} clothes. Total: {self.clothes_count}/{self.box_capacity}")
            else:
                self.clothes_count = 0
                print(f"[Washing Machine] The box is now empty, you can put on some clothes. Total: {self.clothes_count}/{self.box_capacity}")
        '''
        def calculate_consumption(self, consumption_amount, solar_energy_available, battery_status, energy_price):
            """Calcula a energia consumida durante o ciclo."""
            solar_used = 0
            battery_used = 0
            cost = 0

            # Priorizar energia solar
            if solar_energy_available >= consumption_amount:
                solar_used = consumption_amount
                cost = 0
            else:
                solar_used = solar_energy_available
                remaining_energy = consumption_amount - solar_used

                # Utilizar energia da bateria
                if battery_status >= remaining_energy:
                    battery_used = remaining_energy
                    cost = 0
                else:
                    battery_used = battery_status
                    remaining_energy -= battery_used

                    # Usar energia da rede elétrica
                    cost = remaining_energy * energy_price

            return solar_used, battery_used, cost
            '''

        def calculate_dynamic_priority(self):
            """Calcula a prioridade dinâmica com base na ocupação do cesto."""
            fill_percentage = self.clothes_count / self.box_capacity  # Percentagem do cesto cheio

            if fill_percentage <= 0.5:
                # Abaixo de 50% não é permitido iniciar a lavagem
                return 0
            elif fill_percentage < 0.8:
                # Entre 50% e 80%, a prioridade aumenta gradualmente
                return self.priority + (fill_percentage - 0.5) * 20  # Ajusta com base na ocupação
            elif fill_percentage < 1.0:
                # Entre 80% e 100%, a prioridade aumenta significativamente
                return self.priority + 10 + (fill_percentage - 0.8) * 50
            else:
                # Cesto 100% cheio retorna uma prioridade muito alta
                return 1000
            
        def calculate_max_grid_energy(self,price_actual, dynamic_priority, max_possible_energy=3):
        
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


