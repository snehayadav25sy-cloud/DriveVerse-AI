"""
scenario_translator.py — Build 3.7: Scenario Translator
=========================================================
Translates country / city / road_type on a ScenarioConfig to a CARLA
map name (Town01 / Town02 / Town03) with a confidence score and source
tag so downstream components know how certain the mapping is.

Priority order:
  1. cfg.carla_map already set to a known Town → confidence 1.0, source 'explicit'
  2. city  → CITY_TO_CARLA_MAP              → confidence 0.85, source 'city_lookup'
  3. road_type → ROAD_TYPE_TO_CARLA_MAP     → confidence 0.70, source 'road_type_fallback'
  4. default Town01                          → confidence 0.30, source 'default'

Also exposes ALL_MAP_ENTRIES consumed by GET /prompt/maps.
"""

from __future__ import annotations

from app.schemas.scenario import ScenarioConfig, TranslationResult


# ── Lookup tables ─────────────────────────────────────────────────────────────

CITY_TO_CARLA_MAP: dict[str, str] = {
    "tokyo":    "Town03",
    "dubai":    "Town01",
    "bangkok":  "Town01",
    "london":   "Town01",
    "new york": "Town03",
    "berlin":   "Town03",
    "paris":    "Town01",
    "bahrain":  "Town01",
    "mumbai":   "Town01",
    "shanghai": "Town03",
    "sydney":   "Town02",
}

ROAD_TYPE_TO_CARLA_MAP: dict[str, str] = {
    "City":        "Town01",
    "Intersection":"Town01",
    "Urban":       "Town01",
    "Residential": "Town02",
    "Suburban":    "Town02",
    "Rural":       "Town02",
    "Highway":     "Town03",
    "Motorway":    "Town03",
    "Parking":     "Town02",
}

_KNOWN_TOWNS = {"Town01", "Town02", "Town03"}

# Used by GET /prompt/maps
ALL_MAP_ENTRIES: list[dict] = [
    {"city": "Tokyo",    "country": "Japan",     "carla_map": "Town03", "note": "Dense urban/highway"},
    {"city": "Dubai",    "country": "UAE",        "carla_map": "Town01", "note": "City / downtown"},
    {"city": "Bangkok",  "country": "Thailand",   "carla_map": "Town01", "note": "City / urban"},
    {"city": "London",   "country": "UK",         "carla_map": "Town01", "note": "City / urban"},
    {"city": "New York", "country": "USA",        "carla_map": "Town03", "note": "Dense urban/highway"},
    {"city": "Berlin",   "country": "Germany",    "carla_map": "Town03", "note": "Mixed urban/highway"},
    {"city": "Paris",    "country": "France",     "carla_map": "Town01", "note": "City / urban"},
    {"city": "Bahrain",  "country": "Bahrain",    "carla_map": "Town01", "note": "City / downtown"},
    {"city": "Mumbai",   "country": "India",      "carla_map": "Town01", "note": "Dense city"},
    {"city": "Shanghai", "country": "China",      "carla_map": "Town03", "note": "Dense urban/highway"},
    {"city": "Sydney",   "country": "Australia",  "carla_map": "Town02", "note": "Suburban / residential"},
]


# ── Public API ────────────────────────────────────────────────────────────────

def translate_scenario(cfg: ScenarioConfig) -> TranslationResult:
    """
    Resolve a CARLA map for *cfg* and attach the result.

    Mutates *cfg* in-place:
      - cfg.carla_map   → resolved map string
      - cfg.translation → TranslationResult

    Returns the TranslationResult.
    """
    carla_map: str
    confidence: float
    source: str
    note: str = ""

    # 1. Explicit map already set
    if cfg.carla_map and cfg.carla_map in _KNOWN_TOWNS:
        carla_map  = cfg.carla_map
        confidence = 1.0
        source     = "explicit"
        note       = f"Map explicitly set to {carla_map}"

    # 2. City lookup
    elif cfg.city and cfg.city.lower() in CITY_TO_CARLA_MAP:
        carla_map  = CITY_TO_CARLA_MAP[cfg.city.lower()]
        confidence = 0.85
        source     = "city_lookup"
        note       = f"Mapped from city '{cfg.city}'"

    # 3. Road-type fallback
    elif cfg.road_type and cfg.road_type in ROAD_TYPE_TO_CARLA_MAP:
        carla_map  = ROAD_TYPE_TO_CARLA_MAP[cfg.road_type]
        confidence = 0.70
        source     = "road_type_fallback"
        note       = f"Mapped from road_type '{cfg.road_type}'"

    # 4. Default
    else:
        carla_map  = "Town01"
        confidence = 0.30
        source     = "default"
        note       = "No city or road_type matched; defaulting to Town01"

    result = TranslationResult(
        carla_map=carla_map,
        confidence=confidence,
        source=source,
        note=note,
    )

    # Mutate cfg in-place
    cfg.carla_map  = carla_map
    cfg.translation = result

    return result
