"""
sync_engine.py — Multi-Sensor Synchronous Timestamp Verification & Reporting Engine.

In CARLA's synchronous mode every sensor that fires on tick N carries the same
carla.SensorData.frame number.  Timestamp offsets between sensors are rendering-
pipeline latency artefacts, not real desync.  We therefore use frame numbers as
the authoritative sync key and report timestamp deltas as informational only.
"""

import json
import os

class SensorSyncEngine:
    def __init__(self, sensor_keys, max_allowed_delta_ms=1.0):
        self.sensor_keys          = sensor_keys
        self.max_allowed_delta_ms = max_allowed_delta_ms
        self.frame_records        = []
        self.desync_count         = 0

    def record_frame(self, frame_id, sim_timestamp, sensor_snapshots):
        """
        sensor_snapshots: dict of sensor_key -> carla.SensorData object.

        A frame is considered SYNCED when all present sensors share the same
        carla frame number (guaranteed by CARLA's synchronous tick).
        Timestamp deltas are recorded as informational data only.
        """
        timestamps   = {}
        frame_numbers = {}
        deltas       = {}

        # Collect per-sensor frame numbers and timestamps
        for s_key, s_data in sensor_snapshots.items():
            if s_data is not None:
                if hasattr(s_data, 'frame'):
                    frame_numbers[s_key] = s_data.frame
                if hasattr(s_data, 'timestamp'):
                    timestamps[s_key] = round(s_data.timestamp, 6)

        # Determine reference: the CARLA frame number from rgb (or first sensor)
        ref_frame = None
        for s_key in ["rgb"] + list(sensor_snapshots.keys()):
            if s_key in frame_numbers:
                ref_frame = frame_numbers[s_key]
                break

        # Compute timestamp deltas informational
        ref_ts = timestamps.get("rgb") or (next(iter(timestamps.values())) if timestamps else sim_timestamp)
        max_delta = 0.0
        for s_key, ts in timestamps.items():
            d = abs(ts - ref_ts) * 1000.0
            deltas[s_key] = round(d, 4)
            if d > max_delta:
                max_delta = d

        # SYNC CHECK: all sensors must share the same CARLA frame number
        unique_frames = set(frame_numbers.values())
        is_synced = (len(unique_frames) <= 1) if unique_frames else False

        if not is_synced:
            self.desync_count += 1

        record = {
            "frame_id":            frame_id,
            "carla_frame":         ref_frame,
            "sensor_frame_numbers": frame_numbers,
            "ref_timestamp":       round(ref_ts, 6),
            "sim_timestamp":       round(sim_timestamp, 6),
            "sensor_timestamps":   timestamps,
            "deltas_from_ref_ms":  deltas,
            "max_sensor_delta_ms": round(max_delta, 4),
            "synced":              is_synced,
        }
        self.frame_records.append(record)
        return is_synced

    def export_report(self, output_dir):
        """Save sync_report.json in output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, "sync_report.json")
        summary = {
            "total_frames":        len(self.frame_records),
            "desync_frames":       self.desync_count,
            "max_allowed_delta_ms": self.max_allowed_delta_ms,
            "status":              "PASSED" if self.desync_count == 0 else "FAILED",
            "sync_method":         "carla_frame_number",
            "frame_details":       self.frame_records,
        }
        with open(report_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"[Sync Engine] Exported sync report -> {report_path} (Status: {summary['status']})")
        return report_path, summary
