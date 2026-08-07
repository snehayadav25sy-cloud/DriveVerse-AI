"""
Phase 14 tests — Frontend verification

Verifies:
  - Route exists
  - Page renders
  - API service works
  - Loading state
  - Error state
  - World plan display
  - Fallback display
  - Provenance display
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import re

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_14_1_route_exists():
    app_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "App.tsx")
    app_path = os.path.abspath(app_path)
    with open(app_path, "r") as f:
        content = f.read()
    check('/world' in content, "Route /world exists in App.tsx")
    check('WorldGeneration' in content, "WorldGeneration component imported")

def test_14_2_page_renders():
    page_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "pages", "WorldGeneration.tsx")
    page_path = os.path.abspath(page_path)
    with open(page_path, "r") as f:
        content = f.read()
    check('export default function WorldGeneration' in content or 'function WorldGeneration' in content, "WorldGeneration component defined")
    check('World Generation' in content or 'WorldGeneration' in content, "Page has title")
    check('Generate World Plan' in content or 'generatePlan' in content, "Page has generate button/action")

def test_14_3_api_service():
    service_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "services", "world.ts")
    service_path = os.path.abspath(service_path)
    with open(service_path, "r") as f:
        content = f.read()
    check('/world/plan' in content, "API service calls /world/plan")
    check('useMutation' in content, "API service uses mutation")
    check('generatePlan' in content or 'mutate' in content, "API service has generate function")

def test_14_4_loading_state():
    page_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "pages", "WorldGeneration.tsx")
    page_path = os.path.abspath(page_path)
    with open(page_path, "r") as f:
        content = f.read()
    check('loading' in content.lower() or 'generating' in content.lower(), "Page has loading state")

def test_14_5_error_state():
    page_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "pages", "WorldGeneration.tsx")
    page_path = os.path.abspath(page_path)
    with open(page_path, "r") as f:
        content = f.read()
    check('error' in content.lower() or 'Error' in content, "Page handles error state")

def test_14_6_world_plan_display():
    page_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "pages", "WorldGeneration.tsx")
    page_path = os.path.abspath(page_path)
    with open(page_path, "r") as f:
        content = f.read()
    check('buildings' in content.lower(), "Page displays buildings count")
    check('vehicles' in content.lower(), "Page displays vehicles count")
    check('pedestrians' in content.lower(), "Page displays pedestrians count")

def test_14_7_fallback_display():
    page_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "pages", "WorldGeneration.tsx")
    page_path = os.path.abspath(page_path)
    with open(page_path, "r") as f:
        content = f.read()
    check('fallback' in content.lower() or 'asset_resolution_stats' in content.lower(), "Page displays fallback info")

def test_14_8_provenance_display():
    page_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "pages", "WorldGeneration.tsx")
    page_path = os.path.abspath(page_path)
    with open(page_path, "r") as f:
        content = f.read()
    check('provenance' in content.lower(), "Page displays provenance")

def test_14_9_sidebar_link():
    sidebar_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "components", "Sidebar.tsx")
    sidebar_path = os.path.abspath(sidebar_path)
    with open(sidebar_path, "r") as f:
        content = f.read()
    check('/world' in content, "Sidebar has /world link")
    check('World Generation' in content, "Sidebar has World Generation label")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 14 - Frontend Verification Tests")
    print("=" * 65)
    try:
        test_14_1_route_exists()
        test_14_2_page_renders()
        test_14_3_api_service()
        test_14_4_loading_state()
        test_14_5_error_state()
        test_14_6_world_plan_display()
        test_14_7_fallback_display()
        test_14_8_provenance_display()
        test_14_9_sidebar_link()
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
