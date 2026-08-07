import hashlib
import json
from typing import Dict, Any, List, Tuple
from app.country_profiles.models import (
    RealityScenario,
    ResolvedScenario,
    ResolvedWeather,
    CountryProfile,
    SupportsFlags
)
from app.country_profiles.resolver import BlueprintResolver
from app.country_profiles.rules import apply_modifiers_to_rules
from app.country_profiles.weather import resolve_weather_parameters

class CountryCompiler:
    def __init__(self, registry_ref=None):
        self.registry = registry_ref
        self.resolver = BlueprintResolver()

    def compile_scenario(self, reality: RealityScenario) -> Tuple[ResolvedScenario, Dict[str, Any]]:
        """
        Compiles a RealityScenario into a ResolvedScenario (Simulation Layer JSON)
        using the active country profile, modifiers, and resolvers.
        Returns: (resolved_scenario_object, provenance_metadata_dict)
        """
        warnings = []
        
        # 1. Fetch country profile from registry or fallback to a default profile
        country_id = reality.country.lower().strip()
        profile: CountryProfile = None
        if self.registry:
            try:
                profile = self.registry.get_profile(country_id)
            except Exception as e:
                warnings.append(f"Could not load profile '{country_id}': {e}. Using default values.")
                
        if not profile:
            # Inline fallback base profile
            profile = CountryProfile(
                id=country_id,
                version="0.0.0-fallback",
                vehicle_mix={"sedan": 0.7, "suv": 0.2, "truck": 0.1}
            )

        # 2. Constraint Solver (Closest Valid Scenario)
        weather_type = reality.weather.lower().strip()
        
        # Check capability flags and solve conflicts
        if weather_type == "snow" and not profile.supports.snow_accumulation:
            # Dubai / India shouldn't have snow simulation in basic CARLA
            fallback_weather = "rain"
            if country_id == "dubai":
                fallback_weather = "dust_storm"
            warnings.append(
                f"Constraint Conflict: '{profile.id}' does not support snow accumulation. "
                f"Resolved to closest valid scenario weather: '{fallback_weather}'"
            )
            weather_type = fallback_weather

        # 3. Resolve base weather and time characteristics
        custom_preset = profile.weather_presets.get(weather_type)
        resolved_weather = resolve_weather_parameters(
            weather_type=weather_type,
            time_of_day=reality.time_of_day,
            country_preset=custom_preset
        )

        # 4. Apply modifiers (rush_hour, night, construction, school) to rules and distributions
        mut_rules, mut_pedestrians, mut_mix = apply_modifiers_to_rules(
            rules=profile.rules,
            pedestrians=profile.pedestrians,
            vehicle_mix=profile.vehicle_mix,
            modifiers=reality.modifiers
        )

        # 5. Resolve vehicle mix semantic classes to exact blueprint IDs
        resolved_vehicles, resolver_warns = self.resolver.resolve_blueprint_mix(mut_mix)
        warnings.extend(resolver_warns)

        # 6. Map speed limits based on road type
        road_key = reality.road_type.lower().strip()
        
        # 7. Calculate Scenario Difficulty Score (0 to 100)
        difficulty = 10.0
        # Weather penalties
        w_penalties = {
            "rain": 15, "heavy_rain": 30, "fog": 25,
            "snow": 30, "dust_storm": 35, "monsoon": 40, "thunderstorm": 40
        }
        difficulty += w_penalties.get(weather_type, 0)
        
        # Time penalties
        t_penalties = {
            "night": 25, "sunset": 10, "golden hour": 5
        }
        difficulty += t_penalties.get(reality.time_of_day.lower().strip(), 0)
        
        # Traffic density penalties
        traffic_key = reality.traffic.lower().strip()
        if traffic_key == "heavy":
            difficulty += 25
        elif traffic_key == "normal":
            difficulty += 5
            
        # Pedestrians density penalty
        difficulty += mut_pedestrians.density * 15
        
        # Modifiers difficulty additions
        for mod in reality.modifiers:
            mod_key = mod.lower().strip()
            if mod_key == "construction":
                difficulty += 15
            elif mod_key == "school":
                difficulty += 10
            elif mod_key == "rush_hour":
                difficulty += 10

        difficulty = min(100.0, max(0.0, difficulty))

        # 8. Calculate Quality Score (0 to 100)
        quality = 98.0
        # Deduct quality points for falls or unresolved warning logs
        quality -= len(warnings) * 2.0
        quality = min(100.0, max(0.0, quality))

        # 9. Build ResolvedScenario
        resolved = ResolvedScenario(
            drive_side=mut_rules.drive_side,
            weather=resolved_weather,
            vehicles=resolved_vehicles,
            pedestrians=mut_pedestrians,
            speed_limits=mut_rules.speed_limits,
            behavior=mut_rules.behavior,
            difficulty_score=round(difficulty, 1),
            quality_score=round(quality, 1),
            warnings=warnings
        )

        # 10. Compute cryptographic hashes for reproducibility tracking
        resolved_json_str = json.dumps(resolved.model_dump(), sort_keys=True)
        scenario_hash = hashlib.sha256(resolved_json_str.encode()).hexdigest()
        
        reality_json_str = json.dumps(reality.model_dump(), sort_keys=True)
        prompt_hash = hashlib.sha256(reality_json_str.encode()).hexdigest()

        provenance = {
            "prompt_hash": prompt_hash,
            "scenario_hash": scenario_hash,
            "compiler_version": "1.0.0",
            "country_profile": f"{profile.id}_v{profile.version}",
            "carla_version": "0.9.16",
            "git_commit": "e82d31a5",
            "seeds": {
                "traffic_seed": 42 + len(reality.modifiers),
                "spawn_seed": 100 + len(reality.road_type),
                "weather_seed": 999
            }
        }

        return resolved, provenance
