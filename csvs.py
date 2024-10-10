# Imports needed

import pandas as pd


#--------------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------------#

# Reading the first csv
df_energy = pd.read_csv('energy_dataset.csv')

# Printing to check some information about the csv
print(df_energy.head())

# This are the irrelevant columns, which we are going to drop
irrelevant_columns = [
    'generation biomass',
    'generation fossil brown coal/lignite',
    'generation fossil coal-derived gas',
    'generation fossil gas',
    'generation fossil hard coal',
    'generation fossil oil',
    'generation fossil oil shale',
    'generation fossil peat',
    'generation geothermal',
    'generation hydro pumped storage aggregated',
    'generation hydro pumped storage consumption',
    'generation hydro run-of-river and poundage',
    'generation hydro water reservoir',
    'generation marine',
    'generation nuclear',
    'generation other',
    'generation other renewable',
    'generation waste'
]

# Drop of the irrelevant columns
df_energy_cleaned = df_energy.drop(columns=irrelevant_columns, errors='ignore')

# Printing the cleaned csv
print(df_energy_cleaned.head())

#--------------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------------#

# Reading the second csv
df_weather = pd.read_csv('weather_features.csv')
print(df_weather.head())


# Same goes for this one
irrelevant_columns_weather = [
    'rain_1h', 
    'rain_3h', 
    'snow_3h', 
    'weather_id', 
    'weather_icon'
]

# Drop of the irrelevant columns
df_weather_cleaned = df_weather.drop(columns=irrelevant_columns_weather, errors='ignore')



# Printing the cleaned csv
print(df_weather_cleaned.head())

#--------------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------------#

