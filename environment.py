import csvs 

class Environment:
    def __init__(self, date, city, time_of_day, num_divisions, solar_power_available, energy_storage_capacity):
        self.date = date
        self.city = city
        self.time_of_day = time_of_day
        self.num_divisions = num_divisions
        self.solar_power_available = solar_power_available
        self.energy_storage_capacity = energy_storage_capacity
        self.weather_data = self.load_weather_data()
        self.energy_data = self.load_energy_data()

    def load_weather_data(self):
        weather_df = csvs.get_cleaned_weather_data()

        # Filtrar os dados pela cidade especificada
        city_data = weather_df[weather_df['city_name'] == self.city]

        # Encontrar registros com a data e hora especificada
        filtered_data = city_data[city_data['dt_iso'].str.startswith(f"{self.date} {self.time_of_day}:00")]

        print("Dados filtrados:")
        print(filtered_data)

        if filtered_data.empty:
            print(f"Nenhum dado meteorológico encontrado para {self.time_of_day} horas na cidade {self.city} na data {self.date}")
            return None
        else:
            current_weather = filtered_data.iloc[0]
            return current_weather



    def load_energy_data(self):
        energy_df = csvs.get_cleaned_energy_data()
        return energy_df

    def display_weather_data(self):
        if self.weather_data is not None:
            print(f"Dados Meteorológicos para {self.city} às {self.time_of_day:02d} horas:")
            print(self.weather_data)
        else:
            print("Sem dados meteorológicos disponíveis.")

if __name__ == "__main__":
    env = Environment(date='2015-01-01', 
                      city='Valencia', 
                      time_of_day=14, 
                      num_divisions=5, 
                      solar_power_available=5.0, 
                      energy_storage_capacity=10.0)
    
    env.display_weather_data()
