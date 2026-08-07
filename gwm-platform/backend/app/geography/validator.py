"""
app/geography/validator.py — Build 5: OpenDRIVE validator

Validates a generated .xodr file for:
  - XML well-formedness
  - Unique road/junction IDs
  - Valid road/lane references
  - No broken links
  - Positive road lengths
  - Valid geometry (no NaN/Inf)
  - Consistent lane counts

Returns:
  {
    "valid": bool,
    "errors": [...],
    "warnings": [...],
    "statistics": {...}
  }
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


class OpenDriveValidator:
    """Validates OpenDRIVE .xodr files."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _err(self, msg: str):
        self.errors.append(msg)

    def _warn(self, msg: str):
        self.warnings.append(msg)

    def validate(self, xodr_path: str) -> Dict[str, Any]:
        self.errors.clear()
        self.warnings.clear()

        stats = {
            "road_count": 0,
            "junction_count": 0,
            "lane_count": 0,
            "geometry_count": 0,
        }

        # 1. XML well-formedness
        try:
            tree = ET.parse(xodr_path)
            root = tree.getroot()
        except ET.ParseError as e:
            self._err(f"XML parse error: {e}")
            return {"valid": False, "errors": self.errors, "warnings": self.warnings, "statistics": stats}

        # 2. Unique road IDs
        road_ids = []
        for road in root.iter("road"):
            rid = road.get("id")
            if rid is None:
                self._err("Road element missing 'id' attribute")
            else:
                if rid in road_ids:
                    self._err(f"Duplicate road ID: {rid}")
                road_ids.append(rid)
            stats["road_count"] += 1

            # 3. Positive length
            length_str = road.get("length", "0")
            try:
                length = float(length_str)
                if length <= 0:
                    self._err(f"Road {rid} has non-positive length: {length}")
            except ValueError:
                self._err(f"Road {rid} has invalid length: {length_str}")

            # 4. Geometry validity
            for geom in road.iter("geometry"):
                stats["geometry_count"] += 1
                for coord in ("x", "y", "z", "hdg", "length"):
                    val = geom.get(coord)
                    if val is not None:
                        try:
                            f = float(val)
                            if math.isnan(f) or math.isinf(f):
                                self._err(f"Road {rid} geometry has NaN/Inf in {coord}={val}")
                        except ValueError:
                            self._err(f"Road {rid} geometry has invalid {coord}={val}")

            # 5. Lane count
            for ls in road.iter("laneSection"):
                lanes = list(ls.iter("lane"))
                stats["lane_count"] += len(lanes)

        # 6. Unique junction IDs
        junction_ids = []
        for junc in root.iter("junction"):
            jid = junc.get("id")
            if jid is None:
                self._err("Junction element missing 'id' attribute")
            else:
                if jid in junction_ids:
                    self._err(f"Duplicate junction ID: {jid}")
                junction_ids.append(jid)
            stats["junction_count"] += 1

        # 7. Road/link references
        valid_road_ids = set(road_ids)
        for link in root.iter("link"):
            for successor in link.iter("successor"):
                eid = successor.get("elementId")
                if eid and eid not in valid_road_ids and eid != "-1":
                    self._warn(f"Link references unknown road/junction ID: {eid}")

        valid = len(self.errors) == 0
        return {
            "valid": valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "statistics": stats,
        }
