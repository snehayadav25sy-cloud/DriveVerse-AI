import random
from typing import Dict, List, Tuple
from app.country_profiles.defaults import DEFAULT_BLUEPRINT_MAP, DEFAULT_ASSET_MAP

class BlueprintResolver:
    def __init__(self, custom_blueprint_map: Dict[str, List[str]] = None):
        self.blueprint_map = custom_blueprint_map or DEFAULT_BLUEPRINT_MAP

    def resolve_vehicle_class(self, vehicle_class: str) -> Tuple[List[str], bool, str]:
        """
        Resolves a semantic vehicle class to a list of CARLA blueprint IDs.
        Returns: (blueprints, renderable, warning_message)
        """
        # Clean the key
        cls_key = vehicle_class.lower().strip()
        
        # Exact match check
        if cls_key in self.blueprint_map and self.blueprint_map[cls_key]:
            return self.blueprint_map[cls_key], True, ""
            
        # Specific semantic fallbacks
        if cls_key == "auto_rickshaw":
            # auto_rickshaw -> microlino fallback
            return self.blueprint_map["micro"], False, "No CARLA asset exists for 'auto_rickshaw'; using microlino (vehicle.micro.microlino) as visual stand-in"
        elif cls_key == "rickshaw":
            return self.blueprint_map["micro"], False, "No CARLA asset exists for 'rickshaw'; using microlino (vehicle.micro.microlino) as visual stand-in"
        elif cls_key == "suv":
            # If no custom SUV mapping but we have default
            if "suv" in self.blueprint_map:
                return self.blueprint_map["suv"], True, ""
        elif cls_key in ["minibus", "double_decker_bus"]:
            return self.blueprint_map["bus"], False, f"No specialized asset for '{cls_key}'; using generic bus (vehicle.mitsubishi.fusorosa) as fallback"
        elif cls_key in ["delivery_van", "cargo_van"]:
            return self.blueprint_map["van"], True, ""
        elif cls_key == "hgv":
            return self.blueprint_map["hgv"], True, ""
            
        # Universal fallback to sedan
        return self.blueprint_map["sedan"], False, f"No blueprint mapping for '{vehicle_class}'; falling back to generic sedan"

    def resolve_blueprint_mix(self, vehicle_mix: Dict[str, float]) -> Tuple[Dict[str, float], List[str]]:
        """
        Translates a mix of semantic classes (e.g. {"sedan": 0.6, "auto_rickshaw": 0.4})
        to a mix of exact blueprint IDs, tracking fallback warnings.
        """
        blueprint_mix = {}
        warnings = []
        
        # Calculate total weight to normalize
        total_weight = sum(vehicle_mix.values())
        if total_weight <= 0:
            return {}, ["Empty vehicle mix provided"]
            
        for sem_class, weight in vehicle_mix.items():
            bps, renderable, warn = self.resolve_vehicle_class(sem_class)
            if warn:
                warnings.append(warn)
                
            # Distribute weight equally among possible blueprints for this class
            share = (weight / total_weight) / len(bps)
            for bp in bps:
                blueprint_mix[bp] = blueprint_mix.get(bp, 0.0) + share
                
        return blueprint_mix, warnings

class AssetResolver:
    def __init__(self, custom_asset_map: Dict[str, List[str]] = None):
        self.asset_map = custom_asset_map or DEFAULT_ASSET_MAP

    def resolve_building_tag(self, osm_tag: str) -> List[str]:
        """
        Maps an OSM building tag to generic static mesh categories.
        """
        tag_key = osm_tag.lower().strip()
        if tag_key in self.asset_map:
            return self.asset_map[tag_key]
        return ["Static.Building.Generic"]
