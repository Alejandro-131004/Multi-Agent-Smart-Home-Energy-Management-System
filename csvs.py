import pandas as pd

def get_cleaned_energy_data():
    df_energy = pd.read_csv('energy_dataset.csv')
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
    df_energy_cleaned = df_energy.drop(columns=irrelevant_columns, errors='ignore')
    return df_energy_cleaned

def get_cleaned_weather_data():
    df_weather = pd.read_csv('weather_features.csv')
    irrelevant_columns_weather = [
        'rain_1h', 
        'rain_3h', 
        'snow_3h', 
        'weather_id', 
        'weather_icon'
    ]
    df_weather_cleaned = df_weather.drop(columns=irrelevant_columns_weather, errors='ignore')
    return df_weather_cleaned
