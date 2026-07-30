# Synthetic Driving Video Dataset Generator

A CARLA-based pipeline that generates labeled synthetic driving video datasets —
built to explore whether simulation-generated data can supplement real-world
datasets (like Waymo Open Dataset, nuScenes, KITTI) for training autonomous
driving perception models, with a focus on edge cases and regions that are
underrepresented in existing public datasets.

This is 100% software — there is no physical hardware, camera, or LiDAR unit
involved anywhere. "Camera" and "LiDAR" refer to simulated sensor models inside
the CARLA simulator, which render synthetic images and point clouds from a
virtual 3D world.

---

## What this project does

1. Spawns a virtual city scene in CARLA (open-source driving simulator)
2. Places an "ego" vehicle with a virtual camera (and optionally LiDAR) attached
3. Fills the scene with AI-driven traffic and pedestrians
4. Drives the ego vehicle around on autopilot while continuously recording video
5. Automatically computes ground-truth bounding box labels for every frame
   (since the simulator knows the exact 3D position of every object — no manual
   annotation needed)
6. Exports each driving sequence as an `.mp4` video clip with synced labels,
   in three standard formats (KITTI, YOLO, COCO) simultaneously
7. Cycles through named "scenario presets" — edge cases like heavy rain,
   dense fog, jaywalking pedestrians, sudden braking — so the dataset covers
   conditions that are rare and expensive to capture in real-world driving

---

## Project files

| File | Purpose |
|---|---|
| `generate_synthetic_data.py` | v1 — generates standalone labeled images (kept for reference; superseded by the video version) |
| `generate_synthetic_video_dataset.py` | v2 — generates video clips (.mp4) instead of loose images, with basic weather cycling |
| `generate_synthetic_video_dataset_v2.py` | **current version** — adds named edge-case scenario presets and multi-format label export (KITTI + YOLO + COCO) |

Use `generate_synthetic_video_dataset_v2.py` going forward — it's the most complete version.

---

## Setup instructions

