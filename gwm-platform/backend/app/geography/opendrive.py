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

        # Build topology maps
        edge_map: Dict[str, List[RoadEdge]] = {}
        for edge in self.graph.edges:
            edge_map.setdefault(edge.from_node, []).append(edge)
            edge_map.setdefault(edge.to_node, []).append(edge)

        junction_nodes = {nid for nid, edges in edge_map.items() if len(edges) > 2}

        road_id_to_edge: Dict[str, RoadEdge] = {}
        for edge in self.graph.edges:
            road_id = edge.edge_id.replace("/", "_").replace("edge_", "r_")
            road_id_to_edge[road_id] = edge

        road_lanes: Dict[str, List[str]] = {}
        for edge in self.graph.edges:
            road_id = edge.edge_id.replace("/", "_").replace("edge_", "r_")
            lanes = int(self._safe_float(
                float(edge.road.lanes),
                2.0,
                f"Road {road_id}: lane count missing, defaulted to 2",
            ))
            lane_ids: List[str] = []
            for i in range(lanes // 2):
                lane_ids.append(str(-(i + 1)))
            for i in range(lanes - lanes // 2):
                lane_ids.append(str(i + 1))
            road_lanes[road_id] = lane_ids

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
                x0 = from_node.coordinate.longitude
                y0 = from_node.coordinate.latitude
                x1 = to_node.coordinate.longitude
                y1 = to_node.coordinate.latitude
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

            # Road-level predecessor/successor links
            lines.append(f"    <link>")
            # Predecessors: roads that end at this road's start node
            if from_node and from_node.node_id in junction_nodes:
                jid = from_node.node_id.replace("/", "_")
                lines.append(f"      <predecessor elementType=\"junction\" elementId=\"{jid}\"/>")
            else:
                for e in edge_map.get(edge.from_node, []):
                    if e is not edge and e.to_node == edge.from_node:
                        pid = e.edge_id.replace("/", "_").replace("edge_", "r_")
                        lines.append(f"      <predecessor elementType=\"road\" elementId=\"{pid}\"/>")
            # Successors: roads that start at this road's end node
            if to_node and to_node.node_id in junction_nodes:
                jid = to_node.node_id.replace("/", "_")
                lines.append(f"      <successor elementType=\"junction\" elementId=\"{jid}\"/>")
            else:
                for e in edge_map.get(edge.to_node, []):
                    if e is not edge and e.from_node == edge.to_node:
                        sid = e.edge_id.replace("/", "_").replace("edge_", "r_")
                        lines.append(f"      <successor elementType=\"road\" elementId=\"{sid}\"/>")
            lines.append(f"    </link>")
            lines.append(f"  </road>")

        # Junctions
        for nid in junction_nodes:
            jid = nid.replace("/", "_")
            node = next((n for n in self.graph.nodes if n.node_id == nid), None)
            if not node:
                continue
            lines.append(f"  <junction name=\"\" id=\"{jid}\" type=\"priority\">")
            incoming_edges = [e for e in edge_map.get(nid, []) if e.to_node == nid]
            outgoing_edges = [e for e in edge_map.get(nid, []) if e.from_node == nid]
            for inc in incoming_edges:
                inc_id = inc.edge_id.replace("/", "_").replace("edge_", "r_")
                inc_lanes = road_lanes.get(inc_id, [])
                for out in outgoing_edges:
                    out_id = out.edge_id.replace("/", "_").replace("edge_", "r_")
                    out_lanes = road_lanes.get(out_id, [])
                    conn_id = hashlib.md5(f"{inc_id}_{out_id}".encode()).hexdigest()[:8]
                    lines.append(f"    <connection id=\"{conn_id}\" incomingRoad=\"{inc_id}\" connectingRoad=\"{out_id}\" junctionId=\"{jid}\">")
                    inc_right = [l for l in inc_lanes if l.startswith("-") is False and l != "0"]
                    inc_left = [l for l in inc_lanes if l.startswith("-")]
                    out_right = [l for l in out_lanes if l.startswith("-") is False and l != "0"]
                    out_left = [l for l in out_lanes if l.startswith("-")]
                    for i in range(min(len(inc_right), len(out_right))):
                        lines.append(f"      <laneLink from=\"{inc_right[i]}\" to=\"{out_right[i]}\"/>")
                    for i in range(min(len(inc_left), len(out_left))):
                        lines.append(f"      <laneLink from=\"{inc_left[i]}\" to=\"{out_left[i]}\"/>")
                    lines.append(f"    </connection>")
            lines.append(f"  </junction>")

        lines.append("</OpenDRIVE>")

        xml_content = "\n".join(lines)
        self._validate_opendrive(xml_content, road_lanes)

        # Post-process: detect shared geometric endpoints and promote them to explicit junctions
        xml_content = self._promote_shared_endpoints_to_junctions(xml_content, road_lanes)

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

    def _validate_opendrive(self, xml_content: str, road_lanes: Dict[str, List[str]]) -> None:
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Generated OpenDRIVE is not valid XML: {e}")

        errors: List[str] = []

        road_ids = set(road_lanes.keys())
        junction_ids = {j.get("id") for j in root.findall(".//junction")}

        for road in root.findall(".//road"):
            rid = road.get("id", "")
            if rid not in road_ids:
                errors.append(f"Road ID '{rid}' has no matching edge in graph")
                continue

            link = road.find("link")
            if link is not None:
                for pred in link.findall("predecessor"):
                    ref = pred.get("elementId")
                    if pred.get("elementType") == "road" and ref not in road_ids:
                        errors.append(f"Road '{rid}' predecessor references unknown road '{ref}'")
                    elif pred.get("elementType") == "junction" and ref not in junction_ids:
                        errors.append(f"Road '{rid}' predecessor references unknown junction '{ref}'")
                for succ in link.findall("successor"):
                    ref = succ.get("elementId")
                    if succ.get("elementType") == "road" and ref not in road_ids:
                        errors.append(f"Road '{rid}' successor references unknown road '{ref}'")
                    elif succ.get("elementType") == "junction" and ref not in junction_ids:
                        errors.append(f"Road '{rid}' successor references unknown junction '{ref}'")

            valid_lanes = set(road_lanes.get(rid, []))
            for lane in road.findall(".//lanes//lane"):
                lid = lane.get("id", "")
                if lid not in valid_lanes:
                    errors.append(f"Road '{rid}' declares lane '{lid}' but lane list does not include it")

        for junction in root.findall(".//junction"):
            jid = junction.get("id", "")
            for connection in junction.findall(".//connection"):
                inc = connection.get("incomingRoad", "")
                conn = connection.get("connectingRoad", "")
                if inc not in road_ids:
                    errors.append(f"Junction '{jid}' connection references unknown incoming road '{inc}'")
                if conn not in road_ids:
                    errors.append(f"Junction '{jid}' connection references unknown connecting road '{conn}'")
                inc_lanes = set(road_lanes.get(inc, []))
                conn_lanes = set(road_lanes.get(conn, []))
                for lanelink in connection.findall(".//laneLink"):
                    frm = lanelink.get("from")
                    to = lanelink.get("to")
                    if frm not in inc_lanes:
                        errors.append(f"Junction '{jid}' laneLink from='{frm}' references non-existent lane on road '{inc}'")
                    if to not in conn_lanes:
                        errors.append(f"Junction '{jid}' laneLink to='{to}' references non-existent lane on road '{conn}'")

        for signal in root.findall(".//signal"):
            road_id = signal.get("road")
            lane_id = signal.get("lane")
            if road_id and road_id not in road_ids:
                errors.append(f"Signal references unknown road '{road_id}'")
            if lane_id and lane_id not in set(road_lanes.get(road_id, [])):
                errors.append(f"Signal references non-existent lane '{lane_id}' on road '{road_id}'")

        for obj in root.findall(".//object"):
            road_id = obj.get("road")
            lane_id = obj.get("lane")
            if road_id and road_id not in road_ids:
                errors.append(f"Object references unknown road '{road_id}'")
            if lane_id and lane_id not in set(road_lanes.get(road_id, [])):
                errors.append(f"Object references non-existent lane '{lane_id}' on road '{road_id}'")

        if errors:
            raise ValueError(
                "OpenDRIVE generation produced dangling references:\n- " + "\n- ".join(errors)
            )

    def _promote_shared_endpoints_to_junctions(
        self, xml_content: str, road_lanes: Dict[str, List[str]]
    ) -> str:
        import math
        import xml.etree.ElementTree as ET
        from collections import defaultdict

        root = ET.fromstring(xml_content)
        roads = {r.get("id"): r for r in root.findall(".//road")}

        coord_map: Dict[Tuple[float, float], List[Tuple[str, bool]]] = defaultdict(list)
        for rid, road in roads.items():
            geom = road.find("geometry")
            if geom is None:
                continue
            x = float(geom.get("x", 0))
            y = float(geom.get("y", 0))
            length = float(geom.get("length", 0))
            hdg = float(geom.get("hdg", 0))
            ex = x + length * math.cos(hdg)
            ey = y + length * math.sin(hdg)
            coord_map[(round(x, 3), round(y, 3))].append((rid, True))
            coord_map[(round(ex, 3), round(ey, 3))].append((rid, False))

        junction_counter = 0
        for coord, items in coord_map.items():
            if len(items) < 2:
                continue

            incoming = [rid for rid, is_start in items if not is_start]
            outgoing = [rid for rid, is_start in items if is_start]

            if not incoming and not outgoing:
                continue

            if not incoming:
                incoming = [outgoing.pop(0)]
            if not outgoing:
                outgoing = [incoming.pop(0)]

            junction_counter += 1
            jid = f"j_shared_{junction_counter}"

            for rid in incoming:
                road = roads[rid]
                link = road.find("link")
                if link is None:
                    link = ET.SubElement(road, "link")
                pred = ET.SubElement(link, "predecessor")
                pred.set("elementType", "junction")
                pred.set("elementId", jid)
                road.set("junction", jid)

            for rid in outgoing:
                road = roads[rid]
                link = road.find("link")
                if link is None:
                    link = ET.SubElement(road, "link")
                succ = ET.SubElement(link, "successor")
                succ.set("elementType", "junction")
                succ.set("elementId", jid)
                road.set("junction", jid)

            junction = ET.SubElement(root, "junction")
            junction.set("name", "")
            junction.set("id", jid)
            junction.set("type", "priority")

            for inc_id in incoming:
                inc_lanes = road_lanes.get(inc_id, [])
                inc_right = [l for l in inc_lanes if not l.startswith("-") and l != "0"]
                inc_left = [l for l in inc_lanes if l.startswith("-")]
                for out_id in outgoing:
                    out_lanes = road_lanes.get(out_id, [])
                    out_right = [l for l in out_lanes if not l.startswith("-") and l != "0"]
                    out_left = [l for l in out_lanes if l.startswith("-")]
                    conn_id = hashlib.md5(f"{inc_id}_{out_id}".encode()).hexdigest()[:8]
                    connection = ET.SubElement(junction, "connection")
                    connection.set("id", conn_id)
                    connection.set("incomingRoad", inc_id)
                    connection.set("connectingRoad", out_id)
                    connection.set("junctionId", jid)
                    for i in range(min(len(inc_right), len(out_right))):
                        lane_link = ET.SubElement(connection, "laneLink")
                        lane_link.set("from", inc_right[i])
                        lane_link.set("to", out_right[i])
                    for i in range(min(len(inc_left), len(out_left))):
                        lane_link = ET.SubElement(connection, "laneLink")
                        lane_link.set("from", inc_left[i])
                        lane_link.set("to", out_left[i])

        return ET.tostring(root, encoding="unicode", xml_declaration=False)
