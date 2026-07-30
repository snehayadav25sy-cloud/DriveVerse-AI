import time

def load_simulation_map(client, map_name="Town01"):
    """
    Ensures the specified map is loaded in the CARLA simulator.
    """
    try:
        # Brief warm-up: give CARLA server a moment to fully initialise
        time.sleep(3)
        # Restore a long timeout before querying — connect() may have left it at 5s
        client.set_timeout(60.0)
        world = client.get_world()
        current_map = world.get_map().name
        
        # Maps in CARLA are named like 'Carla/Maps/Town01'
        if map_name in current_map:
            print(f"[CARLA Map] Map {map_name} is already loaded.")
            return world
            
        print(f"[CARLA Map] Loading map {map_name}...")
        # load_world() is long-running — 60s timeout is needed
        world = client.load_world(map_name)
        # Give simulator a moment to settle after map switch
        time.sleep(5)
        return world
    except Exception as e:
        raise RuntimeError(f"Failed to load map {map_name} in CARLA: {e}")
