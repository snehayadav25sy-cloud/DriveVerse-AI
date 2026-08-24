"""
app/simulators/carla/map_loader.py — Build 5: Load OpenDRIVE into CARLA

CARLA 0.9.16 OpenDRIVE loading strategies (in order of preference):
  1. Dynamic load via client.generate_opendrive_world(xodr_content, params)
     - WARNING: Known to cause simulator crashes/timeouts in CARLA 0.9.16
     - Requires CARLA to be running with an existing map loaded
  2. Static load via Maps/ directory + client.load_world(map_name)
     - Place .xodr in CARLA's Maps/ content directory
     - Launch CARLA with -map=MapName
     - Most reliable for production use
  3. Fallback to closest built-in CARLA town by road-type similarity
     - Used when custom OpenDRIVE loading fails
     - Dataset metadata MUST record this fallback

This module attempts strategies in order and reports honestly.
"""
from __future__ import annotations

import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple

from app.simulators.carla.adapter import connect, disconnect, check_carla_available, CarlaAdapterError, carla_alive


def _sanitize_map_name(xodr_path: str) -> str:
    """Derive a safe CARLA map name from an .xodr file path."""
    base = os.path.splitext(os.path.basename(xodr_path))[0]
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in base)


def _get_carla_maps_dir() -> str:
    """Return CARLA's Maps content directory."""
    carla_root = os.environ.get("CARLA_ROOT", r"C:\Users\sneha_nqarngz\Downloads\CARLA_0.9.16")
    return os.path.join(carla_root, "Content", "Maps")


def _fallback_town_for_road_type(road_type: Optional[str]) -> str:
    """Return the closest built-in CARLA town for a given road type."""
    road_type_lower = (road_type or "city").lower()
    if road_type_lower in ("highway", "motorway", "freeway", "rural"):
        return "Town03"
    elif road_type_lower in ("residential", "suburban", "suburb"):
        return "Town02"
    else:
        return "Town01"


def load_opendrive_map(
    xodr_path: str,
    host: Optional[str] = None,
    port: int = 2000,
    timeout: float = 60.0,
    road_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load an OpenDRIVE .xodr file into CARLA.

    Returns:
      {
        "success": bool,
        "world_name": str | None,
        "map_name": str | None,
        "spawn_point_count": int | None,
        "load_method": str | None,  # "dynamic" | "static" | "fallback_town"
        "error": str | None,
        "detail": str | None,
        "fallback_used": bool,
        "original_map_requested": str | None,
      }

    Strategy:
      1. Try dynamic load via client.generate_opendrive_world() with short timeout.
         WARNING: This is known to cause simulator instability in CARLA 0.9.16.
      2. Try static load via Maps/ directory + client.load_world().
      3. If both fail, fall back to closest built-in CARLA town.
         The dataset metadata MUST record this fallback.
    """
    result: Dict[str, Any] = {
        "success": False,
        "world_name": None,
        "map_name": None,
        "spawn_point_count": None,
        "load_method": None,
        "error": None,
        "detail": None,
        "fallback_used": False,
        "original_map_requested": _sanitize_map_name(xodr_path),
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

    with open(xodr_path, "r", encoding="utf-8") as f:
        xodr_content = f.read()

    client = None
    actors: List[Any] = []
    try:
        client, world = connect(host=host, port=port, timeout=timeout)
        result["world_name"] = world.get_map().name

        # Strategy 1: Dynamic OpenDRIVE load via generate_opendrive_world
        # WARNING: Known to cause crashes/timeouts in CARLA 0.9.16
        try:
            import carla as _carla
            params = _carla.OpendriveGenerationParameters(
                vertex_distance=2.0,
                max_road_length=500.0,
                wall_height=0.0,
                additional_width=0.6,
                smooth_junctions=True,
                enable_mesh_visibility=True,
            )
            print(f"[map_loader] Strategy 1: Attempting dynamic OpenDRIVE load...")
            client.set_timeout(15.0)
            world = client.generate_opendrive_world(xodr_content, params)
            if carla_alive(client):
                result["world_name"] = world.get_map().name
                result["success"] = True
                result["load_method"] = "dynamic"
                print(f"[map_loader] Strategy 1 succeeded: {result['world_name']}")
            else:
                raise RuntimeError("CARLA became unresponsive after generate_opendrive_world")
        except Exception as e:
            print(f"[map_loader] Strategy 1 failed: {type(e).__name__}: {e}")
            result["error"] = f"Dynamic OpenDRIVE load failed: {type(e).__name__}: {e}"
            result["detail"] = (
                "CARLA 0.9.16 generate_opendrive_world() failed or caused simulator instability. "
                "This is a known limitation with complex OpenDRIVE maps. "
                "Falling back to static Maps/ directory load."
            )

        # Strategy 2: Static load via Maps/ directory (if dynamic failed)
        if not result["success"]:
            try:
                print(f"[map_loader] Strategy 2: Attempting static Maps/ directory load...")
                maps_dir = _get_carla_maps_dir()
                os.makedirs(maps_dir, exist_ok=True)
                dest_path = os.path.join(maps_dir, f"{map_name}.xodr")
                shutil.copy2(xodr_path, dest_path)
                print(f"[map_loader] Copied .xodr to: {dest_path}")

                world = client.load_world(map_name)
                result["world_name"] = world.get_map().name
                result["success"] = True
                result["load_method"] = "static"
                result["detail"] = (
                    f"Loaded via Maps/ directory. "
                    f"To use this map persistently, launch CARLA with: -map={map_name}"
                )
                print(f"[map_loader] Strategy 2 succeeded: {result['world_name']}")
            except Exception as e:
                print(f"[map_loader] Strategy 2 failed: {type(e).__name__}: {e}")
                if result["error"] is None:
                    result["error"] = f"Static OpenDRIVE load failed: {type(e).__name__}: {e}"
                    result["detail"] = (
                        "CARLA 0.9.16 could not load the OpenDRIVE map via either "
                        "dynamic generation or static Maps/ directory. "
                        f"Place {xodr_path} in CARLA's Maps/ directory manually and "
                        f"restart CARLA with -map={map_name}"
                    )

        # Strategy 3: Fallback to built-in town (if both custom load methods failed)
        if not result["success"]:
            try:
                fallback_town = _fallback_town_for_road_type(road_type)
                print(f"[map_loader] Strategy 3: Falling back to built-in town: {fallback_town}")
                world = client.load_world(fallback_town)
                result["world_name"] = world.get_map().name
                result["success"] = True
                result["load_method"] = "fallback_town"
                result["fallback_used"] = True
                result["map_name"] = fallback_town
                result["detail"] = (
                    f"Custom OpenDRIVE map '{map_name}' could not be loaded. "
                    f"Fell back to built-in CARLA town '{fallback_town}' by road-type similarity. "
                    f"The dataset metadata MUST record that the geographic scenario was NOT used."
                )
                print(f"[map_loader] Strategy 3 succeeded (fallback): {result['world_name']}")
            except Exception as e:
                print(f"[map_loader] Strategy 3 failed: {type(e).__name__}: {e}")
                if result["error"] is None:
                    result["error"] = f"Fallback town load failed: {type(e).__name__}: {e}"

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
