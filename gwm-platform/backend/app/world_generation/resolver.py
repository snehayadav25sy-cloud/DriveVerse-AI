"""
app/world_generation/resolver.py — Build 6: Semantic Asset Resolver

Maps semantic asset classes to simulator-specific asset candidate lists.

Design:
  - No CARLA imports here.
  - Returns AssetReference objects with explicit fallback chains.
  - Never silently substitutes an asset.
  - Records fallback reasons for every non-exact match.

The actual CARLA blueprint lookup happens in the CARLA adapter layer.
This module only defines the semantic -> candidate mapping and fallback rules.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from app.world_generation.models import AssetReference


# ── Semantic asset registry ──────────────────────────────────────────────
# Maps semantic classes to ordered lists of candidate asset identifiers.
# The first candidate is the preferred (exact) match.
# Subsequent candidates are fallbacks.

SEMANTIC_ASSET_REGISTRY: Dict[str, Dict[str, List[str]]] = {
    # Buildings
    "building": {
        "residential": ["static.prop.house_01", "static.prop.house_02", "static.prop.building_generic"],
        "commercial": ["static.prop.office_01", "static.prop.building_generic"],
        "industrial": ["static.prop.warehouse_01", "static.prop.building_generic"],
        "education": ["static.prop.school_01", "static.prop.building_generic"],
        "religious": ["static.prop.church_01", "static.prop.building_generic"],
        "government": ["static.prop.building_generic"],
        "retail": ["static.prop.shop_01", "static.prop.building_generic"],
        "hospital": ["static.prop.hospital_01", "static.prop.building_generic"],
    },
    # Vegetation
    "vegetation": {
        "tree": ["static.prop.tree_01", "static.prop.tree_02", "static.prop.tree_generic"],
        "palm": ["static.prop.palm_01", "static.prop.tree_generic"],
        "bush": ["static.prop.bush_01", "static.prop.vegetation_generic"],
        "grass": ["static.prop.grass_01", "static.prop.vegetation_generic"],
    },
    # Street furniture
    "street_furniture": {
        "lamp_post": ["static.prop.lamp_post_01", "static.prop.lamp_post_02"],
        "barrier": ["static.prop.barrier_01", "static.prop.barrier_generic"],
        "bollard": ["static.prop.bollard_01", "static.prop.bollard_generic"],
        "bench": ["static.prop.bench_01", "static.prop.bench_generic"],
        "parking_meter": ["static.prop.parking_meter_01", "static.prop.parking_meter_generic"],
        "trash_bin": ["static.prop.trash_bin_01", "static.prop.trash_bin_generic"],
        "guard_rail": ["static.prop.guard_rail_01", "static.prop.guard_rail_generic"],
    },
    # Signs
    "sign": {
        "stop": ["static.prop.stop_sign_01", "static.prop.traffic_sign_generic"],
        "speed_limit": ["static.prop.speed_limit_01", "static.prop.traffic_sign_generic"],
        "yield": ["static.prop.yield_sign_01", "static.prop.traffic_sign_generic"],
        "pedestrian_crossing": ["static.prop.crossing_sign_01", "static.prop.traffic_sign_generic"],
        "traffic_light_ahead": ["static.prop.traffic_light_ahead_01", "static.prop.traffic_sign_generic"],
    },
    # Traffic lights
    "traffic_light": {
        "standard": ["static.prop.traffic_light_01", "static.prop.traffic_light_generic"],
        "pedestrian": ["static.prop.traffic_light_ped_01", "static.prop.traffic_light_generic"],
    },
    # Vehicles
    "vehicle": {
        "sedan": ["vehicle.tesla.model3", "vehicle.audi.a2", "vehicle.vehicle_generic"],
        "suv": ["vehicle.audi.q2", "vehicle.vehicle_generic"],
        "truck": ["vehicle.carlamotors.carlacola", "vehicle.vehicle_generic"],
        "bus": ["vehicle.bus", "vehicle.vehicle_generic"],
        "motorcycle": ["vehicle.harley-davidson.low_rider", "vehicle.vehicle_generic"],
        "bicycle": ["vehicle.bicycle", "vehicle.vehicle_generic"],
        "auto_rickshaw": ["vehicle.auto_rickshaw", "vehicle.vehicle_generic"],  # may not exist in CARLA
    },
    # Pedestrians
    "pedestrian": {
        "adult": ["walker.pedestrian.001", "walker.pedestrian.002", "walker.pedestrian.generic"],
        "child": ["walker.pedestrian.003", "walker.pedestrian.generic"],
        "elderly": ["walker.pedestrian.004", "walker.pedestrian.generic"],
    },
}


class SemanticAssetResolver:
    """
    Resolves semantic asset classes to ordered candidate lists.
    """

    def __init__(self, registry: Optional[Dict[str, Dict[str, List[str]]]] = None):
        self.registry = registry or SEMANTIC_ASSET_REGISTRY

    def resolve(
        self,
        semantic_category: str,
        semantic_subtype: str = "",
        asset_seed: int = 0,
    ) -> AssetReference:
        """
        Resolve a semantic class to an AssetReference.

        Returns:
          AssetReference with:
            - semantic_class: the requested category
            - semantic_subtype: the requested subtype
            - resolved_asset_id: the first candidate (preferred)
            - fallback_chain: remaining candidates
            - is_fallback: True if the preferred was not available
            - fallback_reason: documented reason if fallback occurred
        """
        category = (semantic_category or "").lower().strip()
        subtype = (semantic_subtype or "").lower().strip()

        candidates = self._lookup(category, subtype)
        if not candidates:
            return AssetReference(
                semantic_class=category,
                semantic_subtype=subtype,
                resolved_asset_id="unknown",
                fallback_chain=[],
                is_fallback=True,
                fallback_reason=f"no_candidates_for_{category}",
            )

        preferred = candidates[0]
        fallbacks = candidates[1:]
        is_fallback = False
        fallback_reason = None

        # If the preferred asset contains "generic", it's already a fallback
        if "generic" in preferred.lower():
            is_fallback = True
            fallback_reason = "preferred_asset_unavailable"

        # Deterministic selection from candidates using asset_seed
        if fallbacks:
            selected_idx = asset_seed % len(candidates)
            selected = candidates[selected_idx]
            remaining = [c for i, c in enumerate(candidates) if i != selected_idx]
            if selected != preferred:
                is_fallback = True
                fallback_reason = f"seeded_selection_fallback (seed={asset_seed}, selected={selected}, preferred={preferred})"
            return AssetReference(
                semantic_class=category,
                semantic_subtype=subtype,
                resolved_asset_id=selected,
                fallback_chain=remaining,
                is_fallback=is_fallback,
                fallback_reason=fallback_reason,
            )

        return AssetReference(
            semantic_class=category,
            semantic_subtype=subtype,
            resolved_asset_id=preferred,
            fallback_chain=[],
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
        )

    def resolve_batch(
        self,
        requests: List[Dict[str, str]],
        asset_seed: int = 0,
    ) -> List[AssetReference]:
        """
        Resolve multiple asset requests.
        """
        results = []
        for i, req in enumerate(requests):
            seed = asset_seed + i
            ref = self.resolve(
                semantic_category=req.get("category", ""),
                semantic_subtype=req.get("subtype", ""),
                asset_seed=seed,
            )
            results.append(ref)
        return results

    def _lookup(self, category: str, subtype: str) -> List[str]:
        """Look up candidates from registry."""
        if category in self.registry:
            cat_map = self.registry[category]
            if subtype and subtype in cat_map:
                return cat_map[subtype]
            # Fallback to first subtype in category
            if cat_map:
                return list(cat_map.values())[0]
        return []

    def asset_registry_hash(self) -> str:
        """Deterministic hash of the asset registry."""
        raw = json.dumps(self.registry, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
