import carla

def attach_rgb_camera(world, vehicle):
    """
    Attaches an RGB camera sensor to the vehicle.
    Resolution: 1280x720, FOV: 90, Frame rate: 10 FPS (sensor_tick: 0.1)
    Mounted on the front windshield.
    """
    blueprint_library = world.get_blueprint_library()
    camera_bp = blueprint_library.find("sensor.camera.rgb")
    
    # Configure parameters
    camera_bp.set_attribute("image_size_x", "1280")
    camera_bp.set_attribute("image_size_y", "720")
    camera_bp.set_attribute("fov", "90")
    # 10 FPS -> tick every 0.1s
    camera_bp.set_attribute("sensor_tick", "0.1")
    
    # Placement: front windshield
    # x=1.5 (forward), y=0 (centered), z=1.4 (height)
    transform = carla.Transform(
        carla.Location(x=1.5, y=0.0, z=1.4),
        carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)
    )
    
    camera = world.spawn_actor(camera_bp, transform, attach_to=vehicle)
    print(f"[CARLA Camera] Attached camera to ego vehicle at transform {transform}")
    return camera
