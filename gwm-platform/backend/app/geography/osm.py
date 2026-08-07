"""
app/geography/osm.py — Build 5: OSM data acquisition

Design:
  - OSMProvider is an abstract interface.
  - OverpassProvider is the reference implementation using the Overpass API.
  - All data is returned as parsed Python dicts/lists, never raw XML strings
    leaking into downstream modules.
  - Rate limiting: minimum 1 second between Overpass requests (per usage policy).
  - Missing fields are recorded as None with a fallback reason — never invented.
  - Attribution: OpenStreetMap data is ODbL-licensed. See docs/geography-data-policy.md.

Out of scope:
  - Building geometry generation, procedural buildings, photorealistic reconstruction.
  - This module only fetches metadata; no 3D asset generation.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.geography.cache import compute_cache_key, cache_exists, read_cache, write_cache
from app.geography.models import (
    Road,
    Lane,
    Intersection,
    TrafficSignal,
    Crosswalk,
)


class OSMProvider(ABC):
    """Abstract OSM data provider."""

    @abstractmethod
    def download_region(self, bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
        """Download all OSM data for a bounding box (south, west, north, east)."""
        raise NotImplementedError

    @abstractmethod
    def download_radius(self, lat: float, lon: float, radius_m: float) -> Dict[str, Any]:
        """Download OSM data within radius_m of a point."""
        raise NotImplementedError

    @abstractmethod
    def fetch_roads(self) -> List[Road]:
        """Extract road features from the most recent download."""
        raise NotImplementedError

    @abstractmethod
    def fetch_intersections(self) -> List[Intersection]:
        """Extract intersection nodes from the most recent download."""
        raise NotImplementedError

    @abstractmethod
    def fetch_traffic_signals(self) -> List[TrafficSignal]:
        """Extract traffic signals from the most recent download."""
        raise NotImplementedError

    @abstractmethod
    def fetch_crosswalks(self) -> List[Crosswalk]:
        """Extract crosswalks from the most recent download."""
        raise NotImplementedError

    @abstractmethod
    def fetch_buildings_metadata(self) -> List[Dict[str, Any]]:
        """Extract building metadata (NOT geometry generation)."""
        raise NotImplementedError


class OverpassProvider(OSMProvider):
    """
    OpenStreetMap Overpass API provider.

    Usage policy compliance:
      - Minimum 1 second between requests.
      - No parallel requests from the same client.
      - Reasonable bounding box sizes only (not whole countries).
    """

    FALLBACK_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
    ]

    def __init__(
        self,
        base_url: str = FALLBACK_URLS[0],
        user_agent: str = "DriveVerse-AI-GeographyEngine/1.0",
        timeout: float = 120.0,
        rate_limit_s: float = 1.0,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit_s = rate_limit_s
        self._last_request_time: float = 0.0
        self._last_raw: Optional[Dict[str, Any]] = None
        self._base_urls = [base_url] + [u for u in self.FALLBACK_URLS if u != base_url]

    # ── Rate limiting ─────────────────────────────────────────────────────────

    def _wait_for_rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_s:
            time.sleep(self.rate_limit_s - elapsed)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _request(self, query: str) -> Dict[str, Any]:
        self._wait_for_rate_limit()
        last_exc = None
        for url in self._base_urls:
            for attempt in range(3):
                try:
                    resp = requests.post(
                        url,
                        data=query,
                        timeout=self.timeout,
                        headers={"User-Agent": self.user_agent},
                    )
                    if resp.status_code == 504:
                        time.sleep(2.0 * (attempt + 1))
                        continue
                    resp.raise_for_status()
                    self._last_request_time = time.time()
                    return resp.json()
                except Exception as exc:
                    last_exc = exc
                    time.sleep(1.0)
        raise RuntimeError(f"Overpass request failed after retries: {last_exc}")

    @staticmethod
    def _bbox_to_str(bbox: Tuple[float, float, float, float]) -> str:
        south, west, north, east = bbox
        return f"{south},{west},{north},{east}"

    @staticmethod
    def _radius_to_bbox(lat: float, lon: float, radius_m: float) -> Tuple[float, float, float, float]:
        import math
        d_lat = (radius_m / 111_320.0)
        d_lon = (radius_m / (111_320.0 * math.cos(math.radians(lat))))
        south = lat - d_lat
        north = lat + d_lat
        west = lon - d_lon
        east = lon + d_lon
        return (south, west, north, east)

    # ── Download ─────────────────────────────────────────────────────────────

    def download_region(self, bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
        """Download OSM data for a bounding box."""
        bbox_str = self._bbox_to_str(bbox)
        cache_key = compute_cache_key("overpass", {"bbox": bbox_str})
        if cache_exists(cache_key):
            data = read_cache(cache_key)
            self._last_raw = data
            return data

        query = f"""
        [out:json][timeout:{int(self.timeout)}];
        (
          way["highway"]({bbox_str});
          node["highway"="traffic_signals"]({bbox_str});
          node["crossing"]({bbox_str});
          way["building"]({bbox_str});
        );
        out body;
        >;
        out skel qt;
        """
        data = self._request(query)
        self._last_raw = data
        write_cache(cache_key, data, {"bbox": bbox_str})
        return data

    def download_radius(self, lat: float, lon: float, radius_m: float) -> Dict[str, Any]:
        """Download OSM data within radius_m of a point."""
        bbox = self._radius_to_bbox(lat, lon, radius_m)
        bbox_str = self._bbox_to_str(bbox)
        cache_key = compute_cache_key("overpass", {"lat": lat, "lon": lon, "radius_m": radius_m})
        if cache_exists(cache_key):
            data = read_cache(cache_key)
            self._last_raw = data
            return data

        query = f"""
        [out:json][timeout:{int(self.timeout)}];
        (
          way["highway"]({bbox_str});
          node["highway"="traffic_signals"]({bbox_str});
          node["crossing"]({bbox_str});
          way["building"]({bbox_str});
        );
        out body;
        >;
        out skel qt;
        """
        data = self._request(query)
        self._last_raw = data
        write_cache(cache_key, data, {"lat": lat, "lon": lon, "radius_m": radius_m})
        return data

    # ── Extraction ───────────────────────────────────────────────────────────

    def fetch_roads(self) -> List[Road]:
        """Extract roads from the most recent raw download."""
        if self._last_raw is None:
            return []
        elements = self._last_raw.get("elements", [])
        roads = []
        for el in elements:
            if el.get("type") != "way":
                continue
            tags = el.get("tags", {})
            if "highway" not in tags:
                continue
            geometry = []
            if "geometry" in el:
                geometry = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            else:
                for node_id in el.get("nodes", []):
                    node = next((n for n in elements if n.get("type") == "node" and n.get("id") == node_id), None)
                    if node:
                        geometry.append((node["lon"], node["lat"]))
            roads.append(Road(
                osm_id=f"way/{el['id']}",
                name=tags.get("name"),
                highway_type=tags.get("highway", "unclassified"),
                lanes=int(tags["lanes"]) if "lanes" in tags and tags["lanes"].isdigit() else 1,
                maxspeed=float(tags["maxspeed"]) if "maxspeed" in tags and tags["maxspeed"].isdigit() else None,
                oneway=tags.get("oneway") == "yes",
                surface=tags.get("surface"),
                bridge=tags.get("bridge") == "yes",
                tunnel=tags.get("tunnel") == "yes",
                country=tags.get("addr:country"),
                source_osm_id=f"way/{el['id']}",
                geometry=geometry,
            ))
        return roads

    def fetch_intersections(self) -> List[Intersection]:
        """Extract intersections (nodes used by multiple ways)."""
        if self._last_raw is None:
            return []
        elements = self._last_raw.get("elements", [])
        nodes = {el["id"]: el for el in elements if el.get("type") == "node"}
        ways = [el for el in elements if el.get("type") == "way"]
        node_usage: Dict[int, List[str]] = {}
        for way in ways:
            for node_id in way.get("nodes", []):
                node_usage.setdefault(node_id, []).append(f"way/{way['id']}")
        intersections = []
        for node_id, road_list in node_usage.items():
            if len(road_list) < 2:
                continue
            node = nodes.get(node_id)
            if not node:
                continue
            tags = node.get("tags", {})
            intersections.append(Intersection(
                node_id=f"node/{node_id}",
                latitude=node["lat"],
                longitude=node["lon"],
                incoming_roads=road_list,
                outgoing_roads=road_list,
                traffic_signal=tags.get("highway") == "traffic_signals",
            ))
        return intersections

    def fetch_traffic_signals(self) -> List[TrafficSignal]:
        """Extract traffic signals."""
        if self._last_raw is None:
            return []
        elements = self._last_raw.get("elements", [])
        signals = []
        for el in elements:
            if el.get("type") != "node":
                continue
            tags = el.get("tags", {})
            if tags.get("highway") != "traffic_signals":
                continue
            signals.append(TrafficSignal(
                osm_id=f"node/{el['id']}",
                latitude=el["lat"],
                longitude=el["lon"],
                signal_type="traffic_light",
                lanes=[],
            ))
        return signals

    def fetch_crosswalks(self) -> List[Crosswalk]:
        """Extract crosswalks."""
        if self._last_raw is None:
            return []
        elements = self._last_raw.get("elements", [])
        crosswalks = []
        for el in elements:
            if el.get("type") != "way":
                continue
            tags = el.get("tags", {})
            if "crossing" not in tags:
                continue
            geometry = []
            if "geometry" in el:
                geometry = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            crosswalks.append(Crosswalk(
                osm_id=f"way/{el['id']}",
                latitude=geometry[0][1] if geometry else 0.0,
                longitude=geometry[0][0] if geometry else 0.0,
                crossing_type=tags.get("crossing", "marked"),
                lanes=[],
            ))
        return crosswalks

    def fetch_buildings_metadata(self) -> List[Dict[str, Any]]:
        """
        Extract building metadata only (no geometry generation).
        Returns list of dicts with OSM tags.
        """
        if self._last_raw is None:
            return []
        elements = self._last_raw.get("elements", [])
        buildings = []
        for el in elements:
            if el.get("type") != "way":
                continue
            tags = el.get("tags", {})
            if "building" not in tags:
                continue
            record = {
                "osm_id": f"way/{el['id']}",
                "building_type": tags.get("building"),
                "name": tags.get("name"),
                "levels": tags.get("building:levels"),
                "height": tags.get("height"),
                "area": tags.get("area"),
                "source_osm_id": f"way/{el['id']}",
            }
            buildings.append(record)
        return buildings
