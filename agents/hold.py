    async def decide_power(self, energy_needed, priority):
        """
        Decide a quantidade de energia a ser alocada para o aquecedor com base na
        disponibilidade de energia solar, preço da rede e prioridade do agente.
        """
        
        if solar_energy_available is not None:
            print(f"[Painel Solar] Gerando {solar_energy_available} kWh de energia")
            # Carregar a SolarBattery com a energia gerada, se válida
            if solar_energy_available > 0:
                self.environment.solar_battery.charge(solar_energy_available)
            else:
                print("[Painel Solar] Sem energia solar para carregar.")
        else:
            print("[Painel Solar] Não foi possível gerar energia solar.")
        # Ajusta a quantidade de energia alocada com base na prioridade
        print(energy_needed)
        

        self.update_price()
        # Verifica o preço da rede e ajusta o fornecimento
        if self.current_price is not None and self.current_price <= self.threshold_price:
            print(f"{self.name}: Preço da rede aceitável ({self.current_price} €/kWh).")
            return energy_needed # Aloca energia da rede
        else:
            print(f"{self.name}: Preço da rede alto ({self.current_price} €/kWh), fornecimento reduzido.")
            return 0  # Não aloca energia da rede