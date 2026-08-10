"""
app/simulators/carla/adapter.py — Build 5: CARLA client adapter

Reuses the version-checked connect() logic from Build 2/3.
This is the ONLY place in app/geography/ and app/simulators/ that may
import carla directly.

Architecture integrity rule:
  - app/geography/ must NEVER import carla.
  - All CARLA interactions go through this adapter.
"""

from __future__ import annotations

import importlib.metadata
import os
import time
from typing import List, Optional, Tuple

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False

REQUIRED_VERSION = "0.9.16"


class CarlaAdapterError(Exception):
    """Base error for CARLA adapter failures."""


def check_carla_available() -> Tuple[bool, Optional[str]]:
    """Return (available, error_reason)."""
    if not _CARLA_AVAILABLE:
        return False, "carla package not installed (pip install carla==0.9.16)"
    installed = getattr(_carla, '__version__', None) or importlib.metadata.version('carla')
    if installed != REQUIRED_VERSION:
        return False, f"CARLA client version mismatch: found {installed}, required {REQUIRED_VERSION}"
    return True, None


def connect(
    host: Optional[str] = None,
    port: int = 2000,
    timeout: float = 60.0,
) -> Tuple[any, any]:
    """
    Version-checked CARLA connect.
    Returns (client, world) on success.
    Raises CarlaAdapterError on failure.
    """
    available, err = check_carla_available()
    if not available:
        raise CarlaAdapterError(err)

    host = host or os.environ.get("CARLA_HOST", "127.0.0.1")
    client = _carla.Client(host, port)
    client.set_timeout(timeout)

    try:
        server_version = client.get_server_version()
    except Exception as e:
        raise CarlaAdapterError(
            f"Cannot reach CARLA at {host}:{port}. Is CarlaUE4.exe running? Error: {e}"
        )

    if server_version != REQUIRED_VERSION:
        raise CarlaAdapterError(
            f"CARLA server version mismatch: server reports {server_version}, "
            f"required {REQUIRED_VERSION}. Only "
            f"C:\\carla\\WindowsNoEditor\\CarlaUE4.exe should ever "
            f"be launched."
        )

    client.set_timeout(30.0)
    deadline = time.time() + timeout
    attempt = 0
    last_err = None
    while time.time() < deadline:
        attempt += 1
        try:
            world = client.get_world()
            return client, world
        except Exception as e:
            last_err = e
            time.sleep(2)

    raise CarlaAdapterError(
        f"CARLA get_world() did not succeed within {timeout}s at {host}:{port}: {last_err}"
    )


def disconnect(client, actors: List[any]):
    """Destroy all spawned actors and release the client."""
    for actor in actors:
        try:
            if actor and actor.is_alive:
                actor.destroy()
        except Exception:
            pass
    try:
        client = None
    except Exception:
        pass


def carla_alive(client, timeout: float = 5.0) -> bool:
    """
    Health-check: return True if the CARLA server is still responsive.
    """
    if client is None:
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            client.get_server_version()
            return True
        except Exception:
            time.sleep(1)
    return False


def make_weather(
    cloudiness: float = 0.0,
    precipitation: float = 0.0,
    precipitation_deposits: float = 0.0,
    wind_intensity: float = 0.0,
    fog_density: float = 0.0,
    fog_distance: float = 100.0,
    sun_altitude_angle: float = 45.0,
    wetness: float = 0.0,
) -> any:
    """
    Create a CARLA WeatherParameters object.
    This function lives in the adapter so that app/geography/ tests
    never need to import carla directly.
    """
    return _carla.WeatherParameters(
        cloudiness=cloudiness,
        precipitation=precipitation,
        precipitation_deposits=precipitation_deposits,
        wind_intensity=wind_intensity,
        fog_density=fog_density,
        fog_distance=fog_distance,
        sun_altitude_angle=sun_altitude_angle,
        wetness=wetness,
    )
