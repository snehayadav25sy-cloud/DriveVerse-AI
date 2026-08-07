from app.country_profiles.models import TrafficRules, SpeedLimits, DriverBehavior, PedestrianSettings

def apply_modifiers_to_rules(
    rules: TrafficRules,
    pedestrians: PedestrianSettings,
    vehicle_mix: dict,
    modifiers: list
) -> tuple[TrafficRules, PedestrianSettings, dict]:
    """
    Applies scenario modifiers (rush_hour, night, construction, school)
    to traffic rules, behavior models, pedestrian configurations, and vehicle distributions.
    Returns: (mutated_rules, mutated_pedestrians, mutated_vehicle_mix)
    """
    # Create copies/clones of the configurations to mutate
    mut_limits = SpeedLimits(**rules.speed_limits.model_dump())
    mut_behavior = DriverBehavior(**rules.behavior.model_dump())
    mut_rules = TrafficRules(
        drive_side=rules.drive_side,
        speed_limits=mut_limits,
        signal_duration_s=rules.signal_duration_s,
        behavior=mut_behavior
    )
    mut_pedestrians = PedestrianSettings(**pedestrians.model_dump())
    mut_mix = dict(vehicle_mix)

    for mod in modifiers:
        mod_key = mod.lower().strip()
        if mod_key == "rush_hour":
            # rush_hour increases traffic density, makes drivers slightly more aggressive,
            # reduces stopping distance (closer tailgating), increases bus/HGV shares.
            mut_rules.behavior.aggressiveness = min(1.0, mut_rules.behavior.aggressiveness + 0.15)
            mut_rules.behavior.stopping_distance_m = max(1.5, mut_rules.behavior.stopping_distance_m - 0.5)
            mut_rules.behavior.horn_frequency = min(1.0, mut_rules.behavior.horn_frequency + 0.2)
            mut_rules.signal_duration_s = int(mut_rules.signal_duration_s * 1.3)
            # Increase bus and truck mix relative shares
            if "bus" in mut_mix:
                mut_mix["bus"] = mut_mix["bus"] * 1.5
            if "truck" in mut_mix:
                mut_mix["truck"] = mut_mix["truck"] * 1.3
        elif mod_key == "night":
            # night traffic has lower pedestrian density, slightly faster speeds (fewer bottlenecks),
            # but less aggressive driving.
            mut_pedestrians.density = max(0.0, mut_pedestrians.density * 0.1)
            mut_rules.behavior.aggressiveness = max(0.2, mut_rules.behavior.aggressiveness - 0.1)
            mut_rules.behavior.stopping_distance_m = mut_rules.behavior.stopping_distance_m + 0.5
            mut_rules.behavior.horn_frequency = max(0.0, mut_rules.behavior.horn_frequency - 0.05)
        elif mod_key == "construction":
            # construction limits speeds heavily, reduces lane discipline (merging bottlenecks),
            # increases truck/HGV presence.
            mut_rules.speed_limits.highway = int(mut_limits.highway * 0.6)
            mut_rules.speed_limits.urban = int(mut_limits.urban * 0.7)
            mut_rules.speed_limits.residential = int(mut_limits.residential * 0.8)
            mut_rules.behavior.lane_discipline = max(0.4, mut_rules.behavior.lane_discipline - 0.3)
            mut_rules.behavior.aggressiveness = min(1.0, mut_rules.behavior.aggressiveness + 0.05)
            if "truck" in mut_mix:
                mut_mix["truck"] = mut_mix["truck"] * 1.8
            if "hgv" in mut_mix:
                mut_mix["hgv"] = mut_mix["hgv"] * 2.0
        elif mod_key == "school":
            # school zones drop speed limit to 20, increase pedestrian density.
            mut_rules.speed_limits.urban = min(20, mut_limits.urban)
            mut_rules.speed_limits.residential = min(20, mut_limits.residential)
            mut_rules.speed_limits.school = 20
            mut_pedestrians.density = min(1.0, mut_pedestrians.density + 0.3)
            mut_rules.behavior.aggressiveness = max(0.1, mut_rules.behavior.aggressiveness - 0.2)
            mut_rules.behavior.stopping_distance_m = max(4.0, mut_rules.behavior.stopping_distance_m + 1.0)
            
    # Normalize vehicle mix back to shares
    total_mix = sum(mut_mix.values())
    if total_mix > 0:
        mut_mix = {k: v / total_mix for k, v in mut_mix.items()}
        
    return mut_rules, mut_pedestrians, mut_mix
