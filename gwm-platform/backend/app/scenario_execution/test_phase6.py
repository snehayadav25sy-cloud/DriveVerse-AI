"""
Phase 6 tests — Sensor manager and synchronization
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.scenario_execution.sensors.sensor_manager import SensorManager
from app.scenario_execution.sensors.synchronization import SensorSynchronizer
from app.scenario_execution.models import SensorState, ExecutionCoordinate

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_6_1_sensor_manager():
    manager = SensorManager()
    sensor = SensorState(sensor_id="cam1", sensor_type="rgb", position=ExecutionCoordinate(x=0, y=0, z=1.4))
    manager.register(sensor)
    check(manager.get_sensor("cam1") is not None, "Sensor registered")
    manager.mark_frame("cam1", 0)
    check(manager.get_sensor("cam1").frame_count == 1, "Frame marked")

def test_6_2_sensor_sync():
    sensor_ids = ["cam1", "lidar1", "radar1"]
    sync = SensorSynchronizer(sensor_ids)
    sync.record_frame(0, "cam1", 0.0)
    sync.record_frame(0, "lidar1", 0.01)
    sync.record_frame(0, "radar1", 0.02)
    report = sync.validate()
    check(report.synchronized is True, "Frame 0 synchronized")
    sync.record_frame(1, "cam1", 0.1)
    sync.record_frame(1, "radar1", 0.12)
    report2 = sync.validate()
    check(report2.synchronized is False, "Frame 1 missing lidar")
    check(len(report2.missing_sensor_frames.get("lidar1", [])) == 1, "Missing frame detected")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 6 - Sensor Tests")
    print("=" * 65)
    try:
        test_6_1_sensor_manager()
        test_6_2_sensor_sync()
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
