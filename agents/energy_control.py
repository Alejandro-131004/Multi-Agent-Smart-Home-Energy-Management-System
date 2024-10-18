import asyncio

class EnergyAgent:
    def __init__(self, name, password, environment):
        self.name = name
        self.password = password
        self.environment = environment  # O ambiente é um atributo da classe
        self.current_price = None  # Preço atual da energia da rede
        self.energy_consumption_needed = 0.0  # Energia que os outros agentes vão precisar (em kWh)
        self.threshold_price = 0.20  # Preço limiar para o uso da energia da rede

    def start(self):
        """Inicia o ciclo do agente"""
        print(f"{self.name} agent started.")
        asyncio.run(self.run())

    def stop(self):
        """Finaliza o agente"""
        print(f"{self.name} agent stopped.")

    async def run(self):
        """Comportamento cíclico do agente"""
        while True:
            self.update_price()  # Atualiza o preço da energia
            self.act_on_price()  # Toma decisões com base no preço e na energia solar
            await asyncio.sleep(10)  # Espera 10 segundos antes de repetir o ciclo

    def update_price(self):
        """Atualiza o preço da energia da rede a partir do environment."""
        self.current_price = self.environment.get_energy_prices()  # Método correto do environment
        print(f"{self.name}: Atualizou o preço da energia para {self.current_price} €/kWh.")

    def receive_energy_request(self, consumption_needed):
        """Recebe pedidos de consumo de energia de outros agentes."""
        self.energy_consumption_needed += consumption_needed
        print(f"{self.name}: Recebeu pedido de {consumption_needed} kWh. Consumo total necessário: {self.energy_consumption_needed} kWh.")

    def act_on_price(self):
        """Toma ação baseada no preço da energia e no estado da bateria solar."""
        solar_energy_available = self.environment.solar_battery.get_state_of_charge()  # Supondo que solar_battery é um atributo de environment
        print(f"{self.name}: Energia solar disponível: {solar_energy_available} kWh.")

        if self.current_price is not None:
            print(f"{self.name} recebeu preço de energia: {self.current_price} €/kWh")

            # Se houver energia solar suficiente, usamos a energia solar primeiro
            if solar_energy_available > 0:
                energy_to_use = min(solar_energy_available, self.energy_consumption_needed)
                print(f"{self.name}: Vai usar {energy_to_use} kWh de energia solar.")
                self.environment.solar_battery.discharge(energy_to_use)  # Descarrega a bateria solar
                self.energy_consumption_needed -= energy_to_use
                print(f"{self.name}: Consumo restante após usar energia solar: {self.energy_consumption_needed} kWh.")
            else:
                print(f"{self.name}: Não há energia solar disponível.")

            # Caso ainda haja consumo necessário, usa energia da rede
            if self.energy_consumption_needed > 0:
                print(f"{self.name}: Precisa de {self.energy_consumption_needed} kWh da rede.")
                if self.current_price < self.threshold_price:
                    print(f"{self.name}: O preço está baixo ({self.current_price} €/kWh), pode consumir energia da rede.")
                elif self.current_price > self.threshold_price:
                    print(f"{self.name}: O preço está alto ({self.current_price} €/kWh), deve evitar consumo da rede.")
        else:
            print(f"{self.name}: Não foi possível obter o preço da energia.")

    def decide_heater_temperature(self, desired_temp, current_temp, base_heating_cost_per_degree):
        """Decide a temperatura em que o aquecedor deve operar com base no preço e na energia solar disponível."""
        solar_energy_available = self.environment.solar_battery.get_state_of_charge()
        temp_diff = desired_temp - current_temp

        # Verifica se a diferença de temperatura é positiva (precisa aquecer)
        print(f"{self.name}: Temperatura desejada: {desired_temp}°C, Temperatura atual: {current_temp}°C.")
        print(f"{self.name}: Diferença de temperatura necessária: {temp_diff}°C.")
        
        # Calcula o custo de energia por grau necessário
        energy_cost_per_degree = base_heating_cost_per_degree * temp_diff
        print(f"{self.name}: Custo de energia para aquecer {temp_diff}°C: {energy_cost_per_degree} kWh.")

        # Se houver energia solar, prefira usá-la
        if solar_energy_available > energy_cost_per_degree:
            print(f"{self.name}: Energia solar suficiente disponível. Aquecedor vai operar a {desired_temp}°C.")
            return desired_temp  # Pode operar na temperatura desejada
        else:
            print(f"{self.name}: Energia solar insuficiente. Energia solar disponível: {solar_energy_available} kWh.")

            # Se o preço da energia da rede for alto, ajuste para uma temperatura menor
            if self.current_price is not None and self.current_price > self.threshold_price:
                reduced_temp = current_temp + (solar_energy_available / base_heating_cost_per_degree)
                print(f"{self.name}: Preço da energia elevado ({self.current_price} €/kWh). Reduzindo temperatura para {reduced_temp}°C.")
                return reduced_temp
            else:
                print(f"{self.name}: Preço da energia aceitável ({self.current_price} €/kWh). Aquecedor vai operar a {desired_temp}°C.")
                return desired_temp
    async def decide_power(self, energy_needed):
        """
        Decide a quantidade de energia (LWatts) a ser alocada para o aquecedor com base na
        disponibilidade de energia solar, preço da rede e prioridade do aquecimento.
        """
        solar_energy_available = self.environment.solar_battery.get_state_of_charge()
        print(f"{self.name}: Energia solar disponível: {solar_energy_available} kWh.")
        
        # Prioridade de uso de energia solar
        if solar_energy_available > 0:
            energy_to_use = min(solar_energy_available, energy_needed)
            print(f"{self.name}: Vai usar {energy_to_use} kWh de energia solar.")
            self.environment.solar_battery.discharge(energy_to_use)
            return energy_to_use * 1000  # Convertendo para LWatts se necessário
        else:
            print(f"{self.name}: Não há energia solar disponível.")
        
        # Se não houver energia solar suficiente, verifica o preço da rede
        if self.current_price is not None and self.current_price <= self.threshold_price:
            # Permite usar energia da rede se o preço estiver abaixo do limiar
            print(f"{self.name}: Preço da rede aceitável ({self.current_price} €/kWh), pode usar energia da rede.")
            return energy_needed * 1000  # Aloca a energia necessária em LWatts
        else:
            # Se o preço da energia estiver alto, reduz o fornecimento
            print(f"{self.name}: Preço da rede alto ({self.current_price} €/kWh), fornecimento de energia reduzido.")
            return 0  # Não aloca energia da rede

        return 0  # Caso não haja energia disponível
