"""
worker/main.py — Build 2 multi-sensor job pipeline.

Job flow (progress milestones):
  0%  → job picked up, status=running
  10% → connected to CARLA + map loaded
  20% → ego vehicle spawned
  30% → all requested sensors attached + synchronous mode ready
  30–90% → capture ticking (per-frame progress)
  95% → dataset ZIPped
  100% → Dataset row written, job=completed

Note: CARLA must be running; failed connection marks job as status=failed.
"""

import time
import os
import sys
import zipfile
import json
import uuid
import math
from datetime import datetime, timezone

# ── path setup ───────────────────────────────────────────────────────────────
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

worker_path = os.path.dirname(__file__)
sys.path.insert(0, worker_path)

# Ensure dataset-engine is importable
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dataset-engine'))
sys.path.insert(0, engine_path)

from app.database.database import SessionLocal
from app.models.project import Project  # keeps relationship mapping alive
from app.models.job import Job
from app.models.dataset import Dataset
from app.models.prompt import Scenario as ScenarioModel
from app.country_profiles import registry, compiler
from app.country_profiles.models import RealityScenario
from simulator.carla.population import filter_spawn_points, spawn_background_traffic, spawn_pedestrian_crowd
import random

# ── CARLA simulator modules ──────────────────────────────────────────────────
try:
    from simulator.carla.client   import connect, disconnect
    from simulator.carla.maps     import load_simulation_map
    from simulator.carla.vehicle  import spawn_ego_vehicle
    from simulator.carla.camera   import attach_rgb_camera
    from simulator.carla.lidar    import attach_lidar
    from simulator.carla.capture  import MultiSensorCapture
    HAS_CARLA = True
except Exception as e:
    print(f"[Worker] CARLA modules could not be loaded: {e}")
    HAS_CARLA = False

