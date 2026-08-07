"""
Phase 13 tests — Event execution
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

def test_13_1_vehicle_braking_event():
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()

    vehicle_bp = bp_lib.find("vehicle.tesla.model3")
    vehicle = None
    for sp in spawn_points[:10]:
        vehicle = world.try_spawn_actor(vehicle_bp, sp)
        if vehicle:
            break
    check(vehicle is not None, "Vehicle spawned for braking event")

    if vehicle:
        vehicle.apply_control(carla.VehicleControl(throttle=0.5))
        time.sleep(1)
        vehicle.apply_control(carla.VehicleControl(brake=1.0))
        time.sleep(1)
        check(vehicle.is_alive, "Vehicle alive during braking")
        vehicle.destroy()

def test_13_2_weather_change_event():
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    weather = carla.WeatherParameters(
        cloudiness=80.0,
        precipitation=50.0,
        precipitation_deposits=50.0,
    )
    world.set_weather(weather)
    time.sleep(1)
    current = world.get_weather()
    check(current.cloudiness == 80.0, "Weather cloudiness applied")
    check(current.precipitation == 50.0, "Weather precipitation applied")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 13 - Event Execution Tests")
    print("=" * 65)
    try:
        test_13_1_vehicle_braking_event()
        test_13_2_weather_change_event()
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
