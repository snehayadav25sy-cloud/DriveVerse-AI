import urllib.request, json, sys, os, time

# 1. Login
req = urllib.request.Request('http://localhost:8000/auth/login', data=json.dumps({'email':'test@driveverse.ai','password':'test1234'}).encode(), headers={'Content-Type':'application/json'}, method='POST')
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']

# 2. Get project
req = urllib.request.Request('http://localhost:8000/projects', headers={'Authorization': f'Bearer {token}'})
projs = json.loads(urllib.request.urlopen(req).read().decode())
pid = projs[0]['id']

# 3. Submit Phase 5 Test A job: rgb, optical_flow
job_payload = {'project_id': pid, 'map': 'Town01', 'sensors': ['rgb', 'optical_flow'], 'frames': 15, 'export_format': 'kitti'}
req = urllib.request.Request('http://localhost:8000/jobs', data=json.dumps(job_payload).encode(), headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, method='POST')
job_resp = json.loads(urllib.request.urlopen(req).read().decode())
job_id = job_resp['id']
print(f"Submitted Phase 5 Test A job: {job_id}")

# 4. Run worker logic directly
backend_path = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\backend")
sys.path.insert(0, backend_path)
worker_path = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\worker")
sys.path.insert(0, worker_path)
engine_path = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\dataset-engine")
sys.path.insert(0, engine_path)

from app.database.database import SessionLocal
from app.models import User, Project, Job, Dataset
from main import generate_dataset_job, _sensor_metadata
import uuid

db = SessionLocal()
job = db.query(Job).filter(Job.id == job_id).first()
print(f"Worker picked up job {job.id}...")
job.status = 'running'
db.commit()

sensors = job.sensors if isinstance(job.sensors, list) else [job.sensors or 'rgb']
export_format = job.export_format if job.export_format else 'kitti'

try:
    output_path, rgb_cnt, lid_cnt, ann_cnt = generate_dataset_job(db, job)
    
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
    print(f"SUCCESS: Job {job.id} completed successfully!")

except Exception as e:
    import traceback
    print("!!! JOB FAILED WITH EXCEPTION !!!")
    traceback.print_exc()
    db.rollback()
    job.status = 'failed'
    db.commit()

db.close()
