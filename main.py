import pandas as pd
import asyncio
from agents.initialize_agents import start_agents
from datetime import datetime, timedelta

def main():
    # Define a data de início e término
    start_date = datetime.strptime('2018-04-26 19:00:00', '%Y-%m-%d %H:%M:%S')
    #end_date = datetime.strptime('2015-01-01 23:00:00', '%Y-%m-%d %H:%M:%S')
    
    current_date = start_date
   
    asyncio.run(start_agents(date=current_date.strftime('%Y-%m-%d %H:%M:%S'), city='Madrid', num_divisions=5, desired_temperature=10))  # Passando env como argumento
    
       
        
        

if __name__ == "__main__":
    main()
