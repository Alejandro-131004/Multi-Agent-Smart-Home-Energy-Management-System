# main.py
import pandas as pd
import asyncio
from agents.initialize_agents import start_agents
from environment import Environment

def main():
    # Initialize the environment
    env = Environment(date='2015-01-01 00:00:00', city='Valencia', num_divisions=5)
    
    # Display weather data
    env.display_weather_data()

    # Get current energy price
    current_price = env.get_price_for_current_hour()
    print(f"Current energy price: {current_price}")

    # Start agents
    asyncio.run(start_agents())

if __name__ == "__main__":
    main()
