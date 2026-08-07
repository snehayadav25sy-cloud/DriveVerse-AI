"""
client.py — connect to / disconnect from the CARLA simulator server.
"""

import os
import time
import importlib.metadata

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False

REQUIRED_VERSION = "0.9.16"

def connect(host=None, port=2000, timeout=60.0):
    if not _CARLA_AVAILABLE:
        raise ImportError(
            "The 'carla' package is not installed. "
            "Run: pip install carla==0.9.16"
        )

    installed = getattr(_carla, '__version__', None) or importlib.metadata.version('carla')
    if installed != REQUIRED_VERSION:
        raise RuntimeError(
            f"CARLA client version mismatch: found {installed}, "
            f"required {REQUIRED_VERSION}. Run: "
            f"pip install carla=={REQUIRED_VERSION} --force-reinstall"
        )

    host = host or os.environ.get("CARLA_HOST", "127.0.0.1")
    client = _carla.Client(host, port)
    client.set_timeout(timeout)

    try:
        server_version = client.get_server_version()
    except Exception as e:
        raise ConnectionError(
            f"Cannot reach CARLA at {host}:{port}. "
            f"Is CarlaUE4.exe running? Error: {e}"
        )

    if server_version != REQUIRED_VERSION:
        raise RuntimeError(
            f"CARLA server version mismatch: server reports "
            f"{server_version}, required {REQUIRED_VERSION}. Only "
            f"C:\\carla\\WindowsNoEditor\\CarlaUE4.exe should ever "
            f"be launched — check for other CARLA installs."
        )

    client.set_timeout(30.0)
    deadline = time.time() + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            world = client.get_world()
            print(f"[CARLA Client] get_world() succeeded on attempt {attempt}")
            return client, world
        except Exception as e:
            print(f"[CARLA Client] get_world() attempt {attempt}: {e} — retrying…")
            time.sleep(2)

    raise ConnectionError(
        f"CARLA get_world() did not succeed within {timeout}s at {host}:{port}"
    )


def disconnect(client, actors: list):
    """
    Destroy all spawned actors and release the client.
    Must always be called in a finally block to prevent actor leaks.
    """
    for actor in actors:
        try:
            if actor and actor.is_alive:
                actor.destroy()
                print(f"[CARLA Client] Destroyed actor {actor.type_id}")
        except Exception as e:
            print(f"[CARLA Client] Warning: could not destroy actor: {e}")
    print("[CARLA Client] Disconnected.")
