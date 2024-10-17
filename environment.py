import pandas as pd
import csvs

'''class Environment:
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
        
        # Try to get the price with UTC+1
        current_hour_utc1 = current_hour.tz_localize('UTC+01:00')
        price = self.energy_prices.get(current_hour_utc1, None)
        
        if price is None:
            print(f"Looking for energy price at {current_hour_utc1.isoformat()} - not found, trying UTC+2")
            # Try to get the price with UTC+2 if the first attempt fails
            current_hour_utc2 = current_hour.tz_localize('UTC+02:00')
            price = self.energy_prices.get(current_hour_utc2, None)

            if price is not None:
                print(f"Found energy price at {current_hour_utc2.isoformat()}")
            else:
                print(f"Looking for energy price at {current_hour_utc2.isoformat()} - not found")

        else:
            print(f"Found energy price at {current_hour_utc1.isoformat()}")

        return price


    def update_time(self, new_time):
        """Update the current time and optionally update any other state."""
        self.date = self.date.replace(hour=new_time)

    def display_weather_data(self):
        if self.weather_data is not None:
            print(f"Weather data for {self.city} at {self.date.hour:02d} hours:")
            print(self.weather_data)
        else:
            print("No weather data available.")'''

class Environment:
    def __init__(self, date, city, num_divisions):
        # Parse the date while keeping timezone info fixed to CET (UTC+1)
        self.date = pd.to_datetime(date)  # Keep it as a naive datetime for CET
        self.city = city
        self.num_divisions = num_divisions
        self.weather_data = self.load_weather_data()
        self.energy_data = self.load_energy_data()
        self.energy_prices = self.get_energy_prices()  # Load energy prices

    def load_weather_data(self):
        weather_df = csvs.get_cleaned_weather_data()
        city_data = weather_df[weather_df['city_name'] == self.city]
        filtered_data = city_data[city_data['dt_iso'].str.startswith(f"{self.date.date()} {self.date.hour:02d}:00")]
        if filtered_data.empty:
            return None
        return filtered_data.iloc[0]

    def load_energy_data(self):
        energy_df = csvs.get_cleaned_energy_data()
        return energy_df

    def get_energy_prices(self):
        self.energy_data['date_time'] = pd.to_datetime(self.energy_data['time'], errors='coerce')
        prices = self.energy_data.set_index('date_time')['price actual'].to_dict()
        return prices

    def get_price_for_current_hour(self):
        # Obtém a hora atual do preço da energia, garantindo que o formato esteja exatamente correto
        current_hour = self.date.replace(minute=0, second=0, microsecond=0)

        # Tenta obter o preço com UTC+1
        current_hour_utc1 = current_hour.tz_localize('UTC+01:00')
        price = self.energy_prices.get(current_hour_utc1, None)

        if price is None:
            print(f"Looking for energy price at {current_hour_utc1.isoformat()} - not found, trying UTC+2")
            # Tenta obter o preço com UTC+2 se a primeira tentativa falhar
            current_hour_utc2 = current_hour.tz_localize('UTC+02:00')
            price = self.energy_prices.get(current_hour_utc2, None)

            if price is not None:
                print(f"Found energy price at {current_hour_utc2.isoformat()}")
            else:
                print(f"Looking for energy price at {current_hour_utc2.isoformat()} - not found")
        else:
            print(f"Found energy price at {current_hour_utc1.isoformat()}")

        return price

    def update_time(self, new_time):
        """Atualiza a hora atual e, opcionalmente, atualiza qualquer outro estado."""
        self.date = self.date.replace(hour=new_time)

    def display_weather_data(self):
        if self.weather_data is not None:
            print(f"Weather data for {self.city} at {self.date.hour:02d} hours:")
            print(self.weather_data)
        else:
            print("No weather data available.")

