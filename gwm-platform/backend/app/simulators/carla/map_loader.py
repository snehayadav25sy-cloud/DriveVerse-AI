"""
app/simulators/carla/map_loader.py — Build 5: Load OpenDRIVE into CARLA

WARNING: CARLA 0.9.16 does NOT expose a Python API to dynamically load
an arbitrary .xodr file at runtime. The standard path is:
  1. Place the .xodr in CARLA's Maps content directory
  2. Launch CARLA with -map=MapName
  3. client.load_world("MapName")

This module attempts the best available approach and reports honestly.
"""

from __future__ import annotations

import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple

from app.simulators.carla.adapter import connect, disconnect, check_carla_available, CarlaAdapterError


def _sanitize_map_name(xodr_path: str) -> str:
    """Derive a safe CARLA map name from an .xodr file path."""
    base = os.path.splitext(os.path.basename(xodr_path))[0]
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in base)


def load_opendrive_map(
    xodr_path: str,
    host: Optional[str] = None,
    port: int = 2000,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """
    Load an OpenDRIVE .xodr file into CARLA.

    Returns:
      {
        "success": bool,
        "world_name": str | None,
        "map_name": str | None,
        "spawn_point_count": int | None,
        "error": str | None,
        "detail": str | None,
      }

    Note: In CARLA 0.9.16, true dynamic OpenDRIVE loading from Python
    is not supported. This function attempts the closest available path
    and reports the exact CARLA response.
    """
    result: Dict[str, Any] = {
        "success": False,
        "world_name": None,
        "map_name": None,
        "spawn_point_count": None,
        "error": None,
        "detail": None,
    }

    available, err = check_carla_available()
    if not available:
        result["error"] = err
        result["detail"] = "CARLA client package unavailable"
        return result

    if not os.path.exists(xodr_path):
        result["error"] = f"OpenDRIVE file not found: {xodr_path}"
        return result

    map_name = _sanitize_map_name(xodr_path)
    result["map_name"] = map_name

    client = None
    actors: List[Any] = []
    try:
        client, world = connect(host=host, port=port, timeout=timeout)
        result["world_name"] = world.get_map().name

        # Attempt to load the custom map
        try:
            world = client.load_world(map_name)
            result["world_name"] = world.get_map().name
            result["success"] = True
        except Exception as e:
            # CARLA 0.9.16 likely rejects unknown map names here
            result["error"] = f"CARLA load_world failed: {type(e).__name__}: {e}"
            result["detail"] = (
                "CARLA 0.9.16 does not support dynamic OpenDRIVE loading from Python. "
                "The .xodr must be placed in CARLA's Maps directory and CARLA restarted "
                "with -map=MapName before client.load_world() can succeed."
            )

        # Count spawn points
        try:
            spawn_points = world.get_map().get_spawn_points()
            result["spawn_point_count"] = len(spawn_points)
        except Exception as e:
            result["spawn_point_count"] = 0
            if result["error"] is None:
                result["error"] = f"Failed to get spawn points: {e}"

    except CarlaAdapterError as e:
        result["error"] = str(e)
        result["detail"] = "CARLA connection failed"
    except Exception as e:
        result["error"] = f"Unexpected error: {type(e).__name__}: {e}"
    finally:
        disconnect(client, actors)

    return result
