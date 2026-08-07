"""
Phase 11 tests — Sensor realism models
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.sensor_realism.models import RGBConfig, LiDARConfig, RadarConfig, DepthConfig, SensorRealismConfig

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_11_1_rgb_config():
    cfg = RGBConfig(resolution=(1920, 1080), fov=90.0)
    check(cfg.resolution == (1920, 1080), "RGB resolution")
    check(cfg.fov == 90.0, "RGB FOV")

def test_11_2_lidar_config():
    cfg = LiDARConfig(channels=64, range_m=150.0, points_per_second=500000)
    check(cfg.channels == 64, "LiDAR channels")
    check(cfg.range_m == 150.0, "LiDAR range")
    check(cfg.points_per_second == 500000, "LiDAR points per second")

def test_11_3_radar_config():
    cfg = RadarConfig(range_m=200.0, velocity_noise=0.1)
    check(cfg.range_m == 200.0, "Radar range")
    check(cfg.velocity_noise == 0.1, "Radar velocity noise")

def test_11_4_depth_config():
    cfg = DepthConfig(depth_noise=0.05, max_range=100.0, invalid_pixel_probability=0.01)
    check(cfg.depth_noise == 0.05, "Depth noise")
    check(cfg.invalid_pixel_probability == 0.01, "Invalid pixel probability")

def test_11_5_sensor_realism_config():
    cfg = SensorRealismConfig()
    check(cfg.rgb.fov == 90.0, "Default RGB FOV")
    check(cfg.lidar.channels == 32, "Default LiDAR channels")
    check(cfg.radar.range_m == 100.0, "Default Radar range")
    check(cfg.depth.max_range == 100.0, "Default Depth range")

def test_11_6_invalid_rgb_fov():
    try:
        RGBConfig(fov=200.0)
        check(False, "Should reject FOV > 180")
    except Exception as e:
        check(True, f"Rejected invalid FOV: {type(e).__name__}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 11 - Sensor Realism Tests")
    print("=" * 65)
    try:
        test_11_1_rgb_config()
        test_11_2_lidar_config()
        test_11_3_radar_config()
        test_11_4_depth_config()
        test_11_5_sensor_realism_config()
        test_11_6_invalid_rgb_fov()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

