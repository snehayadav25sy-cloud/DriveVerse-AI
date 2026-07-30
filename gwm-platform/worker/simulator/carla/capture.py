"""
capture.py — multi-sensor capture orchestration for CARLA.

Design decisions
----------------
1. ImageCapture (Build 1 class) is kept UNCHANGED.
   Any code that imports it continues to work without modification.

2. MultiSensorCapture (Build 2) wraps the synchronous-mode loop:
   - ONLY supports 'rgb' and 'lidar' sensors (radar, depth, etc., are deferred).
   - Generates the clean directory layout:
     - images/{frame:06d}.png
     - pointcloud/{frame:06d}.pcd (ASCII PCD)
     - labels/{frame:06d}.txt (internal taxonomy labels)
     - metadata/{frame:06d}.json (per-frame simulation metadata)
     - calibration/calib.json (written once per dataset)

3. Synchronous mode responsibility:
   MultiSensorCapture.start_capture() enables synchronous mode BEFORE starting
   the capture loop and always disables it in the finally block. This guarantees
   the world is returned to async mode even if an exception is raised.
"""

import os
import sys
import math
import time
import struct
import threading

# Dynamic path setup to ensure dataset-engine modules are importable
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_ENGINE = os.path.join(_ROOT, "dataset-engine")
if _ENGINE not in sys.path:
    sys.path.insert(0, _ENGINE)

from capture.rgb import save_rgb_from_path
from capture.lidar import save_lidar, parse_carla_lidar_raw
from annotations.classify import classify_actors
from annotations.tracking import ObjectTracker
from annotations.bbox import filter_and_project
from calibration.intrinsics import compute_intrinsics
from calibration.extrinsics import compute_extrinsics
from metadata.frame_metadata import write_frame_metadata
from exporters.internal import write_labels, write_calibration


# ---------------------------------------------------------------------------
# Build 1 — kept fully intact, zero changes
# ---------------------------------------------------------------------------

class ImageCapture:
    """
    Listens for camera frames, saves them as PNGs, and manages the capture lifecycle.
    (Build 1 — unchanged)
    """
    def __init__(self, output_dir, limit=500, progress_callback=None):
        self.output_dir = output_dir
        self.limit = limit
        self.progress_callback = progress_callback
        self.count = 0
        self.finished = False
        
        os.makedirs(self.output_dir, exist_ok=True)

    def on_frame(self, carla_image):
        if self.finished:
            return
            
        # Save to disk using CARLA's helper (saves as PNG if extension is png)
        filename = os.path.join(self.output_dir, f"{self.count:06d}.png")
        carla_image.save_to_disk(filename)
        
        self.count += 1
        
        if self.progress_callback:
            self.progress_callback(self.count, self.limit)
            
        if self.count >= self.limit:
            self.finished = True
            print(f"[CARLA Capture] Completed capture of {self.limit} frames.")


# ---------------------------------------------------------------------------
# Build 2 — multi-sensor synchronous capture
# ---------------------------------------------------------------------------