# ── storage ──────────────────────────────────────────────────────────────────
STORAGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'storage')
os.makedirs(STORAGE_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Per-sensor metadata for the Dataset record (traceability)
# ─────────────────────────────────────────────────────────────────────────────
def _sensor_metadata(sensors: list) -> dict:
    meta = {}
    if 'rgb' in sensors:
        meta['rgb'] = {'resolution': '1280x720', 'fov': 90, 'fps': 10}
    if 'lidar' in sensors:
        meta['lidar'] = {'channels': 32, 'range_m': 100,
                         'rotation_frequency': 10, 'points_per_second': 100_000}
    return meta


# ─────────────────────────────────────────────────────────────────────────────
# Main generation function
# ─────────────────────────────────────────────────────────────────────────────
def generate_dataset_job(db, job) -> tuple:
    """
    Returns (zip_path, rgb_count, lidar_count, annotation_count)
    """
    job_id  = job.id
    frames  = int(job.frames) if job.frames else 500
    sensors = job.sensors if isinstance(job.sensors, list) else [job.sensors or 'rgb']
    sensors = [s.lower() for s in sensors]
    map_name = job.map if job.map else 'Town01'
    export_format = job.export_format if job.export_format else 'kitti'

    print(f"[Worker] Job {job_id} | map={map_name} | sensors={sensors} | frames={frames} | format={export_format}")

    output_dir  = os.path.join(STORAGE_DIR, f"dataset_{job_id}")
    os.makedirs(output_dir, exist_ok=True)

    # ── Build 4: Country scenario compilation ─────────────────────────────────
    scenario_row = db.query(ScenarioModel).filter(ScenarioModel.job_id == job.id).first()
    s_json = scenario_row.scenario_json if scenario_row else {}

    country = s_json.get("country") or "usa"
    weather = s_json.get("weather") or "sunny"
    traffic = s_json.get("traffic_density") or "normal"
    time_of_day = s_json.get("time_of_day") or "noon"
    road_type = s_json.get("road_type") or "highway"
    modifiers = s_json.get("modifiers") or []

    # Compile country configuration
    reality = RealityScenario(
        country=country,
        weather=weather,
        traffic=traffic,
        time_of_day=time_of_day,
        road_type=road_type,
        modifiers=modifiers
    )
    resolved, provenance = compiler.compile_scenario(reality)
    profile = registry.get_profile(country) or registry.get_profile("usa")

    print(f"[Worker] Compiled country profile '{country}': drive_side={resolved.drive_side}, difficulty={resolved.difficulty_score}")

    # ── progress helper ───────────────────────────────────────────────────────
    def set_progress(pct: float):
        job.progress = min(float(pct), 99.0)
        db.commit()

    def capture_progress(current, total):
        # maps 30% → 90% as frames accumulate
        pct = 30.0 + (current / total) * 60.0
        set_progress(pct)

    # ── attempt real CARLA capture ────────────────────────────────────────────
    success       = False
    actors        = []   # every spawned actor collected here for cleanup
    carla_client  = None
    carla_world   = None

    if HAS_CARLA:
        try:
            print("[Worker] Connecting to CARLA…")
            carla_client, carla_world = connect()
            carla_world = load_simulation_map(carla_client, map_name)
            set_progress(10)

            # Apply compiled weather settings
            import carla
            carla_weather = carla.WeatherParameters(
                cloudiness=resolved.weather.cloudiness,
                precipitation=resolved.weather.precipitation,
                precipitation_deposits=resolved.weather.precipitation_deposits,
                wind_intensity=resolved.weather.wind_intensity,
                sun_azimuth_angle=resolved.weather.sun_azimuth_angle,
                sun_altitude_angle=resolved.weather.sun_altitude_angle,
                fog_density=resolved.weather.fog_density,
                fog_distance=resolved.weather.fog_distance,
                wetness=resolved.weather.wetness
            )
            carla_world.set_weather(carla_weather)
            print(f"[Worker] Applied weather: precipitation={resolved.weather.precipitation}, fog={resolved.weather.fog_density}")

            # Programmatic spawn point filtering based on road_type
            filtered_spawns = filter_spawn_points(carla_world, road_type)
            ego_spawn = random.choice(filtered_spawns) if filtered_spawns else random.choice(carla_world.get_map().get_spawn_points())

            # Find appropriate ego blueprint
            ego_bp = carla_world.get_blueprint_library().find("vehicle.tesla.model3")
            vehicle = carla_world.spawn_actor(ego_bp, ego_spawn)
            vehicle.set_autopilot(True)
            actors.append(vehicle)
            set_progress(20)

            # Spawn background traffic and pedestrians matching target density/mix
            bg_vehicles = spawn_background_traffic(carla_world, carla_client, resolved, road_type, traffic)
            actors.extend(bg_vehicles)

            bg_walkers, bg_controllers = spawn_pedestrian_crowd(carla_world, carla_client, resolved, traffic)
            actors.extend(bg_walkers)
            actors.extend(bg_controllers)

            # Attach only the sensors requested for this job
            sensors_dict = {}
            if 'rgb' in sensors:
                cam = attach_rgb_camera(carla_world, vehicle)
                actors.append(cam)
                sensors_dict['rgb'] = cam

            if 'lidar' in sensors:
                lid = attach_lidar(carla_world, vehicle)
                actors.append(lid)
                sensors_dict['lidar'] = lid

            if 'radar' in sensors:
                from simulator.carla.radar import attach_radar
                rad = attach_radar(carla_world, vehicle)
                actors.append(rad)
                sensors_dict['radar'] = rad

            if 'depth' in sensors:
                from simulator.sensors.depth_camera import attach_depth_camera
                dep = attach_depth_camera(carla_world, vehicle, width=800, height=600)
                actors.append(dep)
                sensors_dict['depth'] = dep

            if 'semantic' in sensors:
                from simulator.sensors.semantic_camera import attach_semantic_camera
                sem = attach_semantic_camera(carla_world, vehicle, width=800, height=600)
                actors.append(sem)
                sensors_dict['semantic'] = sem

            if 'instance' in sensors:
                from simulator.sensors.instance_camera import attach_instance_camera
                ins = attach_instance_camera(carla_world, vehicle, width=800, height=600)
                actors.append(ins)
                sensors_dict['instance'] = ins

            if 'optical_flow' in sensors:
                from simulator.sensors.optical_flow import attach_optical_flow
                flo = attach_optical_flow(carla_world, vehicle, width=800, height=600)
                actors.append(flo)
                sensors_dict['optical_flow'] = flo

            # Multi-Camera Rig Support
            rig_mounts = {
                'camera_front': (1.5, 0.0, 1.4, 0.0),
                'camera_left': (0.0, -0.5, 1.4, -90.0),
                'camera_right': (0.0, 0.5, 1.4, 90.0),
                'camera_rear': (-1.5, 0.0, 1.4, 180.0),
            }
            for cam_name, (x, y, z, yaw) in rig_mounts.items():
                if cam_name in sensors:
                    cam_bp = carla_world.get_blueprint_library().find('sensor.camera.rgb')
                    cam_bp.set_attribute('image_size_x', '1280')
                    cam_bp.set_attribute('image_size_y', '720')
                    cam_bp.set_attribute('fov', '90')
                    trans = carla.Transform(carla.Location(x=x, y=y, z=z), carla.Rotation(pitch=0, yaw=yaw, roll=0))
                    c_actor = carla_world.spawn_actor(cam_bp, trans, attach_to=vehicle)
                    actors.append(c_actor)
                    sensors_dict[cam_name] = c_actor
                    print(f"[CARLA CameraRig] Attached {cam_name} at transform {trans}")

            set_progress(30)

            # MultiSensorCapture handles synchronous mode internally
            capture = MultiSensorCapture(
                sensors_dict, vehicle, output_dir, frames,
                progress_callback=capture_progress,
            )
            capture.start_capture(carla_world)
            success = True

        except Exception as e:
            print(f"[Worker] CARLA failed: {e}. Failing job.")
            job.status = 'failed'
            job.error = str(e)
            db.commit()
            return

        finally:
            # Destroy all actors regardless of success/failure
            if carla_client:
                disconnect(carla_client, actors)



    # ── run exporter ──────────────────────────────────────────────────────────
    if export_format == 'kitti':
        from calibration.intrinsics import compute_intrinsics
        from calibration.extrinsics import compute_extrinsics
        from exporters.kitti import export_kitti
        
        intr = compute_intrinsics(1280, 720, 90.0)
        ext = compute_extrinsics()
        export_kitti(output_dir, frames, intr, ext, sensors)
    elif export_format == 'nuscenes':
        from exporters.nuscenes.export import export_nuscenes
        export_nuscenes(output_dir, frames, sensors)
    elif export_format == 'coco':
        from exporters.coco.export import export_coco
        export_coco(output_dir, frames)

    # ── count rgb, lidar, annotation frames ──────────────────────────────────
    rgb_count = 0
    lidar_count = 0
    annotation_count = 0

    images_dir = os.path.join(output_dir, "images")
    if os.path.exists(images_dir):
        rgb_count = len([f for f in os.listdir(images_dir) if f.endswith(".png")])

    pc_dir = os.path.join(output_dir, "pointcloud")
    if os.path.exists(pc_dir):
        lidar_count = len([f for f in os.listdir(pc_dir) if f.endswith(".pcd")])

    labels_dir = os.path.join(output_dir, "labels")
    if os.path.exists(labels_dir):
        for f in os.listdir(labels_dir):
            if f.endswith(".txt"):
                try:
                    with open(os.path.join(labels_dir, f)) as lf:
                        annotation_count += len([line for line in lf if line.strip()])
                except Exception:
                    pass

    # ── write Build 4 scenario outputs ────────────────────────────────────────
    # 1. resolved_scenario.json
    with open(os.path.join(output_dir, "resolved_scenario.json"), "w") as f:
        json.dump(resolved.model_dump(), f, indent=2)

    # 2. country_profile.json
    with open(os.path.join(output_dir, "country_profile.json"), "w") as f:
        json.dump(profile.model_dump(), f, indent=2)

    # 3. compiler_log.json
    compiler_log = {
        "status": "success",
        "warnings": resolved.warnings,
        "errors": []
    }
    with open(os.path.join(output_dir, "compiler_log.json"), "w") as f:
        json.dump(compiler_log, f, indent=2)

    # 4. metadata.json
    meta = {
        "sensors":     sensors,
        "frame_count": frames,
        "map":         map_name,
        "export_format": export_format,
        "rgb_count": rgb_count,
        "lidar_count": lidar_count,
        "annotation_count": annotation_count,
        "spec":        _sensor_metadata(sensors),
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "difficulty_score": resolved.difficulty_score,
        "quality_score": resolved.quality_score,
        "warnings": resolved.warnings,
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # 5. provenance.json
    with open(os.path.join(output_dir, "provenance.json"), "w") as f:
        json.dump(provenance, f, indent=2)

    # 6. capabilities.json
    import yaml as _yaml
    capabilities_data = {}
    cap_path = os.path.abspath(os.path.join(backend_path, "app", "country_profiles", "capabilities.yaml"))
    try:
        if os.path.exists(cap_path):
            with open(cap_path, 'r') as cap_f:
                capabilities_data = _yaml.safe_load(cap_f)
    except Exception as e:
        capabilities_data = {"error": f"Failed to load capabilities: {e}"}
    with open(os.path.join(output_dir, "capabilities.json"), "w") as f:
        json.dump(capabilities_data, f, indent=2)

    # 7. quality.json
    quality_report = {
        "overall_quality_score": resolved.quality_score,
        "class_balance": resolved.vehicles,
        "pedestrian_density": resolved.pedestrians.density,
        "warnings_count": len(resolved.warnings)
    }
    with open(os.path.join(output_dir, "quality.json"), "w") as f:
        json.dump(quality_report, f, indent=2)

    # 8. difficulty.json
    difficulty_report = {
        "overall_difficulty_score": resolved.difficulty_score,
        "factors": {
            "weather": weather,
            "time_of_day": time_of_day,
            "traffic_density": traffic,
            "road_type": road_type,
            "modifiers": modifiers
        }
    }
    with open(os.path.join(output_dir, "difficulty.json"), "w") as f:
        json.dump(difficulty_report, f, indent=2)

    # ── ZIP ───────────────────────────────────────────────────────────────────
    set_progress(90)
    zip_path = os.path.join(STORAGE_DIR, f"dataset_{job_id}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                fp = os.path.join(root, file)
                zf.write(fp, os.path.relpath(fp, output_dir))

    # Clean up expanded dataset dir
    import shutil
    try:
        shutil.rmtree(output_dir)
    except Exception as e:
        print(f"[Worker] Warning: could not remove temp dir: {e}")

    set_progress(95)
    print(f"[Worker] Job {job_id} complete -> {zip_path}")
    return zip_path, rgb_count, lidar_count, annotation_count


# ─────────────────────────────────────────────────────────────────────────────
# Polling loop
# ─────────────────────────────────────────────────────────────────────────────
def poll_jobs():
    print("[Worker] Polling for queued jobs…")
    while True:
        try:
            db  = SessionLocal()
            job = db.query(Job).filter(Job.status == 'queued').first()

            if job:
                job_id = job.id
                print(f"[Worker] Picked up job {job_id}")
                job.status   = 'running'
                job.progress = 0.0
                db.commit()

                sensors = job.sensors if isinstance(job.sensors, list) else [job.sensors or 'rgb']
                export_format = job.export_format if job.export_format else 'kitti'

                try:
                    output_path, rgb_cnt, lid_cnt, ann_cnt = generate_dataset_job(db, job)

                    dataset = Dataset(
                        id=str(uuid.uuid4()),
                        job_id=job_id,
                        sensors=sensors,
                        sensor_metadata=_sensor_metadata(sensors),
                        path=output_path,
                        frame_count=int(job.frames) if job.frames else 500,
                        rgb_count=rgb_cnt,
                        lidar_count=lid_cnt,
                        annotation_count=ann_cnt,
                        export_format=export_format,
                    )
                    db.add(dataset)

                    job.status      = 'completed'
                    job.output_path = output_path
                    job.progress    = 100.0
                    db.commit()

                except Exception as e:
                    print(f"[Worker] Job {job_id} failed: {e}")
                    try:
                        db.rollback()
                    except Exception:
                        pass
                    try:
                        job.status = 'failed'
                        db.commit()
                    except Exception as commit_err:
                        print(f"[Worker] Could not mark job failed in DB: {commit_err}")

            db.close()

        except Exception as e:
            print(f"[Worker] Polling error: {e}")

        time.sleep(3)


if __name__ == "__main__":
    poll_jobs()
