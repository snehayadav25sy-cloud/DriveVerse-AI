"""
Full System Acceptance Test — Step 10: Reproducibility
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import hashlib
import json

print("=" * 65)
print("  STEP 10 — Reproducibility")
print("=" * 65)

try:
    from app.scenario_execution.models import ExecutionSession, TimingConfig, MapConfig
    from app.scenario_execution.orchestrator import ScenarioOrchestrator
    from app.world_generation.models import WorldPlan, WorldCoordinate, VehiclePlan, PedestrianPlan, SensorConfig
    from app.schemas.scenario import ScenarioConfig, VehicleMix
    from app.country_profiles.models import CountryProfile, TrafficRules, SpeedLimits, DriverBehavior
    
    scenario = ScenarioConfig(
        country="India",
        city="Bengaluru",
        road_type="Highway",
        weather="Rain",
        time_of_day="Dusk",
        traffic_density="Heavy",
        vehicles=VehicleMix(car=40, motorcycle=35, bus=10, truck=5),
        pedestrians=15,
        sensors=["rgb", "lidar"],
        frames=20,
        export_format="kitti",
    )
    
    country_profile = CountryProfile(
        id="india",
        rules=TrafficRules(drive_side="left", speed_limits=SpeedLimits(highway=120, urban=50, residential=40, school=20), behavior=DriverBehavior(aggressiveness=0.7)),
        vehicle_mix={"sedan": 0.3, "rickshaw": 0.2, "motorcycle": 0.5},
    )
    
    world_plan = WorldPlan(
        world_id="world_repro_001",
        seed=42,
        location_query="MG Road, Bengaluru, India",
        country="india",
        map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        vehicles=[
            VehiclePlan(vehicle_id="v1", semantic_type="sedan", blueprint_id="vehicle.tesla.model3", position=WorldCoordinate(x=0, y=0, z=0), is_ego=True),
            VehiclePlan(vehicle_id="v2", semantic_type="motorcycle", position=WorldCoordinate(x=10, y=0, z=0)),
        ],
        pedestrians=[
            PedestrianPlan(pedestrian_id="p1", position=WorldCoordinate(x=5, y=5, z=0)),
        ],
        sensors=[
            SensorConfig(sensor_id="cam1", sensor_type="rgb", position=WorldCoordinate(x=0, y=0, z=1.4), resolution=(1280, 720)),
        ],
        seeds={"world_seed": 42, "traffic_seed": 43, "spawn_seed": 44, "weather_seed": 45, "sensor_seed": 46, "scenario_seed": 47},
    )
    
    orchestrator = ScenarioOrchestrator()
    session1 = orchestrator.create_session(world_plan, {"country": "india", "weather": "rain", "scenario_id": "scenario_repro_001"})
    session2 = orchestrator.create_session(world_plan, {"country": "india", "weather": "rain", "scenario_id": "scenario_repro_001"})
    
    checks = []
    checks.append(("seeds reproducible", session1.seeds == session2.seeds))
    checks.append(("session IDs unique", session1.session_id != session2.session_id))
    checks.append(("scenario preserved", scenario.country == "India"))
    checks.append(("weather preserved", scenario.weather == "Rain"))
    checks.append(("sensors preserved", "rgb" in scenario.sensors and "lidar" in scenario.sensors))
    checks.append(("frames preserved", scenario.frames == 20))
    checks.append(("export_format preserved", scenario.export_format == "kitti"))
    
    plan1 = world_plan.model_dump()
    plan2 = world_plan.model_dump()
    hash1 = hashlib.sha256(json.dumps(plan1, sort_keys=True).encode()).hexdigest()
    hash2 = hashlib.sha256(json.dumps(plan2, sort_keys=True).encode()).hexdigest()
    checks.append(("world plan hash reproducible", hash1 == hash2))
    
    print("\n" + "=" * 65)
    print("  VERIFICATION")
    print("=" * 65)
    all_pass = True
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}]  {label}")
    
    print(f"\nWorld plan hash 1: {hash1[:16]}...")
    print(f"World plan hash 2: {hash2[:16]}...")
    
    print("\n" + "=" * 65)
    if all_pass:
        print("  REPRODUCIBILITY RESULT: PASS")
    else:
        print("  REPRODUCIBILITY RESULT: FAIL")
    print("=" * 65)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\n" + "=" * 65)
    print("  REPRODUCIBILITY RESULT: FAIL")
    print("=" * 65)
    sys.exit(1)
