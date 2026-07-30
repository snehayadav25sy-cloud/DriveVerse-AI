import random

def spawn_ego_vehicle(world, vehicle_filter="vehicle.tesla.model3"):
    """
    Spawns a single ego vehicle at a random spawn point and enables autopilot.
    Returns the spawned vehicle actor.
    """
    blueprint_library = world.get_blueprint_library()
    blueprints = blueprint_library.filter(vehicle_filter)
    
    if not blueprints:
        # Fallback to any vehicle if specific blueprint is not found
        print(f"[CARLA Vehicle] Blueprint {vehicle_filter} not found. Falling back to any vehicle.")
        blueprints = blueprint_library.filter("vehicle.*")
        
    blueprint = random.choice(blueprints)
    
    # Get random spawn point
    spawn_points = world.get_map().get_spawn_points()
    if not spawn_points:
        raise RuntimeError("No spawn points found on the map.")
        
    spawn_point = random.choice(spawn_points)
    
    # Spawn vehicle
    vehicle = world.spawn_actor(blueprint, spawn_point)
    print(f"[CARLA Vehicle] Spawned ego vehicle: {vehicle.type_id} at {spawn_point.location}")
    
    # Enable autopilot
    try:
        vehicle.set_autopilot(True)
        print("[CARLA Vehicle] Autopilot enabled.")
    except Exception as e:
        print(f"[CARLA Vehicle] Warning: Could not enable autopilot natively: {e}")
        
    return vehicle
