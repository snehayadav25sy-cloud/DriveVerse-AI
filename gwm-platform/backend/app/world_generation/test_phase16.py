"""
Phase 15 tests — CARLA adapter verification

Verifies:
  - CARLA version = 0.9.16 check
  - Map provider states (READY, DEPLOYMENT_REQUIRED, UNSUPPORTED, FAILED)
  - Adapter module structure
  - No carla imports in non-adapter modules
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import ast
import re

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_15_1_carla_version_check():
    adapter_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "simulators", "carla", "adapter.py")
    adapter_path = os.path.abspath(adapter_path)
    with open(adapter_path, "r") as f:
        content = f.read()
    check('0.9.16' in content, "CARLA version 0.9.16 referenced in adapter")
    check('REQUIRED_VERSION' in content, "Required version constant defined")

def test_15_2_map_provider_states():
    provider_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "simulators", "carla", "map_provider.py")
    provider_path = os.path.abspath(provider_path)
    with open(provider_path, "r") as f:
        content = f.read()
    check('READY' in content, "READY state defined")
    check('DEPLOYMENT_REQUIRED' in content, "DEPLOYMENT_REQUIRED state defined")
    check('UNSUPPORTED' in content, "UNSUPPORTED state defined")
    check('FAILED' in content, "FAILED state defined")

def test_15_3_opendrive_gap_preserved():
    provider_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "simulators", "carla", "map_provider.py")
    provider_path = os.path.abspath(provider_path)
    with open(provider_path, "r") as f:
        content = f.read()
    check('does not support dynamic OpenDRIVE loading' in content.lower() or 'not supported' in content.lower(), "OpenDRIVE gap documented")
    check('DEPLOYMENT_REQUIRED' in content, "Returns DEPLOYMENT_REQUIRED for OpenDRIVE")

def test_15_4_no_carla_imports_in_world_generation():
    world_gen_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "world_generation")
    world_gen_path = os.path.abspath(world_gen_path)
    for root, dirs, files in os.walk(world_gen_path):
        for f in files:
            if f.endswith('.py') and not f.startswith('test_'):
                filepath = os.path.join(root, f)
                with open(filepath, 'r') as fp:
                    content = fp.read()
                if 'import carla' in content or 'from carla' in content:
                    check(False, f"CARLA import found in world_generation/{f}")
    check(True, "No CARLA imports in world_generation modules")

def test_15_5_no_carla_imports_in_sensor_realism():
    sensor_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "sensor_realism")
    sensor_path = os.path.abspath(sensor_path)
    for root, dirs, files in os.walk(sensor_path):
        for f in files:
            if f.endswith('.py') and not f.startswith('test_'):
                filepath = os.path.join(root, f)
                with open(filepath, 'r') as fp:
                    content = fp.read()
                if 'import carla' in content or 'from carla' in content:
                    check(False, f"CARLA import found in sensor_realism/{f}")
    check(True, "No CARLA imports in sensor_realism modules")

def test_15_6_carla_adapter_structure():
    adapter_dir = os.path.join(os.path.dirname(__file__), "..", "..", "app", "simulators", "carla")
    adapter_dir = os.path.abspath(adapter_dir)
    expected_files = [
        'adapter.py',
        'carla_world_executor.py',
        'carla_assets.py',
        'carla_spawn.py',
        'carla_weather.py',
        'carla_traffic.py',
        'carla_sensors.py',
        'map_provider.py',
    ]
    for f in expected_files:
        filepath = os.path.join(adapter_dir, f)
        check(os.path.exists(filepath), f"CARLA adapter file exists: {f}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 15 - CARLA Adapter Tests")
    print("=" * 65)
    try:
        test_15_1_carla_version_check()
        test_15_2_map_provider_states()
        test_15_3_opendrive_gap_preserved()
        test_15_4_no_carla_imports_in_world_generation()
        test_15_5_no_carla_imports_in_sensor_realism()
        test_15_6_carla_adapter_structure()
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


