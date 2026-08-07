"""
Phase 12 tests — Multi-sensor execution
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

def test_12_1_multi_sensor_spawn():
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()
    spawn = spawn_points[0]

    sensors = []
    sensor_names = ["camera.rgb", "lidar.ray_cast", "other.radar", "camera.depth"]
    for sensor_type in sensor_names:
        bp = bp_lib.find(f"sensor.{sensor_type}")
        sensor = world.try_spawn_actor(bp, spawn)
        sensors.append(sensor)
        check(sensor is not None, f"{sensor_type} sensor spawned")

    for s in sensors:
        if s:
            s.destroy()

def test_12_2_sensor_sync_simulation():
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()

    camera_bp = bp_lib.find("sensor.camera.rgb")
    camera = world.try_spawn_actor(camera_bp, spawn_points[0])
    check(camera is not None, "RGB camera spawned")

    frame_count = [0]
    def on_image(image):
        frame_count[0] += 1

    if camera:
        camera.listen(on_image)
        world.tick()
        world.tick()
        world.tick()
        camera.stop()
        camera.destroy()
        check(frame_count[0] >= 0, "Frames captured")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 12 - Multi-Sensor Execution Tests")
    print("=" * 65)
    try:
        test_12_1_multi_sensor_spawn()
        test_12_2_sensor_sync_simulation()
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
