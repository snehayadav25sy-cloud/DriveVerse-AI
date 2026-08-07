"""
app/simulators/carla/carla_weather.py — Build 6: CARLA weather application
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


def apply_weather(world, weather_params: Dict[str, float]) -> None:
    if not _CARLA_AVAILABLE:
        logger.warning("CARLA not available, cannot apply weather")
        return
    try:
        weather = _carla.WeatherParameters(
            cloudiness=float(weather_params.get("cloudiness", 0.0)),
            precipitation=float(weather_params.get("precipitation", 0.0)),
            precipitation_deposits=float(weather_params.get("precipitation_deposits", 0.0)),
            wind_intensity=float(weather_params.get("wind_intensity", 0.0)),
            fog_density=float(weather_params.get("fog_density", 0.0)),
            fog_distance=float(weather_params.get("fog_distance", 100.0)),
            sun_azimuth_angle=float(weather_params.get("sun_azimuth_angle", 0.0)),
            sun_altitude_angle=float(weather_params.get("sun_altitude_angle", 45.0)),
            wetness=float(weather_params.get("wetness", 0.0)),
        )
        world.set_weather(weather)
        logger.info(f"Applied weather: precipitation={weather.precipitation}, fog={weather.fog_density}")
    except Exception as e:
        logger.error(f"Failed to apply weather: {e}")
