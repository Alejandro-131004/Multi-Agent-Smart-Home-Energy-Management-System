import pandas as pd
import csvs
from agent import EnergyAgent  # Import the EnergyAgent class

class Environment:
    def __init__(self, date, city, num_divisions, solar_power_available, energy_storage_capacity):
        # Parse the date while keeping timezone info fixed to CET (UTC+1)
        self.date = pd.to_datetime(date)  # Keep it as a naive datetime for CET
        self.city = city
        self.num_divisions = num_divisions
        self.solar_power_available = solar_power_available
        self.energy_storage_capacity = energy_storage_capacity
        self.weather_data = self.load_weather_data()
        self.energy_data = self.load_energy_data()
        self.energy_prices = self.get_energy_prices()  # Load energy prices

    def load_weather_data(self):
        weather_df = csvs.get_cleaned_weather_data()

        # Filter the data by the specified city
        city_data = weather_df[weather_df['city_name'] == self.city]

        # Find records with the specified date and time
        filtered_data = city_data[city_data['dt_iso'].str.startswith(f"{self.date.date()} {self.date.hour:02d}:00")]

        print("Filtered weather data:")
        print(filtered_data)

        if filtered_data.empty:
            print(f"No weather data found for {self.date.hour:02d} hours in {self.city} on {self.date.date()}")
            return None
        else:
            current_weather = filtered_data.iloc[0]
            return current_weather

    def load_energy_data(self):
        energy_df = csvs.get_cleaned_energy_data()
        return energy_df

    def get_energy_prices(self):
    # Convert 'time' column to datetime, assuming it might be in ISO 8601 format
        self.energy_data['date_time'] = pd.to_datetime(self.energy_data['time'], errors='coerce')

        # Check for any conversion issues
        if self.energy_data['date_time'].isnull().any():
            print("Warning: Some dates could not be parsed. Here are the problematic entries:")
            print(self.energy_data[self.energy_data['date_time'].isnull()]['time'])

        # Extract the "price actual" column
        prices = self.energy_data.set_index('date_time')['price actual'].to_dict()  # Convert to dictionary for easy access
        print("Energy prices available:")
        print(prices.keys())  # Print the available timestamps
        return prices




    def get_price_for_current_hour(self):
        # Get the current hour's energy price, ensuring we match the format exactly
        current_hour = self.date.replace(minute=0, second=0, microsecond=0)
        
        # Localize to the correct timezone, which in this case is UTC+1
        current_hour = current_hour.tz_localize('UTC+01:00')  # Adjust timezone as necessary
        
        # Look up the price using the correctly formatted timestamp
        price = self.energy_prices.get(current_hour, None)
        
        if price is None:
            print(f"Looking for energy price at {current_hour.isoformat()}")  # This will output in the desired format
        
        return price

    def update_time(self, new_time):
        """Update the current time and optionally update any other state."""
        self.date = self.date.replace(hour=new_time)

    def display_weather_data(self):
        if self.weather_data is not None:
            print(f"Weather data for {self.city} at {self.date.hour:02d} hours:")
            print(self.weather_data)
        else:
            print("No weather data available.")

if __name__ == "__main__":
    # Initialize the environment starting from January 1, 2015
    env = Environment(date='2015-01-01 00:00:00',  # No timezone information needed
                      city='Valencia', 
                      num_divisions=5, 
                      solar_power_available=5.0, 
                      energy_storage_capacity=10.0)
    
    env.display_weather_data()

    # Initialize and start the energy agent
    energy_agent = EnergyAgent("energy_agent@localhost", "password", environment=env)
    energy_agent.start()

    # Update for each hour of the year 2015
    current_date = env.date
    end_date = pd.to_datetime('2015-01-05 23:00:00')  # End of the year

    while current_date <= end_date:
        # Update the agent's price and take action
        energy_agent.update_price()
        energy_agent.act_on_price()

        # Print current date and corresponding energy price
        energy_price = env.get_price_for_current_hour()
        print(f"\nEnergy price at {current_date.strftime('%Y-%m-%d %H:%M:%S')} is {energy_price}")

        # Update the date by one hour
        current_date += pd.Timedelta(hours=1)
        env.update_time(current_date.hour)  # Update the environment's time

    # Stop the agent when done
    energy_agent.stop()
