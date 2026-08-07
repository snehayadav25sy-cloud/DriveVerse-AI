"""
app/geography/cache.py — Build 5: Geography cache

Storage layout:
  storage/geography/cache/<location_hash>/
    source.json      — raw OSM Overpass response
    metadata.json    — cache key, timestamp, params, schema version

Cache key is a deterministic SHA256 hash of:
  - provider name
  - query parameters (lat, lon, radius, or bbox)
  - schema version

This ensures identical requests hit the same cache entry, and any parameter
change produces a different entry.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Optional


GEOGRAPHY_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "storage",
    "geography",
    "cache",
)

SCHEMA_VERSION = "1.0.0"


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def compute_cache_key(
    provider: str,
    params: Dict[str, Any],
) -> str:
    """
    Compute a deterministic cache key from provider name + query params + schema version.
    """
    payload = {
        "provider": provider,
        "params": params,
        "schema_version": SCHEMA_VERSION,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cache_path(cache_key: str) -> str:
    return os.path.join(GEOGRAPHY_CACHE_DIR, cache_key)


def cache_exists(cache_key: str) -> bool:
    path = get_cache_path(cache_key)
    return os.path.exists(os.path.join(path, "source.json"))


def read_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    path = get_cache_path(cache_key)
    source_path = os.path.join(path, "source.json")
    if not os.path.exists(source_path):
        return None
    with open(source_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_cache(cache_key: str, source_data: Dict[str, Any], params: Dict[str, Any]):
    path = get_cache_path(cache_key)
    _ensure_dir(path)
    source_path = os.path.join(path, "source.json")
    meta_path = os.path.join(path, "metadata.json")
    with open(source_path, "w", encoding="utf-8") as f:
        json.dump(source_data, f, separators=(",", ":"))
    metadata = {
        "cache_key": cache_key,
        "provider": params.get("provider", "unknown"),
        "params": params,
        "schema_version": SCHEMA_VERSION,
        "timestamp": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def list_cache_entries() -> list:
    if not os.path.exists(GEOGRAPHY_CACHE_DIR):
        return []
    entries = []
    for name in os.listdir(GEOGRAPHY_CACHE_DIR):
        meta_path = os.path.join(GEOGRAPHY_CACHE_DIR, name, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                entries.append(json.load(f))
    return entries
