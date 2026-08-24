# DriveVerse AI — Autonomous Vehicle Dataset Engine & Dashboard

DriveVerse AI is a production-grade synthetic dataset engine and dashboard platform built around CARLA 0.9.16. It generates high-fidelity sensor datasets (RGB, LiDAR, and bounding box annotations) with deterministic scenario replay capabilities, parameterized geographic context profiles, and a web-based regulator monitoring dashboard.

---

## Key Features

1. **Deterministic Scenario Replay Engine:** Generate reproducible, byte-for-byte identical traffic simulations with precise event scheduling (e.g., lane closures, jaywalking, sudden braking, safety operator manual takeovers).
2. **Multi-Country Parameterization Profiles:** Define country-specific weather patterns, speed limits, vehicle mix rules (NLTA 2025 mix, India mix), and traffic behaviors (yielding parameters, speed modifiers).
3. **Geo-Spatial OpenDRIVE Generation:** Compiles raw OpenStreetMap (OSM) nodes and edges into valid, validated OpenDRIVE (`.xodr`) road maps.
4. **Web-Based Dashboard:** Modern React frontend featuring interactive deck.gl corridor maps, Recharts vehicle mix distribution, OpenDRIVE validator status, and scenario execution tracking.

---

## Environment & Dependency Requirements

Strict environment alignment is required. Any mismatch will cause execution to halt.

### CARLA Simulator Server
* **Version:** CARLA 0.9.16
* **Server Install Path:** `C:\carla\WindowsNoEditor\CarlaUE4.exe`
* **Execution Script:** `C:\carla\start_carla.bat` (Must always launch via this script)

### Python Client Environment
* **Python version:** `3.10.11` (conda env `carla16_env`)
* **CARLA pip package:** `carla==0.9.16`
* Pinned package list is in `requirements-carla.txt`

---

## Installation & Setup

### 1. Launching CARLA Server
Start the CARLA simulator server using the approved batch script:
```powershell
C:\carla\start_carla.bat
```

### 2. Backend API Setup
Activate the conda environment and start the FastAPI server:
```powershell
conda activate carla16_env
cd gwm-platform/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Web Dashboard Setup
Navigate to the frontend directory, install dependencies, and run the Vite dev server:
```bash
cd gwm-platform/frontend
npm install
npm run dev
```

### 4. Running a Dataset Generation Job
Use the dataset worker to execute a deterministic dataset generation run:
```powershell
conda activate carla16_env
cd gwm-platform/worker
python main.py --job-id <uuid>
```

---

## Known System Limitations

* **4GB Local VRAM Constraint:** Local development using the RTX 3050 Laptop GPU (4GB VRAM) is strictly limited to default maps (e.g. `Town01`). Loading custom OpenDRIVE maps (Ebene Cybercity or Pont-Fer Roundabout) or larger worlds requires a cloud GPU instance with >=12GB VRAM.
* **CARLA Fixed Vehicle Assets:** Simulation vehicle configurations are constrained by the hardcoded 3D model asset library of CARLA 0.9.16. Region-specific vehicles (e.g., auto-rickshaws, dual-purpose pickups) are simulated using traffic-property behavior modifiers rather than custom 3D models.
* **Distance/FOV-Only Bounding Box Filtering:** Annotations are computed using distance and Field-Of-View (FOV) math. Raycasting-based occlusion detection is not fully implemented; fully occluded vehicles behind walls may still generate bounding boxes.
* **Estimated Country Profiles:** Due to the lack of public GTFS schedules for Ebene/Mauritius, vehicle mix statistics are configured as `# ESTIMATED` using regional transit data sources.
* **City2Graph Package Conflict:** The `city2graph` Python package strictly requires Python >=3.11/3.12, conflicting with `carla16_env` which is strictly pinned to Python 3.10.11 for CARLA client compatibility. The City2Graph visualizer layer is disabled in the frontend with a descriptive tooltip.
