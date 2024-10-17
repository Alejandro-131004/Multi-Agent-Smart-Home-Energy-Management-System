# main.py
import environment
from agents.energy_control import EnergyAgent
#import agents

'''if __name__ == "__main__":
    # Initialize the environment starting from January 1, 2015
    env = environment.Environment(date='2015-01-01 00:00:00',
                                  city='Valencia',
                                  num_divisions=5)

    env.display_weather_data()

    # Initialize and start the energy agent
    energy_agent = EnergyAgent("energy_agent@localhost", "password", environment=env)
    energy_agent.start()

    # Update for each hour of the year 2015
    current_date = env.date
    end_date = environment.pd.to_datetime('2015-08-05 23:00:00')  # End of the year

    while current_date <= end_date:
        # Update the agent's price and take action
        energy_agent.update_price()
        energy_agent.act_on_price()

        # Print current date and corresponding energy price
        energy_price = env.get_price_for_current_hour()
        print(f"\nEnergy price at {current_date.strftime('%Y-%m-%d %H:%M:%S')} is {energy_price}")

        # Update the date by one hour
        current_date += environment.pd.Timedelta(hours=1)
        env.update_time(current_date.hour)  # Update the environment's time

    # Stop the agent when done
    energy_agent.stop()'''


# main.py
import pandas as pd
from agents.initialize_agents import start_agents
from environment import Environment
import asyncio

def main():


    # Criação do ambiente
    env = Environment(date='2015-01-01 00:00:00',city='Valencia', num_divisions=5)

    # Exibir dados meteorológicos
    env.display_weather_data()

    # Obter o preço da energia para a hora atua
    current_price = env.get_price_for_current_hour()
    print(f"Current energy price: {current_price}")

    # Inicializar e executar os agentes
    asyncio.run(start_agents())

if __name__ == "__main__":
    main()

