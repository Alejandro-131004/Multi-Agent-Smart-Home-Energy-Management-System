import pandas as pd
import asyncio
from agents.initialize_agents import start_agents
from environment import Environment
from datetime import datetime, timedelta

def main():
    # Define a data de início e término
    start_date = datetime.strptime('2015-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime('2015-01-01 23:00:00', '%Y-%m-%d %H:%M:%S')
    
    current_date = start_date
    
    # Loop até alcançar a data de término
    while current_date <= end_date:
        # Inicializa o ambiente
        env = Environment(date=current_date.strftime('%Y-%m-%d %H:%M:%S'), city='Valencia', num_divisions=5, desired_temperature=24)
        
        # Exibe os dados meteorológicos
        env.display_weather_data()

        # Obtém o preço atual da energia
        current_price = env.get_price_for_current_hour()
        print(f"Current energy price for {current_date}: {current_price}")
        
        # Inicia os agentes, passando o ambiente para a função start_agents
        asyncio.run(start_agents(env))  # Passando env como argumento
        
        # Avança uma hora no tempo
        current_date += timedelta(hours=1)

if __name__ == "__main__":
    main()
