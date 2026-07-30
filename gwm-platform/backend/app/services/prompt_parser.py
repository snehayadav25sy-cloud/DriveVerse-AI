"""
prompt_parser.py — Build 3.1: Scenario JSON Engine (Regex Provider)
====================================================================
Rule-based NLP parser that converts free-text scenario descriptions into
a full ScenarioConfig — the central contract for the AI Prompt Engine.

This is the RegexProvider implementation of the LLMProvider interface
(defined in Build 3.6). It runs without any external API key.
"""

from __future__ import annotations

import re
from typing import Any

from app.schemas.scenario import ScenarioConfig, VehicleMix


# ── Vocabulary tables ─────────────────────────────────────────────────────────

# Map aliases  →  canonical CARLA map
_MAP_ALIASES: dict[str, str] = {
    # Town01 — urban / city / intersection
    "town01": "Town01", "town 01": "Town01", "town1": "Town01", "town 1": "Town01",
    "city": "Town01", "urban": "Town01", "downtown": "Town01", "intersection": "Town01",
    "junction": "Town01",
    # Town02 — suburban / residential
    "town02": "Town02", "town 02": "Town02", "town2": "Town02", "town 2": "Town02",
    "suburb": "Town02", "suburban": "Town02", "residential": "Town02",
    "neighbourhood": "Town02", "neighborhood": "Town02",
    # Town03 — highway / motorway / rural
    "town03": "Town03", "town 03": "Town03", "town3": "Town03", "town 3": "Town03",
    "highway": "Town03", "motorway": "Town03", "freeway": "Town03",
    "rural": "Town03", "countryside": "Town03", "open road": "Town03",
    "autobahn": "Town03",
}

# Sensor aliases  →  canonical sensor key
_SENSOR_ALIASES: dict[str, str] = {
    "rgb": "rgb", "camera": "rgb", "colour": "rgb", "color": "rgb",
    "visual": "rgb", "image": "rgb", "photo": "rgb",
    "lidar": "lidar", "laser": "lidar", "pointcloud": "lidar", "point cloud": "lidar",
    "radar": "radar", "radio": "radar",
    "depth": "depth", "depth camera": "depth", "stereo": "depth",
    "semantic": "semantic", "semantic segmentation": "semantic", "segmentation": "semantic",
    "instance": "instance", "instance segmentation": "instance",
    "optical_flow": "optical_flow", "optical flow": "optical_flow", "flow": "optical_flow",
}

# Sensor bundles
_SENSOR_BUNDLES: dict[str, list[str]] = {
    "full sensor suite": ["rgb", "lidar", "radar", "depth", "semantic"],
    "full suite":        ["rgb", "lidar", "radar", "depth", "semantic"],
    "all sensors":       ["rgb", "lidar", "radar", "depth", "semantic", "instance", "optical_flow"],
    "multi modal":       ["rgb", "lidar", "radar"],
    "multimodal":        ["rgb", "lidar", "radar"],
    "stereo lidar":      ["rgb", "lidar"],
    "rgb lidar":         ["rgb", "lidar"],
    "camera lidar":      ["rgb", "lidar"],
    "vision only":       ["rgb"],
    "camera only":       ["rgb"],
    "lidar only":        ["lidar"],
    "radar only":        ["radar"],
    "basic":             ["rgb"],
    "standard":          ["rgb", "lidar"],
    "advanced":          ["rgb", "lidar", "radar", "depth"],
}

# Export format aliases
_FORMAT_ALIASES: dict[str, str] = {
    "kitti": "kitti", "kitti format": "kitti",
    "coco": "coco", "coco json": "coco",
    "nuscenes": "nuscenes", "nu scenes": "nuscenes", "nuscene": "nuscenes",
    "nusc": "nuscenes",
}

# Weather aliases
_WEATHER_ALIASES: dict[str, str] = {
    "clear": "Clear", "sunny": "Clear", "sun": "Clear", "dry": "Clear",
    "cloudless": "Clear", "fair": "Clear",
    "rain": "Rain", "rainy": "Rain", "raining": "Rain", "wet": "Rain",
    "drizzle": "Rain", "shower": "Rain", "heavy rain": "Rain",
    "fog": "Fog", "foggy": "Fog", "mist": "Fog", "misty": "Fog",
    "haze": "Fog", "hazy": "Fog",
    "snow": "Snow", "snowy": "Snow", "snowing": "Snow", "blizzard": "Snow",
    "storm": "Storm", "stormy": "Storm", "thunder": "Storm", "lightning": "Storm",
    "overcast": "Overcast", "cloudy": "Overcast", "grey": "Overcast", "gray": "Overcast",
}

