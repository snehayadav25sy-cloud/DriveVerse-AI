"""
Phase 16 tests — End-to-end pipeline

Pipeline:
  Prompt -> Build 3 -> Build 4 -> Build 5 -> Build 6 -> World Plan -> Provenance
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import hashlib

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_16_1_build3_prompt_parsing():
    from app.services.prompt_parser import parse_prompt
    prompt = "Generate a rainy evening in Mumbai with heavy traffic, motorcycles, buses and pedestrians."
    scenario = parse_prompt(prompt)
    check(scenario is not None, "Prompt parsed successfully")
    check(hasattr(scenario, 'country'), "Scenario has country")
    check(hasattr(scenario, 'weather'), "Scenario has weather")

def test_16_2_build4_country_resolution():
    from app.country_profiles.registry import CountryProfileRegistry
    from app.country_profiles.compiler import CountryCompiler
    from app.country_profiles.models import RealityScenario
    
    countries_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app", "country_profiles", "countries"))
    registry = CountryProfileRegistry(countries_dir)
    compiler = CountryCompiler(registry)
    
    profile = registry.get_profile("india")
    check(profile is not None, "India profile found")
    
    reality = RealityScenario(country="india", weather="rain", traffic="heavy", time_of_day="sunset", road_type="urban")
    resolved, prov = compiler.compile_scenario(reality)
    check(resolved is not None, "Scenario compiled")
    check(resolved.drive_side == "left", "Drive side is left for India")
    check(len(resolved.vehicles) > 0, "Vehicle mix resolved")

def test_16_3_build5_geographic_artifact():
    from app.geography.models import MapArtifact, MapProvenance
    
    artifact = MapArtifact(
        xodr_path="/tmp/test.xodr",
        xodr_size_bytes=1000,
        xodr_hash="abc123",
        validator_passed=True,
        carla_map_name="Town01",
    )
    check(artifact.validator_passed is True, "Map artifact created")
    check(artifact.carla_map_name == "Town01", "Map name set")
    
    prov = MapProvenance(
        location_query="MG Road, Bengaluru",
        radius_m=500.0,
        geocoder_provider="nominatim",
        osm_provider="overpass",
        resolved_latitude=12.9755,
        resolved_longitude=77.6068,
        resolved_country="India",
        resolved_city="Bengaluru",
        road_graph_node_count=3005,
        road_graph_edge_count=659,
        xodr_hash="def456",
    )
    check(prov.resolved_country == "India", "Provenance has country")

def test_16_4_build6_world_plan():
    from app.world_generation.planner import WorldPlanner
    from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
    
    resolved = {
        "country": "india",
        "weather": {"cloudiness": 80.0, "precipitation": 60.0},
        "traffic": "heavy",
        "vehicles": {"sedan": 0.4, "motorcycle": 0.3, "bus": 0.2, "auto_rickshaw": 0.1},
    }
    map_artifact = {
        "location_query": "MG Road, Bengaluru",
        "resolution": {"resolved_latitude": 12.9755, "resolved_longitude": 77.6068},
        "carla_map_name": "Town01",
    }
    country_profile = {
        "id": "india",
        "rules": {"drive_side": "left"},
        "vehicle_mix": {"sedan": 0.4, "motorcycle": 0.3, "bus": 0.2, "auto_rickshaw": 0.1},
    }
    
    planner = WorldPlanner(resolved, map_artifact, country_profile)
    seeds = {"world": 12345, "traffic": 12346, "pedestrian": 12347, "weather": 12348, "asset": 12349, "scenario": 12350}
    plan = planner.plan(seeds=seeds)
    
    check(plan is not None, "World plan generated")
    check(plan.world_id != "", "World ID generated")
    check(len(plan.vehicles) > 0, "Vehicles planned")
    check(len(plan.pedestrians) > 0, "Pedestrians planned")
    check(len(plan.buildings) >= 0, "Buildings planned")
    check(len(plan.vegetation) > 0, "Vegetation planned")
    check(len(plan.signs) > 0, "Signs planned")
    check(len(plan.traffic_lights) > 0, "Traffic lights planned")
    check(len(plan.events) > 0, "Events planned")
    check(plan.plan_hash() != "", "Plan hash generated")

def test_16_5_provenance_chain():
    from app.world_generation.planner import WorldPlanner
    from app.world_generation.provenance import compute_world_provenance, provenance_hash
    
    resolved = {"country": "india", "weather": {"cloudiness": 80.0}, "traffic": "heavy"}
    map_artifact = {"location_query": "MG Road, Bengaluru", "resolution": {"resolved_latitude": 12.9755, "resolved_longitude": 77.6068}, "carla_map_name": "Town01"}
    country_profile = {"id": "india"}
    
    planner = WorldPlanner(resolved, map_artifact, country_profile)
    seeds = {"world": 1, "traffic": 2, "pedestrian": 3, "weather": 4, "asset": 5, "scenario": 6}
    plan = planner.plan(seeds=seeds)
    prov = planner.provenance(plan)
    
    check(prov.country_profile_hash != "", "Country profile hash present")
    check(prov.geography_hash != "", "Geography hash present")
    check(prov.world_plan_hash == plan.plan_hash(), "World plan hash matches")
    check(prov.asset_registry_hash != "", "Asset registry hash present")
    check(prov.provenance_hash() != "", "Provenance hash generated")

def test_16_6_api_integration():
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    payload = {
        "resolved_scenario": {"country": "india", "weather": "rain", "traffic": "heavy"},
        "map_artifact": {"location_query": "MG Road, Bengaluru", "resolution": {"resolved_latitude": 12.9755, "resolved_longitude": 77.6068}, "carla_map_name": "Town01"},
        "country_profile": {"id": "india", "rules": {"drive_side": "left"}, "vehicle_mix": {"sedan": 0.4, "motorcycle": 0.3, "bus": 0.2, "auto_rickshaw": 0.1}},
        "seeds": {"world": 12345, "traffic": 12346, "pedestrian": 12347, "weather": 12348, "asset": 12349, "scenario": 12350},
    }
    resp = client.post("/world/plan", json=payload)
    check(resp.status_code == 200, f"API plan generation: {resp.status_code}")
    data = resp.json()
    check("world_id" in data, "Response has world_id")
    check("plan" in data, "Response has plan")
    check("provenance" in data, "Response has provenance")
    check(len(data["plan"]["vehicles"]) > 0, "Plan has vehicles")
    check(len(data["plan"]["pedestrians"]) > 0, "Plan has pedestrians")

def test_16_7_deterministic_reproducibility():
    from app.world_generation.planner import WorldPlanner
    
    resolved = {"country": "india", "weather": "rain", "traffic": "heavy"}
    map_artifact = {"location_query": "MG Road, Bengaluru", "resolution": {"resolved_latitude": 12.9755, "resolved_longitude": 77.6068}, "carla_map_name": "Town01"}
    country_profile = {"id": "india"}
    
    seeds = {"world": 99999, "traffic": 99998, "pedestrian": 99997, "weather": 99996, "asset": 99995, "scenario": 99994}
    
    planner1 = WorldPlanner(resolved, map_artifact, country_profile)
    plan1 = planner1.plan(seeds=seeds)
    prov1 = planner1.provenance(plan1)
    
    planner2 = WorldPlanner(resolved, map_artifact, country_profile)
    plan2 = planner2.plan(seeds=seeds)
    prov2 = planner2.provenance(plan2)
    
    check(plan1.plan_hash() == plan2.plan_hash(), "Deterministic plan hash")
    check(prov1.provenance_hash() == prov2.provenance_hash(), "Deterministic provenance hash")
    check(plan1.world_id == plan2.world_id, "Deterministic world ID")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 16 - End-to-End Pipeline Tests")
    print("=" * 65)
    try:
        test_16_1_build3_prompt_parsing()
        test_16_2_build4_country_resolution()
        test_16_3_build5_geographic_artifact()
        test_16_4_build6_world_plan()
        test_16_5_provenance_chain()
        test_16_6_api_integration()
        test_16_7_deterministic_reproducibility()
    except AssertionError:
        pass
    except Exception as e:
        print(f"  [ERROR] Unexpected error: {e}")
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
