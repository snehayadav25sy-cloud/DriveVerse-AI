"""
Phase 16 tests — Build 5 integration: Map deployer
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import tempfile
from app.scenario_execution.deployment.map_deployer import MapDeployer
from app.scenario_execution.models import MapConfig, MapProviderType

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_16_1_town_map_available():
    deployer = MapDeployer()
    config = MapConfig(provider=MapProviderType.TOWN, map_name="Town01", deployment_required=False)
    result = deployer.resolve(config)
    check(result.status.value == "AVAILABLE", "Town map is AVAILABLE")
    check(result.map_name == "Town01", "Map name correct")

def test_16_2_opendrive_deployment_required():
    with tempfile.NamedTemporaryFile(suffix=".xodr", delete=False) as tmp:
        tmp.write(b"<OpenDRIVE></OpenDRIVE>")
        artifact_path = tmp.name
    try:
        deployer = MapDeployer()
        config = MapConfig(
            provider=MapProviderType.OPENDRIVE_ARTIFACT,
            map_name="custom_map",
            deployment_required=True,
            artifact_path=artifact_path,
            deployment_instructions=["copy artifact", "restart CARLA"],
        )
        result = deployer.resolve(config)
        check(result.status.value == "DEPLOYMENT_REQUIRED", "OpenDRIVE returns DEPLOYMENT_REQUIRED")
        check(len(result.instructions) > 0, "Instructions provided")
        check("restart" in " ".join(result.instructions).lower(), "Instructions mention restart")
    finally:
        os.unlink(artifact_path)

def test_16_3_opendrive_missing_artifact():
    deployer = MapDeployer()
    config = MapConfig(
        provider=MapProviderType.OPENDRIVE_ARTIFACT,
        map_name="custom_map",
        deployment_required=True,
        artifact_path="/nonexistent/path/map.xodr",
    )
    result = deployer.resolve(config)
    check(result.status.value == "UNAVAILABLE", "Missing artifact is UNAVAILABLE")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 16 - Build 5 Integration Tests")
    print("=" * 65)
    try:
        test_16_1_town_map_available()
        test_16_2_opendrive_deployment_required()
        test_16_3_opendrive_missing_artifact()
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
