"""
Phase 19 tests — Build 2 regression: Sensor/capture baseline
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.sensor_realism.models import SensorRealismConfig, RGBConfig, LiDARConfig, RadarConfig, DepthConfig

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_19_1_sensor_configs():
    rgb = RGBConfig(resolution=(1280, 720), fov=90.0)
    check(rgb.resolution == (1280, 720), "RGB resolution")
    check(rgb.fov == 90.0, "RGB FOV")

    lidar = LiDARConfig(channels=64, range_m=100.0)
    check(lidar.channels == 64, "LiDAR channels")

    radar = RadarConfig(range_m=150.0)
    check(radar.range_m == 150.0, "Radar range")

    depth = DepthConfig(max_range=100.0)
    check(depth.max_range == 100.0, "Depth max range")

def test_19_2_sensor_realism_config():
    config = SensorRealismConfig(
        rgb=RGBConfig(resolution=(1280, 720)),
        lidar=LiDARConfig(channels=64, range_m=100.0),
        radar=RadarConfig(range_m=150.0),
        depth=DepthConfig(max_range=100.0),
    )
    check(config.rgb.resolution == (1280, 720), "RGB resolution in config")
    check(config.lidar.channels == 64, "LiDAR channels in config")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 19 - Build 2 Regression Tests")
    print("=" * 65)
    try:
        test_19_1_sensor_configs()
        test_19_2_sensor_realism_config()
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