### 1. Install CARLA
- Download a pre-built release from [carla.org](https://carla.org) (do not build from source unless you specifically need to)
- Unzip it anywhere on your machine
- This requires a decent GPU (a gaming GPU is sufficient for development-scale generation)

### 2. Launch the simulator
- Windows: run `CarlaUE4.exe` inside the unzipped folder
- Linux: run `./CarlaUE4.sh`
- Leave this window open and running — it's the simulation engine the script connects to

### 3. Install Python dependencies
```bash
pip install carla opencv-python numpy
```
Important: the `carla` pip package version must match your downloaded CARLA
release version exactly (e.g. if you downloaded CARLA 0.9.15, run
`pip install carla==0.9.15`). If the plain pip install doesn't work, look for
a `.whl` file inside `PythonAPI/carla/dist/` in your CARLA folder and install
that instead — it will match your Python version.

### 4. Run the generator
With CARLA still running in the background:
```bash
python generate_synthetic_video_dataset_v2.py
```

---

## Output structure

```
synthetic_video_dataset/
    clip_000_clear_normal_traffic/
        video.mp4                 <- the driving video clip
        labels_kitti/              <- one .txt file per frame, KITTI format
            frame_00000.txt
            frame_00001.txt
            ...
        labels_yolo/                <- one .txt file per frame, YOLO format (normalized coords)
            frame_00000.txt
            ...
        labels_coco.json            <- single COCO-format JSON covering the whole clip
    clip_001_heavy_rain_night/
        ...
    clip_002_dense_fog_low_visibility/
        ...
```

Each run generates one clip per scenario preset (8 clips by default). Running
the script again continues clip numbering and generates another full round.

---

## Scenario presets (edge cases)

Defined in `SCENARIO_PRESETS` at the top of the script. Each preset controls
weather, traffic/pedestrian density, and a triggered "event":

| Preset name | Weather | Event |
|---|---|---|
| `clear_normal_traffic` | Clear, daytime | none — baseline |
| `heavy_rain_night` | Hard rain, night | none |
| `dense_fog_low_visibility` | Cloudy + manually injected fog | `fog` |
| `clear_traffic_jam` | Clear | high traffic density (45 vehicles) |
| `empty_highway_night` | Sunset/low light | very low traffic (3 vehicles) |
| `pedestrian_jaywalking_daytime` | Clear | `jaywalker` — force-spawns a pedestrian crossing the ego vehicle's path |
| `sudden_braking_wet_road` | Wet road | `sudden_brake` — ego vehicle hard-brakes mid-clip, then resumes |
| `sun_glare_sunset` | Sunset | none |

Adding a new edge case is just adding a new dictionary entry to this list —
no other code changes needed unless the scenario requires a new type of
triggered event (like `jaywalker` or `sudden_brake`), in which case add a new
branch in `apply_event_effects()` or the per-frame loop in `record_one_clip()`.

---

## Output label formats

| Format | Structure | Typically used for |
|---|---|---|
| KITTI | `class truncated occluded alpha xmin ymin xmax ymax ...` (3D fields currently placeholder `-1`) | Classic AV benchmarks |
| YOLO | `class_id x_center y_center width height` (all normalized 0-1) | YOLO-family object detectors |
| COCO | Single JSON per clip with `images`, `annotations`, `categories` sections | General object detection frameworks (Detectron2, mmdetection, etc.) |

---

## Known limitations (be upfront about these)

- **2D boxes only.** KITTI's full format includes 3D position, dimensions,
  and rotation — CARLA provides all of this via the actor's transform and
  bounding box extent, but the current script only computes and exports 2D
  boxes. Extending to 3D is a moderate addition, not a redesign.
- **No LiDAR in the v2 video script yet.** The original `generate_synthetic_data.py`
  had LiDAR capture; it hasn't been ported into the video + multi-format
  version yet.
- **No region-specific road/vehicle modeling.** CARLA's built-in towns are
  generic/fictional, not modeled on any real country's roads. Supporting
  underrepresented regions (India, Southeast Asia, Africa, etc.) would require
  building custom maps (via OpenDRIVE) and adding region-appropriate vehicle
  assets (e.g. auto-rickshaws, two-wheelers) and traffic behavior rules —
  this is a separate, larger effort, not a config change.
- **Fixed camera position.** Only one forward-facing camera is simulated;
  real AV datasets typically use multi-camera rigs (front, side, rear) —
  extending to multiple cameras just means attaching additional
  `sensor.camera.rgb` actors at different transforms.
- **No downstream validation yet.** The dataset's actual usefulness (does it
  improve a real detector's accuracy) hasn't been measured yet — this is the
  single most important next step before treating this as a sellable product,
  not just a generation pipeline.

---

## Recommended next steps

1. **Validate usefulness, not just generate data.** Train a small detector
   (e.g. YOLOv8) on a real dataset (KITTI or nuScenes-mini), then again with
   this synthetic data mixed in, and compare accuracy on a real held-out test
   set — especially on rare classes like pedestrians in fog or night scenes.
2. **Add multi-camera and LiDAR support** to match real AV sensor rigs more closely.
3. **Add 3D bounding boxes** to make the KITTI export fully spec-compliant.
4. **Scale up scenario diversity** — more presets, randomized parameter
   ranges within each preset (e.g. randomize fog density instead of one fixed value).
5. **Only after the above:** explore region-specific map/vehicle modeling if
   there's a clear buyer or use case for it — it's the most expensive item on
   this list, so it should be justified by demand first.

---

## Requirements summary

- CARLA (pre-built release, matching version for the `carla` pip package)
- Python 3.8+ (match whatever your CARLA release supports)
- `pip install carla opencv-python numpy`
- A GPU capable of running CARLA (most modern gaming GPUs are sufficient for
  development-scale generation; large-scale generation will eventually need
  cloud GPU resources)
