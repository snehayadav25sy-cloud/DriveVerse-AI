"""
exporters/nuscenes/export.py — converts internal format to nuScenes dataset schema.
"""

import os
import json
import uuid
import time
from datetime import datetime

def export_nuscenes(output_dir: str, frame_count: int, sensors: list) -> str:
    """
    Exports dataset in nuScenes schema metadata format.
    """
    nusc_dir = os.path.join(output_dir, "nuscenes")
    v1_0_mini = os.path.join(nusc_dir, "v1.0-mini")
    os.makedirs(v1_0_mini, exist_ok=True)

    # 1. sensor.json
    sensor_list = []
    sensor_map = {}
    for s_name in sensors:
        s_token = str(uuid.uuid4())
        modality = "camera" if "rgb" in s_name or "camera" in s_name or s_name in ["depth", "semantic", "instance", "optical_flow"] else ("lidar" if s_name == "lidar" else "radar")
        sensor_entry = {
            "token": s_token,
            "channel": s_name.upper(),
            "modality": modality
        }
        sensor_list.append(sensor_entry)
        sensor_map[s_name] = s_token

    with open(os.path.join(v1_0_mini, "sensor.json"), "w") as f:
        json.dump(sensor_list, f, indent=2)

    # 2. calibrated_sensor.json
    calibrated_sensors = []
    calib_map = {}
    for s_name in sensors:
        c_token = str(uuid.uuid4())
        calib_entry = {
            "token": c_token,
            "sensor_token": sensor_map[s_name],
            "translation": [1.5 if s_name == "rgb" else 0.0, 0.0, 1.4 if s_name == "rgb" else 2.5],
            "rotation": [1.0, 0.0, 0.0, 0.0],
            "camera_intrinsic": [[800.0, 0.0, 400.0], [0.0, 800.0, 300.0], [0.0, 0.0, 1.0]] if "rgb" in s_name or "camera" in s_name else []
        }
        calibrated_sensors.append(calib_entry)
        calib_map[s_name] = c_token

    with open(os.path.join(v1_0_mini, "calibrated_sensor.json"), "w") as f:
        json.dump(calibrated_sensors, f, indent=2)

    # 3. scene.json
    scene_token = str(uuid.uuid4())
    log_token = str(uuid.uuid4())
    scene_entry = {
        "token": scene_token,
        "name": "scene-0001",
        "description": "CARLA Autonomous Drive Multi-Sensor Capture",
        "log_token": log_token,
        "nbr_samples": frame_count,
        "first_sample_token": "",
        "last_sample_token": ""
    }

    samples = []
    sample_datas = []
    ego_poses = []
    
    prev_sample_token = ""
    first_sample_token = ""
    last_sample_token = ""

    for frame_id in range(frame_count):
        s_token = str(uuid.uuid4())
        if frame_id == 0:
            first_sample_token = s_token
        if frame_id == frame_count - 1:
            last_sample_token = s_token

        ego_token = str(uuid.uuid4())
        ts = int(time.time() * 1000000) + frame_id * 100000

        ego_pose = {
            "token": ego_token,
            "translation": [0.0, 0.0, 0.0],
            "rotation": [1.0, 0.0, 0.0, 0.0],
            "timestamp": ts
        }
        ego_poses.append(ego_pose)

        sample = {
            "token": s_token,
            "timestamp": ts,
            "scene_token": scene_token,
            "next": "",
            "prev": prev_sample_token
        }
        if prev_sample_token and len(samples) > 0:
            samples[-1]["next"] = s_token

        samples.append(sample)
        prev_sample_token = s_token

        # sample_data for each sensor
        for s_name in sensors:
            sd_token = str(uuid.uuid4())
            ext = "png" if "rgb" in s_name or s_name in ["depth", "semantic", "instance"] else ("pcd" if s_name == "lidar" else "csv")
            sd_entry = {
                "token": sd_token,
                "sample_token": s_token,
                "calibrated_sensor_token": calib_map[s_name],
                "filename": f"samples/{s_name.upper()}/{frame_id:06d}.{ext}",
                "fileformat": ext,
                "width": 1280 if s_name == "rgb" else 800,
                "height": 720 if s_name == "rgb" else 600,
                "timestamp": ts,
                "is_key_frame": True,
                "next": "",
                "prev": ""
            }
            sample_datas.append(sd_entry)

    scene_entry["first_sample_token"] = first_sample_token
    scene_entry["last_sample_token"] = last_sample_token

    with open(os.path.join(v1_0_mini, "scene.json"), "w") as f:
        json.dump([scene_entry], f, indent=2)
    with open(os.path.join(v1_0_mini, "sample.json"), "w") as f:
        json.dump(samples, f, indent=2)
    with open(os.path.join(v1_0_mini, "sample_data.json"), "w") as f:
        json.dump(sample_datas, f, indent=2)
    with open(os.path.join(v1_0_mini, "ego_pose.json"), "w") as f:
        json.dump(ego_poses, f, indent=2)

    print(f"[nuScenes Exporter] Export complete -> {nusc_dir} ({frame_count} frames)")
    return nusc_dir
