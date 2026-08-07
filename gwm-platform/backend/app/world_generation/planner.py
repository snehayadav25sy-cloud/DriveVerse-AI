"""
app/world_generation/planner.py — Build 6: Procedural World Planner

Receives:
  - ResolvedScenario (Build 4)
  - MapArtifact (Build 5)
  - CountryProfile (Build 4)

Produces:
  - WorldPlan (deterministic, inspectable, reproducible)

Design:
  - No CARLA imports.
  - Deterministic seeds.
  - All asset resolution uses SemanticAssetResolver.
  - All randomization uses DomainRandomizer.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from app.world_generation.models import (
    AssetReference,
    BuildingPlan,
    PedestrianPlan,
    ScenarioEvent,
    SensorConfig,
    SignPlan,
    StreetFurniturePlan,
    TrafficLightPlan,
    VehiclePlan,
    VegetationPlan,
    WorldBoundingBox,
    WorldCoordinate,
    WorldPlan,
    WorldProvenance,
)
from app.world_generation.resolver import SemanticAssetResolver
from app.world_generation.randomization import DomainRandomizer
from app.world_generation.vegetation import VegetationEngine
from app.world_generation.furniture import StreetFurnitureEngine
from app.world_generation.traffic import TrafficSignEngine, TrafficLightEngine
from app.world_generation.vehicles import VehiclePopulationEngine
from app.world_generation.pedestrians import PedestrianPopulationEngine
from app.world_generation.events import ScenarioEventEngine


class WorldPlanner:
    """
    Main procedural world planner.

    Generates a deterministic WorldPlan from scenario, geography, and country inputs.
    """

    def __init__(
        self,
        resolved_scenario: Dict[str, Any],
        map_artifact: Dict[str, Any],
        country_profile: Dict[str, Any],
        asset_registry: Optional[Dict[str, Dict[str, List[str]]]] = None,
    ):
        self.resolved = resolved_scenario
        self.map_artifact = map_artifact
        self.country = country_profile
        self.resolver = SemanticAssetResolver(asset_registry)
        self.world_id = self._generate_world_id()

    def plan(self, seeds: Optional[Dict[str, int]] = None) -> WorldPlan:
        """
        Generate the world plan.
        """
        if seeds is None:
            seeds = {
                "world": random.randint(0, 2**31 - 1),
                "traffic": random.randint(0, 2**31 - 1),
                "pedestrian": random.randint(0, 2**31 - 1),
                "weather": random.randint(0, 2**31 - 1),
                "asset": random.randint(0, 2**31 - 1),
                "scenario": random.randint(0, 2**31 - 1),
            }

        origin = self._origin_from_artifact()
        bbox = self._compute_bounding_box(origin)

        plan = WorldPlan(
            world_id=self.world_id,
            seed=seeds["world"],
            location_query=self.map_artifact.get("location_query", "unknown"),
            country=self.country.get("id", "usa"),
            map_name=self.map_artifact.get("carla_map_name", "Town01"),
            carla_coordinate_origin=origin,
            bounding_box=bbox,
            seeds=dict(seeds),
        )

        # Domain randomizer
        rng = DomainRandomizer(seeds)

        # Buildings
        osm_buildings = self.map_artifact.get("osm_buildings", [])
        building_plans = self._plan_buildings(osm_buildings)
        plan.buildings.extend(building_plans)

        # Vegetation
        veg_engine = VegetationEngine(plan)
        veg_plans = veg_engine.generate(density=0.5, season="summer")
        plan.vegetation.extend(veg_plans)

        # Street furniture
        furn_engine = StreetFurnitureEngine(plan)
        furn_plans = furn_engine.generate(density=0.3)
        plan.street_furniture.extend(furn_plans)

        # Traffic signs
        sign_engine = TrafficSignEngine(plan, self.country)
        sign_plans = sign_engine.generate(density=0.2)
        plan.signs.extend(sign_plans)

        # Traffic lights
        tl_engine = TrafficLightEngine(plan, self.country)
        tl_plans = tl_engine.generate(intersection_count=5)
        plan.traffic_lights.extend(tl_plans)

        # Vehicles
        veh_engine = VehiclePopulationEngine(plan, self.country, self.resolved)
        veh_plans = veh_engine.generate(traffic_density=self.resolved.get("traffic", "normal"))
        plan.vehicles.extend(veh_plans)

        # Pedestrians
        ped_engine = PedestrianPopulationEngine(plan, self.country, self.resolved)
        ped_plans = ped_engine.generate(density=0.3)
        plan.pedestrians.extend(ped_plans)

        # Events
        event_engine = ScenarioEventEngine(plan)
        event_plans = event_engine.generate(event_count=3)
        plan.events.extend(event_plans)

        # Sensors
        sensor_plans = self._plan_sensors(origin)
        plan.sensors.extend(sensor_plans)

        # Weather override
        weather_base = self.resolved.get("weather", {})
        if isinstance(weather_base, dict):
            plan.weather_override = rng.randomize_weather(weather_base)

        # Asset resolution stats
        all_assets = (
            [b.asset for b in plan.buildings if b.asset] +
            [v.asset for v in plan.vegetation if v.asset] +
            [f.asset for f in plan.street_furniture if f.asset] +
            [s.asset for s in plan.signs if s.asset] +
            [tl.asset for tl in plan.traffic_lights if tl.asset]
        )
        exact = sum(1 for a in all_assets if a and not a.is_fallback)
        fallback = sum(1 for a in all_assets if a and a.is_fallback)
        plan.asset_resolution_stats = {"exact": exact, "fallback": fallback}

        return plan

    def provenance(self, plan: WorldPlan) -> WorldProvenance:
        """
        Generate provenance for a world plan.
        """
        return WorldProvenance(
            country_profile_hash=self._hash_dict(self.country),
            geography_hash=self._hash_dict(self.map_artifact),
            world_plan_hash=plan.plan_hash(),
            asset_registry_hash=self.resolver.asset_registry_hash(),
            world_seed=plan.seeds.get("world", 0),
            traffic_seed=plan.seeds.get("traffic", 0),
            pedestrian_seed=plan.seeds.get("pedestrian", 0),
            weather_seed=plan.seeds.get("weather", 0),
            asset_seed=plan.seeds.get("asset", 0),
            scenario_seed=plan.seeds.get("scenario", 0),
        )

    def _generate_world_id(self) -> str:
        raw = f"{self.map_artifact.get('location_query', '')}-{self.country.get('id', '')}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _origin_from_artifact(self) -> WorldCoordinate:
        res = self.map_artifact.get("resolution", {})
        lat = res.get("resolved_latitude", 0.0)
        lon = res.get("resolved_longitude", 0.0)
        return WorldCoordinate(x=float(lon), y=float(lat), z=0.0)

    def _compute_bounding_box(self, origin: WorldCoordinate) -> WorldBoundingBox:
        radius = 250.0
        return WorldBoundingBox(
            min_x=origin.x - radius,
            max_x=origin.x + radius,
            min_y=origin.y - radius,
            max_y=origin.y + radius,
            min_z=0.0,
            max_z=50.0,
        )

    def _plan_buildings(self, osm_buildings: List[Dict[str, Any]]) -> List[BuildingPlan]:
        plans = []
        for i, b in enumerate(osm_buildings[:50]):
            asset = self.resolver.resolve("building", b.get("building", "generic"), asset_seed=i)
            footprint = b.get("geometry", [(0, 0), (10, 0), (10, 10), (0, 10)])
            if isinstance(footprint, list) and len(footprint) > 0 and isinstance(footprint[0], dict):
                footprint = [(p.get("x", 0.0), p.get("y", 0.0)) for p in footprint]
            elif isinstance(footprint, list) and len(footprint) > 0 and isinstance(footprint[0], (tuple, list)):
                footprint = [(float(p[0]), float(p[1])) for p in footprint]
            else:
                footprint = [(0, 0), (10, 0), (10, 10), (0, 10)]

            plan = BuildingPlan(
                building_id=b.get("osm_id", f"b_{i:04d}"),
                semantic_type=asset.semantic_subtype or "generic",
                footprint=footprint,
                height_m=10.0,
                rotation_deg=0.0,
                asset=asset,
                geometry_fidelity="exact" if len(footprint) >= 3 else "approximate",
                source_osm_id=b.get("osm_id"),
            )
            plans.append(plan)
        return plans

    def _plan_sensors(self, origin: WorldCoordinate) -> List[SensorConfig]:
        sensors = []
        # Front RGB
        sensors.append(SensorConfig(
            sensor_id="camera_front",
            sensor_type="rgb",
            position=WorldCoordinate(x=origin.x + 1.5, y=origin.y, z=1.4),
            rotation=(0.0, 0.0, 0.0),
            resolution=(1280, 720),
            fov=90.0,
            intrinsic=None,
            extrinsic=None,
        ))
        return sensors

    def _hash_dict(self, d: Dict[str, Any]) -> str:
        raw = json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
