"""
Phase 10 tests — CARLA adapter structure and version check
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

def test_10_1_carla_version():
    adapter_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "adapters", "carla_adapter.py"))
    with open(adapter_path, "r") as f:
        content = f.read()
    check("0.9.16" in content, "CARLA 0.9.16 version referenced")
    check("REQUIRED_CARLA_VERSION" in content, "Required version constant defined")

def test_10_2_no_carla_imports_outside_adapter():
    execution_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
    for root, dirs, files in os.walk(execution_dir):
        for f in files:
            if f.endswith('.py') and not f.startswith('test_') and 'carla_adapter' not in f:
                filepath = os.path.join(root, f)
                with open(filepath, 'r') as fp:
                    content = fp.read()
                if 'import carla' in content or 'from carla' in content:
                    check(False, f"CARLA import found in {filepath}")
    check(True, "No CARLA imports outside adapter")

def test_10_3_adapter_methods():
    adapter_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "adapters", "carla_adapter.py"))
    with open(adapter_path, "r") as f:
        content = f.read()
    methods = ["connect", "disconnect", "load_map", "spawn_actor", "destroy_actor", "attach_sensor", "apply_weather", "tick", "health_check", "cleanup"]
    for method in methods:
        check(f"def {method}" in content, f"Method {method} exists")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 10 - CARLA Adapter Tests")
    print("=" * 65)
    try:
        test_10_1_carla_version()
        test_10_2_no_carla_imports_outside_adapter()
        test_10_3_adapter_methods()
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
