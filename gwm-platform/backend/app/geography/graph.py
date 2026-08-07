"""
app/geography/graph.py — Build 5: Road graph construction

Converts raw OSM data into a RoadGraph:
  - Nodes = intersections, endpoints, dead ends, merges, splits
  - Edges = road segments with geometry, metadata, length

Geometry is in geographic coordinates (WGS84 lat/lon).
Coordinate projection to CARLA space is handled by Phase 6.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Optional, Tuple

from app.geography.models import (
    BoundingBox,
    GeoCoordinate,
    Road,
    RoadEdge,
    RoadGraph,
    RoadNode,
)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two WGS84 points."""
    R = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _cumulative_lengths(geometry: List[Tuple[float, float]]) -> List[float]:
    """Return cumulative distance along a list of (lon, lat) points."""
    dists = [0.0]
    for i in range(1, len(geometry)):
        d = _haversine_m(geometry[i - 1][1], geometry[i - 1][0], geometry[i][1], geometry[i][0])
        dists.append(dists[-1] + d)
    return dists


class RoadGraphBuilder:
    """Builds a RoadGraph from raw OSM elements and extracted roads."""

    def __init__(self, roads: List[Road], intersections: List[Intersection]):
        self.roads = roads
        self.intersections = intersections
        self._node_map: Dict[str, RoadNode] = {}
        self._edges: List[RoadEdge] = []

    def build(self) -> RoadGraph:
        """Construct the full road graph."""
        self._node_map.clear()
        self._edges.clear()

        # Build nodes from intersections first
        for inter in self.intersections:
            node = RoadNode(
                node_id=inter.node_id,
                coordinate=GeoCoordinate(
                    latitude=inter.latitude,
                    longitude=inter.longitude,
                ),
                node_type="intersection",
                roads=inter.incoming_roads + inter.outgoing_roads,
            )
            self._node_map[node.node_id] = node

        # Build edges from roads
        for road in self.roads:
            if not road.geometry or len(road.geometry) < 2:
                continue
            coords = [GeoCoordinate(latitude=lat, longitude=lon) for lon, lat in road.geometry]
            from_coord = coords[0]
            to_coord = coords[-1]
            cum = _cumulative_lengths(road.geometry)
            length_m = cum[-1] if cum else 0.0

            from_id = f"endpoint_{road.osm_id}_start"
            to_id = f"endpoint_{road.osm_id}_end"

            if from_id not in self._node_map:
                self._node_map[from_id] = RoadNode(
                    node_id=from_id,
                    coordinate=from_coord,
                    node_type="endpoint",
                    roads=[road.osm_id],
                )
            else:
                existing = self._node_map[from_id]
                if road.osm_id not in existing.roads:
                    existing.roads.append(road.osm_id)
                if len(existing.roads) > 2:
                    existing.node_type = "merge"

            if to_id not in self._node_map:
                self._node_map[to_id] = RoadNode(
                    node_id=to_id,
                    coordinate=to_coord,
                    node_type="endpoint",
                    roads=[road.osm_id],
                )
            else:
                existing = self._node_map[to_id]
                if road.osm_id not in existing.roads:
                    existing.roads.append(road.osm_id)
                if len(existing.roads) > 2:
                    existing.node_type = "split"

            edge = RoadEdge(
                edge_id=f"edge_{road.osm_id}",
                from_node=from_id,
                to_node=to_id,
                road=road,
                length_m=length_m,
                lane_count=road.lanes,
            )
            self._edges.append(edge)

        # Re-classify nodes with 0 connected edges as dead ends
        connected = set()
        for edge in self._edges:
            connected.add(edge.from_node)
            connected.add(edge.to_node)
        for node in self._node_map.values():
            if node.node_type == "endpoint" and node.node_id not in connected:
                node.node_type = "dead_end"

        nodes = sorted(self._node_map.values(), key=lambda n: n.node_id)
        edges = sorted(self._edges, key=lambda e: e.edge_id)
        metadata = {
            "source": "osm",
            "road_count": len(self.roads),
            "intersection_count": len(self.intersections),
        }
        return RoadGraph(nodes=nodes, edges=edges, metadata=metadata)


def build_graph_from_osm(
    roads: List[Road],
    intersections: List[Intersection],
) -> RoadGraph:
    """
    Convenience function: build a RoadGraph from OSM-extracted roads and intersections.
    """
    builder = RoadGraphBuilder(roads, intersections)
    return builder.build()


def graph_hash(graph: RoadGraph) -> str:
    """Deterministic hash of a RoadGraph for reproducibility checks."""
    payload = {
        "nodes": [n.model_dump() for n in graph.nodes],
        "edges": [e.model_dump() for e in graph.edges],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
