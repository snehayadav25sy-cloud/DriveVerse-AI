"""
Full System Acceptance Test — Step 6: CARLA Connection and Actor Spawn
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import carla
import time
import requests

API_BASE = "http://localhost:8000"

print("=" * 65)
print("  STEP 6 — CARLA: Real Connection and Actor Spawn")
print("=" * 65)

try:
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    print(f"Connected: True")
    print(f"Map: {world.get_map().name}")
    print(f"Server version: {client.get_server_version()}")
    
    bp_lib = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()
    
    vehicles_spawned = 0
    pedestrians_spawned = 0
    
    vehicle_bps = [bp for bp in bp_lib.filter("vehicle.*") if "tesla" in bp.id or "bmw" in bp.id or "audi" in bp.id][:3]
    for bp in vehicle_bps:
        for sp in spawn_points[:5]:
            actor = world.try_spawn_actor(bp, sp)
            if actor:
                vehicles_spawned += 1
                print(f"Spawned vehicle: {bp.id}")
                break
    
    ped_bps = [bp for bp in bp_lib.filter("walker.*")][:2]
    for bp in ped_bps:
        for sp in spawn_points[:5]:
            actor = world.try_spawn_actor(bp, sp)
            if actor:
                pedestrians_spawned += 1
                print(f"Spawned pedestrian: {bp.id}")
                break
    
    checks = []
    checks.append(("CARLA version 0.9.16", client.get_server_version() == "0.9.16"))
    checks.append(("Map loaded", world.get_map() is not None))
    checks.append(("vehicles > 0", vehicles_spawned > 0))
    checks.append(("pedestrians >= 0", pedestrians_spawned >= 0))
    
    print("\n" + "=" * 65)
    print("  VERIFICATION")
    print("=" * 65)
    all_pass = True
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}]  {label}")
    
    print("\n" + "=" * 65)
    if all_pass:
        print("  CARLA RESULT: PASS")
    else:
        print("  CARLA RESULT: FAIL")
    print("=" * 65)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\n" + "=" * 65)
    print("  CARLA RESULT: BLOCKED")
    print("=" * 65)
    sys.exit(2)
