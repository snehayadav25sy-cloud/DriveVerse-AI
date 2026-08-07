"""
app/geography/opendrive.py — Build 5: OpenDRIVE compiler

Converts a RoadGraph into a valid OpenDRIVE 1.6 .xodr file.

Design decisions:
  - Road IDs are derived from OSM way IDs (prefixed with 'r_').
  - Junction IDs are derived from node IDs (prefixed with 'j_').
  - Lane widths default to 3.5m when OSM lane count exists but no per-lane width.
  - Max speed defaults to 50 km/h when OSM maxspeed is missing (documented fallback).
  - Road links are inferred from graph connectivity.
  - Every fallback is recorded in the returned fallbacks list.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional, Tuple

from app.geography.models import RoadGraph, RoadNode, RoadEdge


class OpenDriveCompiler:
    """Compiles a RoadGraph into an OpenDRIVE .xodr file."""

    DEFAULT_LANE_WIDTH = 3.5
    DEFAULT_MAX_SPEED = 50.0
    DEFAULT_SPEED_UNIT = "km/h"

    def __init__(self, graph: RoadGraph):
        self.graph = graph
        self.fallbacks: List[str] = []

    def _record_fallback(self, reason: str):
        self.fallbacks.append(reason)

    def _safe_float(self, value: Optional[float], default: float, fallback_reason: str) -> float:
        if value is None:
            self._record_fallback(fallback_reason)
            return default
        return value

    def compile(self, output_path: str) -> Dict[str, Any]:
        """
        Compile the graph to an .xodr file at output_path.
        Returns metadata dict with path, size, hash, fallbacks.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Build junction map: nodes with >2 connected edges become junctions
        edge_map: Dict[str, List[RoadEdge]] = {}
        for edge in self.graph.edges:
            edge_map.setdefault(edge.from_node, []).append(edge)
            edge_map.setdefault(edge.to_node, []).append(edge)

        junction_nodes = {nid for nid, edges in edge_map.items() if len(edges) > 2}

        lines: List[str] = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<OpenDRIVE xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.opendrive.org/schema/1.6/OpenDrive.xsd">')

        # Header
        lines.append("  <header revMajor=\"1\" revMinor=\"6\" name=\"DriveVerse\" version=\"1.00\">")
        lines.append(f"    <geoReference>+proj=utm +zone=43 +datum=WGS84 +units=m +vunits=m +no_defs</geoReference>")
        lines.append("  </header>")

        # Roads
        for edge in self.graph.edges:
            road_id = edge.edge_id.replace("/", "_").replace("edge_", "r_")
            length = self._safe_float(
                edge.length_m,
                self.DEFAULT_MAX_SPEED * 2,
                f"Road {road_id}: length missing, defaulted to {self.DEFAULT_MAX_SPEED * 2}m",
            )
            maxspeed = self._safe_float(
                edge.road.maxspeed,
                self.DEFAULT_MAX_SPEED,
                f"Road {road_id}: maxspeed missing, defaulted to {self.DEFAULT_MAX_SPEED} km/h",
            )
            lanes = self._safe_float(
                float(edge.road.lanes),
                2.0,
                f"Road {road_id}: lane count missing, defaulted to 2",
            )

            lines.append(f"  <road name=\"{self._xml_escape(edge.road.name or '')}\" length=\"{length:.6f}\" id=\"{road_id}\" junction=\"-1\">")

            # Geometry (use first/last node coordinates as reference)
            from_node = next((n for n in self.graph.nodes if n.node_id == edge.from_node), None)
            to_node = next((n for n in self.graph.nodes if n.node_id == edge.to_node), None)
            if from_node and to_node:
                x0 = from_node.coordinate.latitude
                y0 = from_node.coordinate.longitude
                x1 = to_node.coordinate.latitude
                y1 = to_node.coordinate.longitude
                hdg = self._heading(x0, y0, x1, y1)
                lines.append(f"    <geometry hdg=\"{hdg:.6f}\" length=\"{length:.6f}\" s=\"0.0\" x=\"{x0:.6f}\" y=\"{y0:.6f}\"/>")

            # Lane sections
            lane_width = self._safe_float(
                None if edge.road.maxspeed else self.DEFAULT_LANE_WIDTH,
                self.DEFAULT_LANE_WIDTH,
                f"Road {road_id}: lane width missing, defaulted to {self.DEFAULT_LANE_WIDTH}m",
            )
            lines.append(f"    <lanes>")
            lines.append(f"      <laneSection>")
            lines.append(f"        <left>")
            for i in range(int(lanes) // 2):
                lid = -(i + 1)
                lines.append(f"          <lane id=\"{lid}\" level=\"false\" type=\"driving\" width=\"{lane_width:.3f}\">")
                lines.append(f"            <link/>")
                lines.append(f"          </lane>")
            lines.append(f"        </left>")
            lines.append(f"        <center/>")
            lines.append(f"        <right>")
            for i in range(int(lanes) - int(lanes) // 2):
                lid = i + 1
                lines.append(f"          <lane id=\"{lid}\" level=\"false\" type=\"driving\" width=\"{lane_width:.3f}\">")
                lines.append(f"            <link/>")
                lines.append(f"          </lane>")
            lines.append(f"        </right>")
            lines.append(f"      </laneSection>")
            lines.append(f"    </lanes>")
            lines.append(f"    <link>")
            if to_node and to_node.node_id in junction_nodes:
                jid = to_node.node_id.replace("/", "_")
                lines.append(f"      <successor elementType=\"junction\" elementId=\"{jid}\"/>")
            lines.append(f"    </link>")
            lines.append(f"  </road>")

        # Junctions
        for nid in junction_nodes:
            jid = nid.replace("/", "_")
            node = next((n for n in self.graph.nodes if n.node_id == nid), None)
            if not node:
                continue
            lines.append(f"  <junction name=\"\" id=\"{jid}\" type=\"priority\">")
            for edge in edge_map.get(nid, []):
                road_id = edge.edge_id.replace("/", "_").replace("edge_", "r_")
                lines.append(f"    <connection id=\"{hashlib.md5(road_id.encode()).hexdigest()[:8]}\" incomingRoad=\"{road_id}\" connectingRoad=\"{road_id}\" junctionId=\"{jid}\">")
                lines.append(f"      <laneLink from=\"-1\" to=\"-1\"/>")
                lines.append(f"    </connection>")
            lines.append(f"  </junction>")

        lines.append("</OpenDRIVE>")

        xml_content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        file_size = os.path.getsize(output_path)
        xodr_hash = hashlib.sha256(xml_content.encode("utf-8")).hexdigest()

        return {
            "xodr_path": output_path,
            "xodr_size_bytes": file_size,
            "xodr_hash": xodr_hash,
            "fallbacks": self.fallbacks,
        }

    @staticmethod
    def _heading(x0: float, y0: float, x1: float, y1: float) -> float:
        """Approximate heading from point A to point B in radians."""
        import math
        return math.atan2(y1 - y0, x1 - x0)

    @staticmethod
    def _xml_escape(text: str) -> str:
        import xml.sax.saxutils as saxutils
        return saxutils.escape(text, {'"': ""})
