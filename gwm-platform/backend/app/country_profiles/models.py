from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class SupportsFlags(BaseModel):
    auto_rickshaw: bool = False
    tram: bool = False
    train: bool = False
    snow_accumulation: bool = False
    deformable_terrain: bool = False

class SpeedLimits(BaseModel):
    highway: int = 100
    urban: int = 50
    residential: int = 40
    school: int = 20

class DriverBehavior(BaseModel):
    aggressiveness: float = 0.5   # 0.0 to 1.0
    horn_frequency: float = 0.1   # 0.0 to 1.0
    stopping_distance_m: float = 3.0
    lane_discipline: float = 0.9  # 0.0 to 1.0

class TrafficRules(BaseModel):
    drive_side: str = "right"  # "left" or "right"
    speed_limits: SpeedLimits = Field(default_factory=SpeedLimits)
    signal_duration_s: int = 30
    behavior: DriverBehavior = Field(default_factory=DriverBehavior)

class WeatherPreset(BaseModel):
    rain: float = 0.0
    cloudiness: float = 0.0
    wind: float = 0.0
    wetness: float = 0.0
    fog: float = 0.0
    sun_altitude: float = 45.0  # degrees
    sun_azimuth: float = 0.0     # degrees

class PedestrianSettings(BaseModel):
    density: float = 0.1      # 0.0 to 1.0
    walking_speed: float = 1.2 # m/s

class CountryProfile(BaseModel):
    id: str
    version: str = "1.0.0"
    schema_version: int = 1
    extends: Optional[str] = None
    author: str = "DriveVerse"
    updated: str = "2026-08-06"
    supports: SupportsFlags = Field(default_factory=SupportsFlags)
    rules: TrafficRules = Field(default_factory=TrafficRules)
    weather_presets: Dict[str, WeatherPreset] = Field(default_factory=dict)
    vehicle_mix: Dict[str, float] = Field(default_factory=dict) # e.g. {"sedan": 0.5, "rickshaw": 0.1}
    pedestrians: PedestrianSettings = Field(default_factory=PedestrianSettings)

class RealityScenario(BaseModel):
    country: str = "usa"
    weather: str = "sunny"
    traffic: str = "normal"      # "low", "normal", "heavy"
    time_of_day: str = "noon"    # "morning", "noon", "sunset", "night", "golden hour"
    road_type: str = "highway"
    modifiers: List[str] = Field(default_factory=list)

class ResolvedWeather(BaseModel):
    precipitation: float = 0.0
    cloudiness: float = 0.0
    precipitation_deposits: float = 0.0
    wind_intensity: float = 0.0
    fog_density: float = 0.0
    fog_distance: float = 100.0
    sun_altitude_angle: float = 45.0
    sun_azimuth_angle: float = 0.0
    wetness: float = 0.0

class ResolvedScenario(BaseModel):
    drive_side: str = "right"
    weather: ResolvedWeather = Field(default_factory=ResolvedWeather)
    vehicles: Dict[str, float] = Field(default_factory=dict)  # resolved blueprint shares
    pedestrians: PedestrianSettings = Field(default_factory=PedestrianSettings)
    speed_limits: SpeedLimits = Field(default_factory=SpeedLimits)
    behavior: DriverBehavior = Field(default_factory=DriverBehavior)
    difficulty_score: float = 0.0
    quality_score: float = 0.0
    warnings: List[str] = Field(default_factory=list)

class Provenance(BaseModel):
    prompt_hash: str = ""
    scenario_hash: str = ""
    compiler_version: str = "1.0.0"
    country_profile: str = ""
    carla_version: str = "0.9.16"
    git_commit: str = "unknown"
    seeds: Dict[str, int] = Field(default_factory=dict)