# Time of day aliases
_TOD_ALIASES: dict[str, str] = {
    "day": "Day", "daytime": "Day", "noon": "Day", "morning": "Day",
    "afternoon": "Day", "bright": "Day", "daylight": "Day",
    "night": "Night", "nighttime": "Night", "dark": "Night", "midnight": "Night",
    "evening": "Night", "late night": "Night",
    "dusk": "Dusk", "sunset": "Dusk", "twilight": "Dusk",
    "dawn": "Dawn", "sunrise": "Dawn", "early morning": "Dawn",
}

# Traffic density aliases
_TRAFFIC_ALIASES: dict[str, str] = {
    "no traffic": "None", "empty": "None", "no vehicles": "None",
    "light traffic": "Light", "light": "Light", "sparse": "Light", "few cars": "Light",
    "medium traffic": "Medium", "medium": "Medium", "moderate": "Medium",
    "normal traffic": "Medium", "average": "Medium",
    "heavy traffic": "Heavy", "heavy": "Heavy", "busy": "Heavy",
    "congested": "Heavy", "rush hour": "Heavy", "dense": "Heavy",
    "gridlock": "Gridlock", "jam": "Gridlock", "traffic jam": "Gridlock",
}

# Road type aliases
_ROAD_ALIASES: dict[str, str] = {
    "highway": "Highway", "motorway": "Highway", "freeway": "Highway",
    "autobahn": "Highway", "expressway": "Highway",
    "city street": "City", "city": "City", "urban": "City", "downtown": "City",
    "intersection": "Intersection", "junction": "Intersection", "crossroads": "Intersection",
    "roundabout": "Intersection",
    "residential": "Residential", "suburban": "Residential", "suburb": "Residential",
    "rural": "Rural", "countryside": "Rural", "country road": "Rural",
    "dirt road": "Rural", "dirt track": "Rural",
    "parking": "Parking", "car park": "Parking", "parking lot": "Parking",
}

# Country aliases (Build 4 hook — stored but not yet acted upon in simulation)
_COUNTRY_ALIASES: dict[str, str] = {
    "japan": "Japan", "japanese": "Japan", "tokyo": "Japan",
    "uae": "UAE", "dubai": "UAE", "united arab emirates": "UAE", "abu dhabi": "UAE",
    "uk": "UK", "united kingdom": "UK", "britain": "UK", "england": "UK",
    "london": "UK",
    "usa": "USA", "us": "USA", "america": "USA", "new york": "USA",
    "germany": "Germany", "german": "Germany", "berlin": "Germany",
    "france": "France", "paris": "France",
    "thailand": "Thailand", "bangkok": "Thailand", "thai": "Thailand",
    "bahrain": "Bahrain",
    "india": "India", "mumbai": "India", "delhi": "India",
    "china": "China", "shanghai": "China", "beijing": "China",
    "australia": "Australia", "sydney": "Australia", "melbourne": "Australia",
}

# City to carla map hint (for translator pre-seeding)
_CITY_MAP_HINTS: dict[str, str] = {
    "tokyo": "Town03", "dubai": "Town01", "london": "Town01",
    "bangkok": "Town01", "new york": "Town03", "berlin": "Town03",
    "paris": "Town01", "bahrain": "Town01",
}

# Frame patterns
_FRAME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(\d{2,4})\s+frames?", re.I),
    re.compile(r"(\d{2,4})\s*f\b", re.I),
    re.compile(r"capture\s+(\d{2,4})", re.I),
    re.compile(r"record\s+(\d{2,4})", re.I),
    re.compile(r"generate\s+(\d{2,4})", re.I),
    re.compile(r"(\d{2,4})\s+steps?", re.I),
    re.compile(r"(\d{2,4})\s+ticks?", re.I),
    re.compile(r"(\d{1,2})\s*-?\s*second", re.I),  # "30-second" → 300 frames
]

_FRAME_WORD_HINTS: dict[str, int] = {
    "short": 150, "brief": 100, "quick": 100, "small": 200,
    "long": 1000, "extended": 1200, "large": 1500, "full": 2000,
    "medium": 500, "default": 500,
}

