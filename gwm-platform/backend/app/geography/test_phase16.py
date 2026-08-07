"""
Phase 16 tests — Minimal RGB capture (5-10 frames)

Run:
    python gwm-platform/backend/app/geography/test_phase16.py
"""

import sys
import os
import tempfile
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.simulators.carla.adapter import connect, disconnect, check_carla_available, CarlaAdapterError
from app.simulators.carla.camera import attach_rgb_camera

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def test_16_minimal_rgb_capture():
    """16: 1 vehicle, 1 RGB camera, 5-10 frames."""
    print("\n[16] Minimal RGB capture")
    available, err = check_carla_available()
    check(available is True, f"CARLA available: {available}")
    if not available:
        return

    client = None
    actors = []
    tmpdir = tempfile.mkdtemp(prefix="phase16_capture_")
    print(f"    Output dir: {tmpdir}")

    try:
        client, world = connect()
        bp_lib = world.get_blueprint_library()

        # Spawn vehicle
        vehicle_bp = bp_lib.find("vehicle.tesla.model3")
        if vehicle_bp is None:
            vehicle_bp = bp_lib.find("vehicle.*")
        sp = world.get_map().get_spawn_points()[0]
        vehicle = world.spawn_actor(vehicle_bp, sp)
        actors.append(vehicle)
        print(f"    Spawned vehicle: {vehicle.type_id}")

        # Attach RGB camera using adapter wrapper
        camera = attach_rgb_camera(world, vehicle)
        actors.append(camera)
        print(f"    Attached RGB camera")

        # Enable synchronous mode for deterministic capture
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.1
        world.apply_settings(settings)
        world.tick()

        frame_paths = []
        frame_count = 8

        def on_image(image):
            frame_idx = len(frame_paths)
            path = os.path.join(tmpdir, f"{frame_idx:06d}.png")
            image.save_to_disk(path)
            frame_paths.append(path)

        camera.listen(on_image)

        for i in range(frame_count):
            world.tick()
            time.sleep(0.05)

        camera.stop()
        settings.synchronous_mode = False
        world.apply_settings(settings)

        print(f"    Captured {len(frame_paths)} frames")
        check(5 <= len(frame_paths) <= 10, f"Captured {len(frame_paths)} frames (expected 5-10)")

        # Verify frames exist and are valid images
        valid_images = 0
        for path in frame_paths:
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img.load()
                    valid_images += 1
                except Exception:
                    pass
        print(f"    Valid image files: {valid_images}")
        check(valid_images >= 5, f"At least 5 valid frames on disk ({valid_images})")

        # Check frame size
        first_size = os.path.getsize(frame_paths[0]) if frame_paths else 0
        print(f"    First frame size: {first_size} bytes")
        check(first_size > 1000, f"Frame is non-trivial ({first_size} bytes)")

    except CarlaAdapterError as e:
        check(False, f"CARLA connection failed: {e}")
    except Exception as e:
        check(False, f"Unexpected error: {type(e).__name__}: {e}")
    finally:
        disconnect(client, actors)

    print(f"\n    NOTE: Capture performed on currently loaded CARLA map (not custom OpenDRIVE).")
    print(f"    Output: {tmpdir}")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 16 - Minimal RGB Capture")
    print("=" * 65)

    try:
        test_16_minimal_rgb_capture()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
