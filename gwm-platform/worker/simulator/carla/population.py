import random
import sys
import os

try:
    import carla
except ImportError:
    pass

DENSITY_VEHICLES = {
    "none": 0,
    "light": 15,
    "medium": 40,
    "heavy": 80,
    "gridlock": 130
}

DENSITY_PEDESTRIANS = {
    "none": 0,
    "light": 5,
    "medium": 15,
    "heavy": 40,
    "gridlock": 70
}

def filter_spawn_points(world, road_type: str):
    """
    Filters spawn points on Town01-Town03 based on road_type (Highway, Residential, Intersection, City).
    """
    map_obj = world.get_map()
    all_spawns = map_obj.get_spawn_points()
    
    if not road_type or not all_spawns:
        return all_spawns
        
    road_type = road_type.lower().strip()
    filtered = []
    
    for sp in all_spawns:
        wp = map_obj.get_waypoint(sp.location)
        if not wp:
            continue
            
        if road_type in ["intersection", "junction"]:
            if wp.is_junction:
                filtered.append(sp)
        elif road_type == "highway":
            # Highways typically have wider lanes or specific road ids on Town01-Town03
            if wp.lane_width > 3.5 or (wp.lane_type == carla.LaneType.Driving and wp.road_id in [1, 2, 3, 4]):
                filtered.append(sp)
        elif road_type in ["residential", "suburban", "city"]:
            if not wp.is_junction:
                filtered.append(sp)
        else:
            filtered.append(sp)
            
    if not filtered:
        return all_spawns
    return filtered

def spawn_background_traffic(world, client, resolved_scenario, road_type: str, traffic_density: str) -> list:
    """
    Spawns background traffic matching the resolved blueprint distribution, speed limit,
    and behavior parameters.
    """
    actors = []
    density_key = traffic_density.lower().strip()
    target_count = DENSITY_VEHICLES.get(density_key, 30)
    
    if target_count <= 0:
        return actors

    # Resolve blueprint probability distribution
    vehicle_mix = resolved_scenario.vehicles
    bps_list = list(vehicle_mix.keys())
    weights = list(vehicle_mix.values())
    
    if not bps_list or sum(weights) == 0:
        blueprint_library = world.get_blueprint_library()
        blueprints = blueprint_library.filter("vehicle.*")
        bps_list = [bp.id for bp in blueprints]
        weights = [1.0 / len(bps_list)] * len(bps_list)

    # Filter spawn points
    spawn_points = filter_spawn_points(world, road_type)
    random.shuffle(spawn_points)

    # Setup Traffic Manager
    traffic_manager = client.get_trafficmanager(8000)
    traffic_manager.set_synchronous_mode(True)
    
    # Configure global behaviors
    stopping_dist = resolved_scenario.behavior.stopping_distance_m
    traffic_manager.set_global_distance_to_leading_vehicle(stopping_dist)
    
    # Aggressiveness maps to speed limit offset (percentage speed difference)
    # Positive means drive slower, negative means drive faster
    aggr = resolved_scenario.behavior.aggressiveness
    speed_limit_offset = (0.5 - aggr) * 30.0
    traffic_manager.set_global_percentage_speed_difference(speed_limit_offset)

    # Keep drive side rules
    # If drive side is left, instruct vehicles to stay left (keep_right = False or stay left offset)
    drive_left = (resolved_scenario.drive_side == "left")

    for i, sp in enumerate(spawn_points):
        if len(actors) >= target_count:
            break
            
        bp_id = random.choices(bps_list, weights=weights)[0]
        bp = world.get_blueprint_library().find(bp_id)
        
        if bp.has_attribute('color'):
            color = random.choice(bp.get_attribute('color').recommended_values)
            bp.set_attribute('color', color)
            
        bp.set_attribute('role_name', 'autopilot')
        
        vehicle = world.try_spawn_actor(bp, sp)
        if vehicle:
            vehicle.set_autopilot(True, traffic_manager.get_port())
            
            # Apply individual behaviors
            traffic_manager.update_vehicle_lights(vehicle, True)
            
            # Lane discipline / weaving behavior
            if resolved_scenario.behavior.lane_discipline < 0.6:
                # low discipline -> frequent lane changes
                traffic_manager.random_left_lanechange_percentage(vehicle, 30)
                traffic_manager.random_right_lanechange_percentage(vehicle, 30)
                
            # If left-side driving, set keep right rule percentage to high negative or adjust lane preferences
            if drive_left:
                # keep right rule = -100% means keep left
                traffic_manager.keep_right_rule_percentage(vehicle, -100.0)
            else:
                traffic_manager.keep_right_rule_percentage(vehicle, 100.0)
                
            actors.append(vehicle)
            
    print(f"[CARLA Population] Spawned {len(actors)} background vehicles (Target: {target_count})")
    return actors

def spawn_pedestrian_crowd(world, client, resolved_scenario, traffic_density: str) -> tuple[list, list]:
    """
    Spawns walkers and AI controllers matching the pedestrian density and walking speed.
    """
    walkers = []
    controllers = []
    
    density_key = traffic_density.lower().strip()
    target_count = int(DENSITY_PEDESTRIANS.get(density_key, 15) * resolved_scenario.pedestrians.density)
    
    if target_count <= 0:
        return walkers, controllers
        
    walker_bps = world.get_blueprint_library().filter("walker.pedestrian.*")
    if not walker_bps:
        return walkers, controllers

    locations = []
    for _ in range(target_count * 2):
        loc = world.get_random_location_from_navigation()
        if loc:
            locations.append(loc)

    for loc in locations:
        if len(walkers) >= target_count:
            break
            
        bp = random.choice(walker_bps)
        if bp.has_attribute('is_invincible'):
            bp.set_attribute('is_invincible', 'false')
            
        trans = carla.Transform(location=loc)
        walker = world.try_spawn_actor(bp, trans)
        if walker:
            controller_bp = world.get_blueprint_library().find('controller.ai.walker')
            controller = world.try_spawn_actor(controller_bp, carla.Transform(), attach_to=walker)
            if controller:
                walkers.append(walker)
                controllers.append(controller)

    # Initialize walkers
    world.tick()
    for controller in controllers:
        controller.start()
        controller.go_to_location(world.get_random_location_from_navigation())
        controller.set_max_speed(resolved_scenario.pedestrians.walking_speed)

    print(f"[CARLA Population] Spawned {len(walkers)} walkers and {len(controllers)} controllers (Target: {target_count})")
    return walkers, controllers
