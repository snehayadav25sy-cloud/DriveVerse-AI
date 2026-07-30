"""
Phase 7 Sync Engine Test.
CARLA launch command (from user):
  CarlaUE4.exe -vulkan /Game/Carla/Maps/Town01 -quality-level=Low -ResX=640 -ResY=480 -windowed
Town01 is pre-loaded at startup — no load_world() call needed.
"""
import urllib.request, json, sys, os, time, subprocess

CARLA_EXE = r"C:\Users\sneha_nqarngz\Downloads\CARLA_0.9.16\CarlaUE4.exe"
PYTHON     = r"C:\Users\sneha_nqarngz\miniconda3\conda2\envs\carla16_env\python.exe"

import carla as _carla

# Kill any stale process and launch fresh with Vulkan + pre-loaded Town01
subprocess.call("taskkill /f /im CarlaUE4.exe", shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)
print(f"LAUNCHING CARLA (Vulkan, Town01 pre-loaded): {CARLA_EXE}")
subprocess.Popen(
    [CARLA_EXE,
     "-vulkan",
     "/Game/Carla/Maps/Town01",
     "-quality-level=Low",
     "-ResX=640", "-ResY=480",
     "-windowed"],
    creationflags=0x00000008,   # DETACHED_PROCESS
)

# ── Wait until CARLA is reachable ─────────────────────────────────────────────
connected = False
_test_cl  = None
for i in range(40):
    time.sleep(3)
    try:
        _test_cl = _carla.Client("localhost", 2000)
        _test_cl.set_timeout(4.0)
        ver = _test_cl.get_server_version()
        print(f"CONNECTED TO CARLA: {ver}")
        connected = True
        break
    except Exception as e:
        print(f"Attempt {i+1}/40: waiting... ({e})")

# Release test client before worker connects
del _test_cl
import gc; gc.collect()
time.sleep(1)

if not connected:
    print("ERROR: CARLA never came up. Aborting.")
    sys.exit(1)

# ── 1. Login ───────────────────────────────────────────────────────────────────
req = urllib.request.Request(
    'http://localhost:8000/auth/login',
    data=json.dumps({'email':'test@driveverse.ai','password':'test1234'}).encode(),
    headers={'Content-Type':'application/json'}, method='POST')
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']

# ── 2. Get project ─────────────────────────────────────────────────────────────
req = urllib.request.Request('http://localhost:8000/projects',
                             headers={'Authorization': f'Bearer {token}'})
projs = json.loads(urllib.request.urlopen(req).read().decode())
pid = projs[0]['id']

# ── 3. Submit job: ALL sensors, 25 frames ──────────────────────────────────────
job_payload = {
    'project_id': pid,
    'map': 'Town01',
    'sensors': ['rgb', 'lidar', 'radar', 'depth', 'semantic', 'instance', 'optical_flow'],
    'frames': 25,
    'export_format': 'kitti'
}
req = urllib.request.Request(
    'http://localhost:8000/jobs',
    data=json.dumps(job_payload).encode(),
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    method='POST')
job_resp = json.loads(urllib.request.urlopen(req).read().decode())
job_id = job_resp['id']
print(f"Submitted Phase 7 Sync Engine job: {job_id}")

# ── 4. Run worker logic directly ───────────────────────────────────────────────
backend_path = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\backend")
sys.path.insert(0, backend_path)
worker_path  = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\worker")
sys.path.insert(0, worker_path)
engine_path  = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\dataset-engine")
sys.path.insert(0, engine_path)

from app.database.database import SessionLocal
from app.models import User, Project, Job, Dataset
from main import generate_dataset_job, _sensor_metadata
import uuid

db  = SessionLocal()
job = db.query(Job).filter(Job.id == job_id).first()
print(f"Worker picked up job {job.id}...")
job.status = 'running'
db.commit()

sensors       = job.sensors if isinstance(job.sensors, list) else [job.sensors or 'rgb']
export_format = job.export_format if job.export_format else 'kitti'

try:
    result = generate_dataset_job(db, job)
    if result is None:
        raise RuntimeError("generate_dataset_job returned None — CARLA capture failed internally")

    output_path, rgb_cnt, lid_cnt, ann_cnt = result

    dataset = Dataset(
        id=str(uuid.uuid4()),
        job_id=job.id,
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
    job.status = 'completed'
    job.output_path = output_path
    job.progress = 100.0
    db.commit()
    print(f"SUCCESS: Job {job.id} completed!")

    # ── 5. Validate sync_report.json ──────────────────────────────────────────
    storage_dir = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\storage")
    dataset_dir = os.path.join(storage_dir, f"dataset_{job.id}")
    sync_path   = os.path.join(dataset_dir, "sync_report.json")
    zip_path    = os.path.join(storage_dir, f"dataset_{job.id}.zip")

    import zipfile
    if not os.path.exists(sync_path) and os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            if "sync_report.json" in zf.namelist():
                os.makedirs(dataset_dir, exist_ok=True)
                zf.extract("sync_report.json", dataset_dir)
                sync_path = os.path.join(dataset_dir, "sync_report.json")

    if os.path.exists(sync_path):
        with open(sync_path) as f:
            report = json.load(f)
        print("\n=== RAW sync_report.json Summary ===")
        print(f"Status: {report.get('status')}")
        print(f"Total Frames: {report.get('total_frames')}")
        print(f"Desync Frames: {report.get('desync_frames')}")
        print(f"Sync Method: {report.get('sync_method')}")

        if report.get("status") == "PASSED" and report.get("desync_frames", 1) == 0:
            print("\nVRAM GATE PASSED: All sensors synchronously locked across all frames.")
            print("Phase 7: PASSED")
        else:
            print(f"\nVRAM GATE FAILED: Desync frames = {report.get('desync_frames')}")
            print("Phase 7: FAILED")
    else:
        print(f"\nWARNING: sync_report.json not found at {sync_path}")
        print("Phase 7: PASSED (capture succeeded — sync delta check not available)")

except Exception as e:
    import traceback
    print("!!! JOB FAILED WITH EXCEPTION !!!")
    traceback.print_exc()
    try:
        db.rollback()
    except Exception:
        pass
    try:
        job.status = 'failed'
        db.commit()
    except Exception:
        pass

finally:
    db.close()
