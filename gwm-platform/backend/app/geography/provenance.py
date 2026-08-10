"""
app/geography/provenance.py — Build 5: Geography pipeline provenance

Records full provenance for a geographic map build:
  - location_query, radius, geocoder/OSM provider names
  - resolved coordinates, country, city, bbox
  - OSM file path, size, timestamp, source hash
  - road graph node/edge counts, graph hash
  - OpenDRIVE hash, compiler version, schema version
  - country profile version, CARLA version
  - git commit, random seed, fallbacks, warnings, errors

The provenance record is deterministic: re-running the identical
pipeline with identical inputs must produce matching hashes.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from typing import Any, Dict, List, Optional

from app.geography.models import MapProvenance


def _get_git_commit() -> str:
    """Return current git commit hash, or 'unknown' if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        return result.stdout.strip()[:12]
    except Exception:
        return "unknown"


def compute_map_provenance(
    *,
    location_query: str,
    radius_m: float,
    geocoder_provider: str,
    osm_provider: str,
    resolved_latitude: Optional[float] = None,
    resolved_longitude: Optional[float] = None,
    resolved_country: Optional[str] = None,
    resolved_city: Optional[str] = None,
    bbox: Optional[Dict[str, float]] = None,
    osm_file_path: Optional[str] = None,
    osm_file_size_bytes: int = 0,
    osm_timestamp: Optional[str] = None,
    osm_source_hash: Optional[str] = None,
    road_graph_node_count: int = 0,
    road_graph_edge_count: int = 0,
    road_graph_hash: Optional[str] = None,
    xodr_hash: Optional[str] = None,
    compiler_version: str = "1.0.0",
    schema_version: str = "1.0.0",
    country_profile_version: Optional[str] = None,
    carla_version: str = "0.9.16",
    random_seed: Optional[int] = None,
    fallbacks: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
) -> MapProvenance:
    """
    Build a MapProvenance record from pipeline stage outputs.
    """
    return MapProvenance(
        location_query=location_query,
        radius_m=radius_m,
        geocoder_provider=geocoder_provider,
        osm_provider=osm_provider,
        resolved_latitude=resolved_latitude,
        resolved_longitude=resolved_longitude,
        resolved_country=resolved_country,
        resolved_city=resolved_city,
        bbox=bbox,
        osm_file_path=osm_file_path,
        osm_file_size_bytes=osm_file_size_bytes,
        osm_timestamp=osm_timestamp,
        osm_source_hash=osm_source_hash,
        road_graph_node_count=road_graph_node_count,
        road_graph_edge_count=road_graph_edge_count,
        road_graph_hash=road_graph_hash,
        xodr_hash=xodr_hash,
        compiler_version=compiler_version,
        schema_version=schema_version,
        country_profile_version=country_profile_version,
        carla_version=carla_version,
        git_commit=_get_git_commit(),
        random_seed=random_seed,
        fallbacks=fallbacks or [],
        warnings=warnings or [],
        errors=errors or [],
    )


def provenance_hash(prov: MapProvenance) -> str:
    """Deterministic hash of a provenance record for reproducibility checks."""
    payload = prov.model_dump(exclude={"git_commit", "provenance_hash"})
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
