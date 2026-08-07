"""
app/geography/geocoder.py — Build 5: Geocoder interface + Nominatim implementation

Design:
  - Geocoder is an abstract interface.
  - NominatimGeocoder is the reference implementation using OpenStreetMap Nominatim.
  - All methods return LocationResolution objects.
  - Caching is in-memory (process-local). For persistent cache, see Phase 4.
  - Timeout and exponential backoff are implemented per request.
  - NEVER fabricate coordinates — if geocoding fails, return None with error detail.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlencode

import requests

from app.geography.models import LocationResolution, GeoCoordinate, BoundingBox


class Geocoder(ABC):
    """Abstract geocoder interface."""

    @abstractmethod
    def geocode(self, query: str) -> Optional[LocationResolution]:
        """Resolve a free-text location query to coordinates."""
        raise NotImplementedError

    @abstractmethod
    def reverse_geocode(self, lat: float, lon: float) -> Optional[LocationResolution]:
        """Resolve coordinates to a human-readable location."""
        raise NotImplementedError

    @abstractmethod
    def resolve_location(self, request) -> LocationResolution:
        """
        Resolve a LocationRequest.
        If request has explicit lat/lon, bypass geocoding and return a synthetic resolution.
        Otherwise, call geocode().
        """
        raise NotImplementedError


class NominatimGeocoder(Geocoder):
    """
    OpenStreetMap Nominatim geocoder.

    Usage policy:
      - Maximum 1 request per second.
      - Provide a valid User-Agent / Referer.
      - Attribution required: 'Data © OpenStreetMap contributors, ODbL 1.0 license'
    """

    def __init__(
        self,
        base_url: str = "https://nominatim.openstreetmap.org",
        user_agent: str = "DriveVerse-AI-GeographyEngine/1.0",
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_base: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._cache: dict[str, LocationResolution] = {}

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _cache_key(self, kind: str, value: str) -> str:
        raw = f"{kind}:{value}".lower().strip()
        return hashlib.sha256(raw.encode()).hexdigest()

    def _request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make a GET request with retry + exponential backoff."""
        url = f"{self.base_url}/{endpoint}"
        params.setdefault("format", "json")
        params.setdefault("addressdetails", "1")
        params.setdefault("extratags", "0")
        params.setdefault("namedetails", "0")

        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    headers={"User-Agent": self.user_agent},
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    sleep_s = self.backoff_base * (2 ** (attempt - 1))
                    time.sleep(sleep_s)
        return None

    # ── Public API ───────────────────────────────────────────────────────────

    def geocode(self, query: str) -> Optional[LocationResolution]:
        """
        Geocode a free-text query.
        Returns LocationResolution on success, None on failure.
        """
        key = self._cache_key("geocode", query)
        if key in self._cache:
            cached = self._cache[key]
            cached = cached.model_copy(update={"cached": True})
            return cached

        data = self._request("search", {"q": query, "limit": 1})
        if not data or not isinstance(data, list) or len(data) == 0:
            return None

        item = data[0]
        lat = float(item.get("lat", 0))
        lon = float(item.get("lon", 0))

        bbox = None
        if "boundingbox" in item and len(item["boundingbox"]) == 4:
            try:
                bbox = BoundingBox(
                    south=float(item["boundingbox"][0]),
                    north=float(item["boundingbox"][1]),
                    west=float(item["boundingbox"][2]),
                    east=float(item["boundingbox"][3]),
                )
            except Exception:
                bbox = None

        addr = item.get("address", {})
        resolution = LocationResolution(
            query=query,
            provider="nominatim",
            latitude=lat,
            longitude=lon,
            display_name=item.get("display_name"),
            country=addr.get("country"),
            country_code=addr.get("country_code"),
            state=addr.get("state"),
            city=addr.get("city") or addr.get("town") or addr.get("county"),
            bounding_box=bbox,
            raw=item,
            cached=False,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self._cache[key] = resolution
        return resolution

    def reverse_geocode(self, lat: float, lon: float) -> Optional[LocationResolution]:
        """
        Reverse-geocode coordinates.
        Returns LocationResolution on success, None on failure.
        """
        key = self._cache_key("reverse", f"{lat},{lon}")
        if key in self._cache:
            cached = self._cache[key]
            cached = cached.model_copy(update={"cached": True})
            return cached

        data = self._request("reverse", {"lat": str(lat), "lon": str(lon)})
        if not data or "lat" not in data:
            return None

        lat = float(data.get("lat", 0))
        lon = float(data.get("lon", 0))
        addr = data.get("address", {})

        resolution = LocationResolution(
            query=f"{lat},{lon}",
            provider="nominatim",
            latitude=lat,
            longitude=lon,
            display_name=data.get("display_name"),
            country=addr.get("country"),
            country_code=addr.get("country_code"),
            state=addr.get("state"),
            city=addr.get("city") or addr.get("town") or addr.get("county"),
            raw=data,
            cached=False,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self._cache[key] = resolution
        return resolution

    def resolve_location(self, request) -> LocationResolution:
        """
        Resolve a LocationRequest.
        If explicit lat/lon are provided, return a synthetic resolution without
        hitting the network. Otherwise, call geocode().
        Raises ValueError if neither text nor coords are usable.
        """
        if request.latitude is not None and request.longitude is not None:
            synthetic = LocationResolution(
                query=request.location or f"{request.latitude},{request.longitude}",
                provider=request.provider,
                latitude=request.latitude,
                longitude=request.longitude,
                display_name=request.location,
                country=request.country,
                cached=False,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            return synthetic

        if not request.location:
            raise ValueError("LocationRequest must have 'location' or both 'latitude' and 'longitude'")

        result = self.geocode(request.location)
        if result is None:
            raise ValueError(
                f"Geocoding failed for query: '{request.location}'. "
                "No results returned from provider."
            )
        return result