# Vehicle count patterns: "100 cars", "30 trucks", "50 pedestrians"
_VEHICLE_PATTERNS: dict[str, re.Pattern[str]] = {
    "car":        re.compile(r"(\d+)\s+cars?", re.I),
    "truck":      re.compile(r"(\d+)\s+trucks?", re.I),
    "bus":        re.compile(r"(\d+)\s+buses?", re.I),
    "motorcycle": re.compile(r"(\d+)\s+motorcycles?", re.I),
    "bicycle":    re.compile(r"(\d+)\s+bicycles?", re.I),
    "van":        re.compile(r"(\d+)\s+vans?", re.I),
}
_PEDESTRIAN_PATTERN = re.compile(r"(\d+)\s+pedestrians?", re.I)


# ── Core parser ───────────────────────────────────────────────────────────────

def parse_prompt(prompt: str) -> ScenarioConfig:
    """
    Convert free-text scenario description → ScenarioConfig.

    This is the RegexProvider implementation.
    The LLMProvider layer (Build 3.6) will swap this with GPT/Gemini/Claude
    while keeping the same ScenarioConfig output contract.
    """
    text  = prompt.strip().lower()
    conf: dict[str, float] = {}
    expl: list[str] = []

    # ── Geography ─────────────────────────────────────────────────────────────
    country  = _match_longest(text, _COUNTRY_ALIASES)
    city     = _extract_city(text)
    road_type = _match_longest(text, _ROAD_ALIASES)
    carla_map_hint = _extract_carla_hint(text, city)

    if country:
        conf["country"] = 1.0
        expl.append(f"Country → {country}")
    if city:
        conf["city"] = 1.0
        expl.append(f"City → {city}")
    if road_type:
        conf["road_type"] = 1.0
        expl.append(f"Road type → {road_type}")

    # ── Map (from explicit Town keyword or road/city hint) ────────────────────
    carla_map = _match_longest(text, _MAP_ALIASES)
    if carla_map:
        conf["carla_map"] = 1.0
        expl.append(f"CARLA map → {carla_map} (direct keyword)")
    elif carla_map_hint:
        carla_map = carla_map_hint
        conf["carla_map"] = 0.7
        expl.append(f"CARLA map → {carla_map} (inferred from city/road type)")

    # ── Environment ───────────────────────────────────────────────────────────
    weather    = _match_longest(text, _WEATHER_ALIASES)
    time_of_day = _match_longest(text, _TOD_ALIASES)

    if weather:
        conf["weather"] = 1.0; expl.append(f"Weather → {weather}")
    if time_of_day:
        conf["time_of_day"] = 1.0; expl.append(f"Time of day → {time_of_day}")

    # ── Traffic ──────────────────────────────────────────────────────────────
    traffic_density = _match_longest(text, _TRAFFIC_ALIASES)
    if traffic_density:
        conf["traffic_density"] = 1.0; expl.append(f"Traffic → {traffic_density}")

    # Vehicle counts
    vehicles = VehicleMix()
    for field, pat in _VEHICLE_PATTERNS.items():
        m = pat.search(text)
        if m:
            setattr(vehicles, field, int(m.group(1)))
            expl.append(f"vehicles.{field} → {m.group(1)}")

    pedestrians = 0
    pm = _PEDESTRIAN_PATTERN.search(text)
    if pm:
        pedestrians = int(pm.group(1))
        expl.append(f"Pedestrians → {pedestrians}")

    # ── Sensors ───────────────────────────────────────────────────────────────
    detected_sensors: set[str] = set()
    for bundle, sensors in sorted(_SENSOR_BUNDLES.items(), key=lambda kv: -len(kv[0])):
        if bundle in text:
            detected_sensors.update(sensors)
            expl.append(f"Sensors ← bundle '{bundle}': {sensors}")
    for alias, canonical in sorted(_SENSOR_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            detected_sensors.add(canonical)

    sensors = sorted(detected_sensors) if detected_sensors else ["rgb"]
    conf["sensors"] = 1.0 if detected_sensors else 0.0
    if not detected_sensors:
        expl.append("Sensors → ['rgb'] (default — no keyword found)")
    else:
        expl.append(f"Sensors → {sensors}")

    # ── Frames ───────────────────────────────────────────────────────────────
    frames: int | None = None
    for pat in _FRAME_PATTERNS:
        m = pat.search(text)
        if m:
            val = int(m.group(1))
            if "second" in pat.pattern:
                val = val * 10   # 10 FPS
            frames = max(1, min(val, 2000))
            break

    if frames is None:
        for word, count in _FRAME_WORD_HINTS.items():
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                frames = count
                expl.append(f"Frames → {count} (from '{word}')")
                conf["frames"] = 0.6
                break

    if frames is not None and "frames" not in conf:
        conf["frames"] = 1.0
        expl.append(f"Frames → {frames}")
    elif frames is None:
        frames = 500
        conf["frames"] = 0.0
        expl.append("Frames → 500 (default)")

    # ── Export format ─────────────────────────────────────────────────────────
    fmt = _match_longest(text, _FORMAT_ALIASES)
    if fmt:
        conf["export_format"] = 1.0; expl.append(f"Format → {fmt}")
    else:
        fmt = "kitti"
        conf["export_format"] = 0.0; expl.append("Format → kitti (default)")

    # ── Unrecognised tokens ───────────────────────────────────────────────────
    unrecognised = _find_unrecognised(text, [
        _MAP_ALIASES, _SENSOR_ALIASES, _FORMAT_ALIASES,
        _WEATHER_ALIASES, _TOD_ALIASES, _TRAFFIC_ALIASES,
        _ROAD_ALIASES, _COUNTRY_ALIASES,
    ] + [dict.fromkeys(_SENSOR_BUNDLES)] + [dict.fromkeys(_FRAME_WORD_HINTS)])

    return ScenarioConfig(
        country=country,
        city=city,
        road_type=road_type,
        weather=weather,
        time_of_day=time_of_day,
        traffic_density=traffic_density,
        vehicles=vehicles,
        pedestrians=pedestrians,
        sensors=sensors,
        frames=frames,
        export_format=fmt,
        carla_map=carla_map,
        confidence=conf,
        explanation=expl,
        unrecognised_tokens=unrecognised,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _match_longest(text: str, aliases: dict[str, str]) -> str | None:
    """Return the canonical value for the longest alias found in text."""
    for alias, canonical in sorted(aliases.items(), key=lambda kv: -len(kv[0])):
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            return canonical
    return None


def _extract_city(text: str) -> str | None:
    """Extract city name as a display string (Title Case)."""
    for alias, country in sorted(_COUNTRY_ALIASES.items(), key=lambda kv: -len(kv[0])):
        # If the alias looks like a city (not generic word) return it
        if len(alias) > 4 and alias not in {"japan", "france", "germany", "china",
                                              "india", "australia", "bahrain", "thailand"}:
            if re.search(r"\b" + re.escape(alias) + r"\b", text):
                return alias.title()
    return None


def _extract_carla_hint(text: str, city: str | None) -> str | None:
    """Derive carla_map from city name, falling back to road type."""
    if city:
        hint = _CITY_MAP_HINTS.get(city.lower())
        if hint:
            return hint
    # Road-type fallback
    road_map = {
        "highway": "Town03", "motorway": "Town03", "freeway": "Town03",
        "residential": "Town02", "suburban": "Town02", "suburb": "Town02",
        "urban": "Town01", "city": "Town01", "intersection": "Town01",
    }
    for keyword, carla in road_map.items():
        if keyword in text:
            return carla
    return None


def _find_unrecognised(text: str, vocab_list: list[dict]) -> list[str]:
    """Strip known vocabulary and flag remaining content words."""
    cleaned = text
    all_keys: list[str] = []
    for d in vocab_list:
        all_keys.extend(d.keys())
    all_keys += [
        "generate", "dataset", "capture", "record", "simulation", "sim",
        "scenario", "with", "using", "and", "or", "the", "a", "an", "of",
        "for", "in", "on", "at", "frames", "frame", "steps", "step",
        "ticks", "tick", "second", "please", "i", "want", "need",
        "create", "make", "build", "run", "execute", "start",
        "cars", "car", "trucks", "truck", "buses", "bus",
        "motorcycles", "motorcycle", "bicycles", "bicycle", "vans", "van",
        "pedestrians", "pedestrian",
    ]
    for kw in sorted(all_keys, key=len, reverse=True):
        cleaned = re.sub(r"\b" + re.escape(kw) + r"\b", " ", cleaned, flags=re.I)
    remaining = [w for w in re.split(r"\W+", cleaned) if len(w) > 3]
    return list(set(remaining))
