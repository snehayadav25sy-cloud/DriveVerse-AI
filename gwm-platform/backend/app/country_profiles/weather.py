from app.country_profiles.models import ResolvedWeather, WeatherPreset

# Maps high-level weather terms to ResolvedWeather objects
WEATHER_PRESETS = {
    "sunny": ResolvedWeather(
        precipitation=0.0,
        cloudiness=0.0,
        precipitation_deposits=0.0,
        wind_intensity=0.0,
        fog_density=0.0,
        fog_distance=100.0,
        sun_altitude_angle=45.0,
        sun_azimuth_angle=0.0,
        wetness=0.0
    ),
    "cloudy": ResolvedWeather(
        precipitation=0.0,
        cloudiness=75.0,
        precipitation_deposits=0.0,
        wind_intensity=10.0,
        fog_density=0.0,
        fog_distance=100.0,
        sun_altitude_angle=35.0,
        sun_azimuth_angle=0.0,
        wetness=0.0
    ),
    "rain": ResolvedWeather(
        precipitation=40.0,
        cloudiness=80.0,
        precipitation_deposits=25.0,
        wind_intensity=20.0,
        fog_density=5.0,
        fog_distance=80.0,
        sun_altitude_angle=20.0,
        sun_azimuth_angle=0.0,
        wetness=30.0
    ),
    "heavy_rain": ResolvedWeather(
        precipitation=80.0,
        cloudiness=95.0,
        precipitation_deposits=70.0,
        wind_intensity=50.0,
        fog_density=15.0,
        fog_distance=50.0,
        sun_altitude_angle=15.0,
        sun_azimuth_angle=0.0,
        wetness=80.0
    ),
    "fog": ResolvedWeather(
        precipitation=0.0,
        cloudiness=60.0,
        precipitation_deposits=0.0,
        wind_intensity=2.0,
        fog_density=70.0,
        fog_distance=15.0,
        sun_altitude_angle=25.0,
        sun_azimuth_angle=0.0,
        wetness=10.0
    ),
    "snow": ResolvedWeather(
        precipitation=0.0,
        cloudiness=90.0,
        precipitation_deposits=50.0,  # snow deposits
        wind_intensity=30.0,
        fog_density=10.0,
        fog_distance=40.0,
        sun_altitude_angle=12.0,
        sun_azimuth_angle=0.0,
        wetness=0.0  # cold/frozen
    ),
    "dust_storm": ResolvedWeather(
        precipitation=0.0,
        cloudiness=50.0,
        precipitation_deposits=0.0,
        wind_intensity=80.0,
        fog_density=40.0,       # simulated dust fog
        fog_distance=20.0,
        sun_altitude_angle=30.0,
        sun_azimuth_angle=0.0,
        wetness=0.0
    ),
    "thunderstorm": ResolvedWeather(
        precipitation=90.0,
        cloudiness=100.0,
        precipitation_deposits=80.0,
        wind_intensity=80.0,
        fog_density=20.0,
        fog_distance=30.0,
        sun_altitude_angle=10.0,
        sun_azimuth_angle=0.0,
        wetness=90.0
    ),
    "monsoon": ResolvedWeather(
        precipitation=95.0,
        cloudiness=100.0,
        precipitation_deposits=90.0,
        wind_intensity=65.0,
        fog_density=25.0,
        fog_distance=25.0,
        sun_altitude_angle=15.0,
        sun_azimuth_angle=0.0,
        wetness=100.0
    )
}

# Sun altitude mapping for time of day labels
TIME_ALTITUDES = {
    "morning": 20.0,
    "noon": 75.0,
    "sunset": 5.0,
    "night": -60.0,
    "golden hour": 10.0
}

def resolve_weather_parameters(
    weather_type: str,
    time_of_day: str,
    country_preset: WeatherPreset = None
) -> ResolvedWeather:
    """
    Resolves higher-level weather and time labels to concrete CARLA-friendly coordinates.
    Allows injecting custom WeatherPresets from country profiles.
    """
    w_key = weather_type.lower().strip()
    t_key = time_of_day.lower().strip()
    
    # Grab base weather config
    if country_preset:
        base_weather = ResolvedWeather(
            precipitation=country_preset.rain,
            cloudiness=country_preset.cloudiness,
            precipitation_deposits=country_preset.wetness * 0.8,
            wind_intensity=country_preset.wind,
            fog_density=country_preset.fog,
            fog_distance=30.0 if country_preset.fog > 20 else 100.0,
            sun_altitude_angle=country_preset.sun_altitude,
            sun_azimuth_angle=country_preset.sun_azimuth,
            wetness=country_preset.wetness
        )
    elif w_key in WEATHER_PRESETS:
        # Clone default
        base_weather = ResolvedWeather(**WEATHER_PRESETS[w_key].model_dump())
    else:
        # Fallback to sunny
        base_weather = ResolvedWeather(**WEATHER_PRESETS["sunny"].model_dump())
        
    # Map time altitude
    if t_key in TIME_ALTITUDES:
        base_weather.sun_altitude_angle = TIME_ALTITUDES[t_key]
        if t_key == "sunset":
            base_weather.sun_azimuth_angle = 180.0
        elif t_key == "golden hour":
            base_weather.sun_azimuth_angle = 200.0
            
    # Under night weather conditions, drop sun below horizon if not set
    if t_key == "night":
        base_weather.sun_altitude_angle = -60.0
        
    return base_weather
