"""
Phase 11 tests — CARLA smoke execution
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import time
import carla

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_11_1_carla_connection():
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    check(world is not None, "Connected to CARLA world")
    check("Town" in world.get_map().name, "Map loaded")

def test_11_2_spawn_actors():
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()
    vehicle_bp = bp_lib.find("vehicle.tesla.model3")
    spawn_points = world.get_map().get_spawn_points()
    check(len(spawn_points) > 0, "Spawn points available")
    vehicle = None
    for sp in spawn_points[:10]:
        vehicle = world.try_spawn_actor(vehicle_bp, sp)
        if vehicle:
            break
    check(vehicle is not None, "Vehicle spawned")
    if vehicle:
        vehicle.destroy()

def test_11_3_spawn_sensor():
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()
    camera_bp = bp_lib.find("sensor.camera.rgb")
    spawn_points = world.get_map().get_spawn_points()
    camera = world.try_spawn_actor(camera_bp, spawn_points[0])
    check(camera is not None, "Camera sensor spawned")
    if camera:
        camera.destroy()

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 11 - CARLA Smoke Execution Tests")
    print("=" * 65)
    try:
        test_11_1_carla_connection()
        test_11_2_spawn_actors()
        test_11_3_spawn_sensor()
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