class MultiSensorCapture:
    """
    Orchestrates synchronous multi-sensor capture in CARLA.
    Only supports 'rgb' and 'lidar'.
    """

    def __init__(self, sensors: dict, ego_vehicle, output_dir: str, frames: int,
                 progress_callback=None):
        """
        Parameters
        ----------
        sensors           : dict  {sensor_name: carla.Sensor}
                            Keys must be a subset of {"rgb", "lidar"}.
        ego_vehicle       : carla.Vehicle  Ego vehicle actor.
        output_dir        : str   root directory for this dataset
        frames            : int   number of synchronous ticks to capture
        progress_callback : callable(current_frame, total_frames) | None
        """
        self.sensors = sensors
        self.ego_vehicle = ego_vehicle
        self.output_dir = output_dir
        self.frames = frames
        self.progress_callback = progress_callback

        # Initialize tracking & calibration params
        self.tracker = ObjectTracker()
        self.camera_params = compute_intrinsics(
            image_width=1280,
            image_height=720,
            fov_h_degrees=90.0,
        )

        # Synchronisation queues & sync engine
        import queue
        from simulator.carla.sync_engine import SensorSyncEngine
        self._queues = {k: queue.Queue() for k in sensors}
        self.sync_engine = SensorSyncEngine(list(sensors.keys()))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_capture(self, world):
        """
        Enable synchronous mode, listen on all sensors, tick the world
        *self.frames* times, then disable synchronous mode.
        """
        # 1. Enable synchronous mode FIRST before listening
        original_settings = world.get_settings()
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.1
        world.apply_settings(settings)
        print("[CARLA Capture] Synchronous mode enabled (10 FPS).")

        # Tick once so synchronous mode takes effect on CARLA server
        world.tick()

        # 2. Register callbacks
        for name, sensor in self.sensors.items():
            sensor.listen(self._queues[name].put)

        # 3. Drain any initial queue items to start clean
        import queue
        for q in self._queues.values():
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break

        try:
            for frame_id in range(self.frames):
                # Advance the simulation by exactly one fixed step
                world.tick()

                snapshot = {}
                for name in self.sensors:
                    try:
                        snapshot[name] = self._queues[name].get(timeout=5.0)
                    except queue.Empty:
                        snapshot[name] = None

                # ── 1. Save RGB Frame ─────────────────────────────────────────
                if "rgb" in snapshot and snapshot["rgb"] is not None:
                    # Save to a temporary file, then copy via dataset-engine helper
                    temp_path = os.path.join(self.output_dir, f"_temp_{frame_id}.png")
                    snapshot["rgb"].save_to_disk(temp_path)
                    save_rgb_from_path(temp_path, frame_id, self.output_dir)
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

                # ── 2. Save LiDAR Frame ───────────────────────────────────────
                if "lidar" in snapshot and snapshot["lidar"] is not None:
                    points = parse_carla_lidar_raw(bytes(snapshot["lidar"].raw_data))
                    save_lidar(points, frame_id, self.output_dir)

                # ── 2b. Save Radar Detections ──────────────────────────────────
                if "radar" in snapshot and snapshot["radar"] is not None:
                    radar_csv_path = os.path.join(self.output_dir, "radar.csv")
                    file_exists = os.path.exists(radar_csv_path)
                    with open(radar_csv_path, "a") as rf:
                        if not file_exists:
                            rf.write("frame_id,depth,azimuth,altitude,velocity\n")
                        for detect in snapshot["radar"]:
                            rf.write(f"{frame_id},{detect.depth:.4f},{detect.azimuth:.4f},{detect.altitude:.4f},{detect.velocity:.4f}\n")

                # ── 2c. Save Depth Frame ──────────────────────────────────────
                if "depth" in snapshot and snapshot["depth"] is not None:
                    depth_dir = os.path.join(self.output_dir, "depth")
                    os.makedirs(depth_dir, exist_ok=True)
                    import numpy as np
                    from PIL import Image
                    from simulator.sensors.depth_camera import parse_carla_depth
                    depth_meters = parse_carla_depth(bytes(snapshot["depth"].raw_data), width=800, height=600)
                    depth_uint16 = (depth_meters * 100.0).clip(0, 65535).astype(np.uint16)
                    depth_img = Image.fromarray(depth_uint16)
                    depth_img.save(os.path.join(depth_dir, f"{frame_id:06d}.png"))

                # ── 2d. Save Semantic Frame ───────────────────────────────────
                if "semantic" in snapshot and snapshot["semantic"] is not None:
                    sem_dir = os.path.join(self.output_dir, "semantic")
                    os.makedirs(sem_dir, exist_ok=True)
                    import numpy as np
                    from PIL import Image
                    from simulator.sensors.semantic_camera import parse_carla_semantic
                    sem_rgb = parse_carla_semantic(bytes(snapshot["semantic"].raw_data), width=800, height=600)
                    sem_img = Image.fromarray(sem_rgb)
                    sem_img.save(os.path.join(sem_dir, f"{frame_id:06d}.png"))

                # ── 2e. Save Instance Frame ───────────────────────────────────
                if "instance" in snapshot and snapshot["instance"] is not None:
                    inst_dir = os.path.join(self.output_dir, "instance")
                    os.makedirs(inst_dir, exist_ok=True)
                    import numpy as np
                    from PIL import Image
                    from simulator.sensors.instance_camera import parse_carla_instance
                    inst_rgb, _ = parse_carla_instance(bytes(snapshot["instance"].raw_data), width=800, height=600)
                    inst_img = Image.fromarray(inst_rgb)
                    inst_img.save(os.path.join(inst_dir, f"{frame_id:06d}.png"))

                # ── 2f. Save Optical Flow Frame ───────────────────────────────
                if "optical_flow" in snapshot and snapshot["optical_flow"] is not None:
                    flow_dir = os.path.join(self.output_dir, "optical_flow")
                    os.makedirs(flow_dir, exist_ok=True)
                    import numpy as np
                    from simulator.sensors.optical_flow import parse_carla_optical_flow
                    flow_array = parse_carla_optical_flow(bytes(snapshot["optical_flow"].raw_data), width=800, height=600)
                    np.save(os.path.join(flow_dir, f"{frame_id:06d}.npy"), flow_array)

                # ── 2g. Save Multi-Camera Rig Frames ──────────────────────────
                for cam_key in ["camera_front", "camera_left", "camera_right", "camera_rear"]:
                    if cam_key in snapshot and snapshot[cam_key] is not None:
                        cam_dir = os.path.join(self.output_dir, cam_key)
                        os.makedirs(cam_dir, exist_ok=True)
                        from PIL import Image
                        import numpy as np
                        bgra = np.frombuffer(bytes(snapshot[cam_key].raw_data), dtype=np.uint8).reshape((720, 1280, 4))
                        rgb = bgra[:, :, :3][:, :, ::-1]
                        Image.fromarray(rgb).save(os.path.join(cam_dir, f"{frame_id:06d}.png"))

                # ── 2h. Record Timestamp Sync ────────────────────────────────
                w_snap = world.get_snapshot()
                sim_time = w_snap.timestamp.elapsed_seconds if hasattr(w_snap, 'timestamp') else time.time()
                self.sync_engine.record_frame(frame_id, sim_time, snapshot)

                # ── 3. Actor Discovery & Annotation ───────────────────────────
                ego_trans = self.ego_vehicle.get_transform()
                ego_loc = ego_trans.location
                ego_rot = ego_trans.rotation
                ego_pose = {
                    "x": ego_loc.x,
                    "y": ego_loc.y,
                    "z": ego_loc.z,
                    "yaw": ego_rot.yaw,
                }

                carla_actors = world.get_actors()
                raw_actors = []
                for actor in carla_actors:
                    if actor.id == self.ego_vehicle.id:
                        continue
                    if "vehicle" in actor.type_id or "walker" in actor.type_id:
                        loc = actor.get_location()
                        ext = actor.bounding_box.extent
                        vel = actor.get_velocity()
                        raw_actors.append({
                            "actor_id": actor.id,
                            "blueprint_id": actor.type_id,
                            "location": {"x": loc.x, "y": loc.y, "z": loc.z},
                            "extent": {"x": ext.x, "y": ext.y, "z": ext.z},
                            "velocity": {"x": vel.x, "y": vel.y, "z": vel.z},
                        })

                classified = classify_actors(raw_actors)
                tracked = self.tracker.assign(classified)

                annotated = []
                for actor in tracked:
                    res = filter_and_project(actor, ego_pose, self.camera_params, max_range=100.0)
                    if res is not None:
                        annotated.append(res)

                write_labels(frame_id, annotated, self.output_dir)

                # ── 4. Metadata ───────────────────────────────────────────────
                ego_vel = self.ego_vehicle.get_velocity()
                speed_ms = math.sqrt(ego_vel.x**2 + ego_vel.y**2 + ego_vel.z**2)
                gps = {"latitude": 0.0, "longitude": 0.0, "altitude": 0.0}

                weather = world.get_weather()
                weather_dict = {
                    "cloudiness": weather.cloudiness,
                    "precipitation": weather.precipitation,
                    "precipitation_deposits": weather.precipitation_deposits,
                    "wind_intensity": weather.wind_intensity,
                    "sun_azimuth_angle": weather.sun_azimuth_angle,
                    "sun_altitude_angle": weather.sun_altitude_angle,
                    "fog_density": weather.fog_density,
                    "fog_distance": weather.fog_distance,
                    "wetness": weather.wetness,
                }

                snapshot_world = world.get_snapshot()
                sim_elapsed_seconds = snapshot_world.timestamp.elapsed_seconds
                tick_number = snapshot_world.frame

                write_frame_metadata(
                    frame_id,
                    tick_number,
                    self.output_dir,
                    weather=weather_dict,
                    speed_ms=speed_ms,
                    gps=gps,
                    town=world.get_map().name,
                    sensors_present=list(self.sensors.keys()),
                    sim_elapsed_seconds=sim_elapsed_seconds,
                )

                if self.progress_callback:
                    self.progress_callback(frame_id + 1, self.frames)
                
                # Release references to raw CARLA images immediately to prevent VRAM leak
                del snapshot
                import gc
                gc.collect()

            # ── 5. Calibration (once per dataset) ────────────────────────────
            extrinsics = compute_extrinsics()
            write_calibration(self.output_dir, self.camera_params, extrinsics)
            if "radar" in self.sensors:
                radar_csv_path = os.path.join(self.output_dir, "radar.csv")
                print(f"[CARLA Radar] Export complete -> {radar_csv_path}")
            self.sync_engine.export_report(self.output_dir)
            print(f"[CARLA Capture] Multi-sensor capture complete: {self.frames} frames.")

        finally:
            # Stop listening on all sensors
            for sensor in self.sensors.values():
                try:
                    sensor.stop()
                except Exception as e:
                    print(f"[CARLA Capture] Warning: could not stop sensor: {e}")

            # Always restore original settings
            try:
                world.apply_settings(original_settings)
                print("[CARLA Capture] Synchronous mode disabled.")
            except Exception as e:
                print(f"[CARLA Capture] Warning: could not restore settings: {e}")



