"""
app/geography/projection.py — Build 5: Coordinate projection

WGS84 (lat/lon) → local metric → CARLA coordinates.

Strategy:
  - Use a local equirectangular projection centred on the scenario origin.
  - X = Easting (metres east of origin)
  - Y = Northing (metres north of origin)
  - Z = altitude (metres, passed through unchanged)

Scale factors at the origin latitude are computed once and stored.
The projection is fully deterministic for a given origin.

CARLA coordinate convention:
  - X forward (north in our projection)
  - Y right (east in our projection)
  - Z up
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

from app.geography.models import GeoCoordinate, RoadEdge, RoadGraph, RoadNode


def project_geographic_to_carla(
    lat: float,
    lon: float,
    alt: float,
    origin_lat: float,
    origin_lon: float,
) -> Tuple[float, float, float]:
    """
    Project a single WGS84 coordinate into CARLA local space.

    Returns (carla_x, carla_y, carla_z) where:
      carla_x = northing (forward)
      carla_y = easting (right)
      carla_z = altitude (up)
    """
    phi0 = math.radians(origin_lat)
    phi = math.radians(lat)
    dphi = math.radians(lat - origin_lat)
    dlambda = math.radians(lon - origin_lon)

    # Approximate metres per degree at origin latitude
    m_per_deg_lat = 111_132.0 - 559.0 * math.cos(2 * phi0)
    m_per_deg_lon = 111_412.0 * math.cos(phi0) - 93.5 * math.cos(3 * phi0)

    north = dphi * m_per_deg_lat
    east = dlambda * m_per_deg_lon

    carla_x = north
    carla_y = east
    carla_z = alt

    return (carla_x, carla_y, carla_z)


def projection_metadata(origin_lat: float, origin_lon: float) -> Dict[str, Any]:
    """Return metadata describing the projection for provenance."""
    phi0 = math.radians(origin_lat)
    m_per_deg_lat = 111_132.0 - 559.0 * math.cos(2 * phi0)
    m_per_deg_lon = 111_412.0 * math.cos(phi0) - 93.5 * math.cos(3 * phi0)
    return {
        "origin_latitude": origin_lat,
        "origin_longitude": origin_lon,
        "projection": "equirectangular_local",
        "m_per_deg_lat": round(m_per_deg_lat, 6),
        "m_per_deg_lon": round(m_per_deg_lon, 6),
        "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
        "scale": 1.0,
    }


def project_graph(graph: RoadGraph, origin_lat: float, origin_lon: float) -> RoadGraph:
    """
    Project all node coordinates in a RoadGraph into CARLA space.

    Returns a NEW RoadGraph with projected coordinates.
    Original graph is not modified.
    """
    new_nodes = []
    for node in graph.nodes:
        cx, cy, cz = project_geographic_to_carla(
            node.coordinate.latitude,
            node.coordinate.longitude,
            node.coordinate.altitude,
            origin_lat,
            origin_lon,
        )
        new_coord = GeoCoordinate(latitude=cx, longitude=cy, altitude=cz)
        new_node = RoadNode(
            node_id=node.node_id,
            coordinate=new_coord,
            node_type=node.node_type,
            roads=list(node.roads),
        )
        new_nodes.append(new_node)

    new_edges = []
    for edge in graph.edges:
        new_road = edge.road.model_copy()
        new_edge = RoadEdge(
            edge_id=edge.edge_id,
            from_node=edge.from_node,
            to_node=edge.to_node,
            road=new_road,
            length_m=edge.length_m,
            lane_count=edge.lane_count,
        )
        new_edges.append(new_edge)

    new_meta = dict(graph.metadata)
    new_meta["projection"] = projection_metadata(origin_lat, origin_lon)
    return RoadGraph(nodes=new_nodes, edges=new_edges, metadata=new_meta)


def distance_between_nodes_carla(
    node_a: RoadNode,
    node_b: RoadNode,
) -> float:
    """Euclidean distance between two already-projected CARLA nodes."""
    dx = node_a.coordinate.latitude - node_b.coordinate.latitude
    dy = node_a.coordinate.longitude - node_b.coordinate.longitude
    dz = node_a.coordinate.altitude - node_b.coordinate.altitude
    return math.sqrt(dx * dx + dy * dy + dz * dz)
