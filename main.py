# main.py
import pandas as pd
import asyncio
from agents.initialize_agents import start_agents
from environment import Environment

def main():
    # Inicializa o ambiente
    env = Environment(date='2015-01-01 00:00:00', city='Valencia', num_divisions=5,desired_temperature=24)
    
    # Exibe os dados meteorológicos
    env.display_weather_data()

    # Obtém o preço atual da energia
    current_price = env.get_price_for_current_hour()
    print(f"Current energy price: {current_price}")

    # Inicia os agentes, passando o ambiente para a função start_agents
    asyncio.run(start_agents(env))  # Passando env como argumento

if __name__ == "__main__":
    main()
