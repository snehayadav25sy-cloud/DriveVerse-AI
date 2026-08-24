"""
app/api/geography.py — Build 5: Geography API endpoints

Endpoints:
  POST /geography/resolve  — resolve a location query to coordinates
  POST /geography/build    — full pipeline: resolve -> OSM -> graph -> OpenDRIVE -> validate
  POST /geography/graph    — resolve + OSM + graph only; returns GeoJSON for deck.gl
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
from app.geography.cache import compute_cache_key, cache_exists, read_cache
from app.geography.graph import build_graph_from_osm, graph_hash
from app.geography.projection import project_graph, projection_metadata
from app.geography.opendrive import OpenDriveCompiler
from app.geography.validator import OpenDriveValidator
from app.geography.provenance import compute_map_provenance, provenance_hash
from app.geography.models import BoundingBox, LocationResolution, MapArtifact

router = APIRouter(prefix="/geography", tags=["geography"])

geocoder = NominatimGeocoder()


class LocationRequest(BaseModel):
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_m: float = Field(500.0, gt=0)
    provider: str = Field("nominatim", min_length=1)


class ResolveResponse(BaseModel):
    status: str
    query: str
    resolution: Optional[LocationResolution] = None
    error: Optional[str] = None


class BuildResponse(BaseModel):
    status: str
    stages: Dict[str, Any]
    map_artifact: Optional[MapArtifact] = None
    provenance: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class GraphGeoJSONResponse(BaseModel):
    status: str
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    node_count: int = 0
    edge_count: int = 0
    elapsed_ms: float = 0.0
    geojson: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/resolve", response_model=ResolveResponse)
def resolve_location(req: LocationRequest):
    """
    Resolve a location query or explicit lat/lon to geographic coordinates.
    """
    try:
        if req.latitude is not None and req.longitude is not None:
            resolution = geocoder.resolve_location(req)
        elif req.location:
            resolution = geocoder.geocode(req.location)
            if resolution is None:
                return ResolveResponse(
                    status="failed",
                    query=req.location,
                    error=f"Geocoding returned no results for '{req.location}'",
                )
        else:
            raise HTTPException(status_code=422, detail="Provide 'location' or both 'latitude' and 'longitude'")

        return ResolveResponse(
            status="resolved",
            query=resolution.query,
            resolution=resolution,
        )
    except HTTPException:
        raise
    except Exception as e:
        return ResolveResponse(
            status="failed",
            query=req.location or f"{req.latitude},{req.longitude}",
            error=str(e),
        )


@router.post("/build", response_model=BuildResponse)
def build_map(req: LocationRequest):
    """
    Full pipeline: resolve -> OSM -> graph -> OpenDRIVE -> validate.
    """
    stages: Dict[str, Any] = {}
    start = time.perf_counter()

    try:
        # Stage 1: Resolve
        stage_start = time.perf_counter()
        if req.latitude is not None and req.longitude is not None:
            resolution = geocoder.resolve_location(req)
        elif req.location:
            resolution = geocoder.geocode(req.location)
            if resolution is None:
                return BuildResponse(
                    status="failed",
                    stages={"resolve": {"status": "failed", "error": f"No geocoding results for '{req.location}'"}},
                    error="Geocoding failed",
                )
        else:
            return BuildResponse(
                status="failed",
                stages={"resolve": {"status": "failed", "error": "No location provided"}},
                error="No location provided",
            )
        stages["resolve"] = {
            "status": "resolved",
            "latitude": resolution.latitude,
            "longitude": resolution.longitude,
            "country": resolution.country,
            "city": resolution.city,
            "elapsed_ms": round((time.perf_counter() - stage_start) * 1000, 1),
        }

        lat = resolution.latitude
        lon = resolution.longitude

        # Stage 2: OSM download
        stage_start = time.perf_counter()
        osm_provider = OverpassProvider()
        raw = osm_provider.download_radius(lat, lon, req.radius_m)
        if raw is None:
            return BuildResponse(
                status="failed",
                stages={**stages, "osm": {"status": "failed", "error": "Overpass returned no data"}},
                error="OSM download failed",
            )
        roads = osm_provider.fetch_roads()
        intersections = osm_provider.fetch_intersections()
        cache_key = compute_cache_key("overpass", {"lat": lat, "lon": lon, "radius_m": req.radius_m})
        stages["osm"] = {
            "status": "downloaded",
            "element_count": len(raw.get("elements", [])),
            "road_count": len(roads),
            "intersection_count": len(intersections),
            "cache_key": cache_key[:16] + "...",
            "elapsed_ms": round((time.perf_counter() - stage_start) * 1000, 1),
        }

        # Stage 3: Graph
        stage_start = time.perf_counter()
        graph = build_graph_from_osm(roads, intersections)
        ghash = graph_hash(graph)
        stages["graph"] = {
            "status": "built",
            "node_count": graph.node_count(),
            "edge_count": graph.edge_count(),
            "graph_hash": ghash[:16] + "...",
            "elapsed_ms": round((time.perf_counter() - stage_start) * 1000, 1),
        }

        # Stage 4: Projection
        stage_start = time.perf_counter()
        projected = project_graph(graph, lat, lon)
        stages["projection"] = {
            "status": "projected",
            "origin": {"lat": lat, "lon": lon},
            "elapsed_ms": round((time.perf_counter() - stage_start) * 1000, 1),
        }

        # Stage 5: OpenDRIVE
        stage_start = time.perf_counter()
        compiler = OpenDriveCompiler(projected)
        xodr_path = os.path.join(tempfile.gettempdir(), f"driveverse_{cache_key[:12]}.xodr")
        compile_meta = compiler.compile(xodr_path)
        stages["opendrive"] = {
            "status": "compiled",
            "path": xodr_path,
            "size_bytes": compile_meta["xodr_size_bytes"],
            "xodr_hash": compile_meta["xodr_hash"][:16] + "...",
            "fallbacks": len(compile_meta.get("fallbacks", [])),
            "elapsed_ms": round((time.perf_counter() - stage_start) * 1000, 1),
        }

        # Stage 6: Validate
        stage_start = time.perf_counter()
        validator = OpenDriveValidator()
        vresult = validator.validate(xodr_path)
        stages["validate"] = {
            "status": "valid" if vresult["valid"] else "invalid",
            "errors": len(vresult["errors"]),
            "warnings": len(vresult["warnings"]),
            "statistics": vresult["statistics"],
            "elapsed_ms": round((time.perf_counter() - stage_start) * 1000, 1),
        }

        # Build MapArtifact
        map_artifact = MapArtifact(
            xodr_path=xodr_path,
            xodr_size_bytes=compile_meta["xodr_size_bytes"],
            xodr_hash=compile_meta["xodr_hash"],
            validator_passed=vresult["valid"],
            validator_errors=vresult["errors"],
            validator_warnings=vresult["warnings"],
            location_query=req.location or f"{lat},{lon}",
            metadata={
                "osm_elements": len(raw.get("elements", [])),
                "road_count": len(roads),
                "intersection_count": len(intersections),
                "fallbacks": compile_meta.get("fallbacks", []),
            },
        )

        # Provenance
        prov = compute_map_provenance(
            location_query=req.location or f"{lat},{lon}",
            radius_m=req.radius_m,
            geocoder_provider="nominatim",
            osm_provider="overpass",
            resolved_latitude=lat,
            resolved_longitude=lon,
            resolved_country=resolution.country,
            resolved_city=resolution.city,
            osm_file_path=f"cache/{cache_key[:12]}/source.json",
            osm_file_size_bytes=len(str(raw).encode("utf-8")),
            osm_timestamp=resolution.timestamp,
            osm_source_hash=compute_cache_key("overpass", {"lat": lat, "lon": lon, "radius_m": req.radius_m}),
            road_graph_node_count=graph.node_count(),
            road_graph_edge_count=graph.edge_count(),
            road_graph_hash=ghash,
            xodr_hash=compile_meta["xodr_hash"],
            fallbacks=compile_meta.get("fallbacks", []),
            warnings=vresult["warnings"],
            errors=vresult["errors"],
        )

        prov_dict = prov.model_dump()
        prov_dict["provenance_hash"] = provenance_hash(prov)
        total_ms = round((time.perf_counter() - start) * 1000, 1)
        return BuildResponse(
            status="complete" if vresult["valid"] else "completed_with_errors",
            stages=stages,
            map_artifact=map_artifact,
            provenance=prov_dict,
            error=None,
        )

    except Exception as e:
        return BuildResponse(
            status="failed",
            stages=stages,
            error=str(e),
        )


@router.post("/graph", response_model=GraphGeoJSONResponse)
def build_graph_geojson(req: LocationRequest):
    """
    Resolve + OSM + graph only; returns a GeoJSON FeatureCollection for deck.gl.
    Skips OpenDRIVE compilation and validation — fast path for map preview.
    """
    start = time.perf_counter()
    try:
        # Stage 1: Resolve
        if req.latitude is not None and req.longitude is not None:
            resolution = geocoder.resolve_location(req)
        elif req.location:
            resolution = geocoder.geocode(req.location)
            if resolution is None:
                return GraphGeoJSONResponse(
                    status="failed",
                    error=f"Geocoding returned no results for '{req.location}'",
                )
        else:
            return GraphGeoJSONResponse(
                status="failed",
                error="Provide 'location' or both 'latitude' and 'longitude'",
            )

        lat = resolution.latitude
        lon = resolution.longitude

        # Stage 2: OSM
        osm_provider = OverpassProvider()
        raw = osm_provider.download_radius(lat, lon, req.radius_m)
        if raw is None:
            return GraphGeoJSONResponse(
                status="failed",
                error="Overpass returned no data",
            )
        roads = osm_provider.fetch_roads()
        intersections = osm_provider.fetch_intersections()

        # Stage 3: Graph
        graph = build_graph_from_osm(roads, intersections)

        # Serialize to GeoJSON FeatureCollection
        features: List[Dict[str, Any]] = []

        # Road edges → LineString features
        for edge in graph.edges:
            road = edge.road
            # geometry stored as list of (lon, lat) tuples
            if road.geometry and len(road.geometry) >= 2:
                coordinates = [[pt[0], pt[1]] for pt in road.geometry]
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                    "properties": {
                        "feature_type": "edge",
                        "edge_id": edge.edge_id,
                        "road_type": road.road_type,
                        "name": road.name or "",
                        "lanes": road.lanes,
                        "length_m": round(edge.length_m, 1),
                        "one_way": road.one_way,
                        "speed_kph": road.speed_kph,
                    },
                })

        # Nodes → Point features
        for node in graph.nodes:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [node.coordinate.longitude, node.coordinate.latitude],
                },
                "properties": {
                    "feature_type": "node",
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                },
            })

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return GraphGeoJSONResponse(
            status="complete",
            center_lat=lat,
            center_lon=lon,
            node_count=graph.node_count(),
            edge_count=graph.edge_count(),
            elapsed_ms=elapsed_ms,
            geojson={
                "type": "FeatureCollection",
                "features": features,
            },
        )

    except Exception as e:
        return GraphGeoJSONResponse(
            status="failed",
            error=str(e),
        )
