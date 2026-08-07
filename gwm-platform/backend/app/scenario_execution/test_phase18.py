"""
Phase 18 tests — Build 3 regression: Prompt engine baseline
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.schemas.scenario import ScenarioConfig, VehicleMix

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_18_1_scenario_config():
    config = ScenarioConfig(
        country="India",
        city="Mumbai",
        road_type="Highway",
        weather="Rain",
        time_of_day="Night",
        traffic_density="Heavy",
        vehicles=VehicleMix(car=10, truck=2, bus=1, motorcycle=20),
        sensors=["rgb", "lidar", "radar", "depth"],
        frames=600,
    )
    check(config.country == "India", "Country")
    check(config.weather == "Rain", "Weather")
    check(config.traffic_density == "Heavy", "Traffic density")
    check(config.time_of_day == "Night", "Time of day")
    check(config.vehicles.motorcycle == 20, "Motorcycle count")
    check(config.frames == 600, "Frames")

def test_18_2_validation():
    try:
        ScenarioConfig(
            country="",
            city="",
            road_type="Invalid",
            weather="Invalid",
            time_of_day="Invalid",
            traffic_density="Invalid",
        )
        check(False, "Should reject invalid values")
    except Exception:
        check(True, "Rejects invalid values")

def test_18_3_to_job_params():
    config = ScenarioConfig(
        carla_map="Town01",
        sensors=["rgb", "lidar"],
        frames=500,
        export_format="kitti",
    )
    params = config.to_job_params()
    check(params["map"] == "Town01", "Map param")
    check(params["frames"] == 500, "Frames param")
    check(params["export_format"] == "kitti", "Export format")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 18 - Build 3 Regression Tests")
    print("=" * 65)
    try:
        test_18_1_scenario_config()
        test_18_2_validation()
        test_18_3_to_job_params()
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
