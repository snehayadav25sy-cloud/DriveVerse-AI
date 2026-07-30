import sys, os, traceback
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
job = db.query(Job).filter(Job.status == 'queued').order_by(Job.created_at.desc()).first()
if not job:
    print("NO QUEUED JOBS FOUND")
    db.close()
    sys.exit(0)

print(f"Processing job {job.id}...")
job.status = 'running'
db.commit()

sensors = job.sensors if isinstance(job.sensors, list) else [job.sensors or 'rgb']
export_format = job.export_format if job.export_format else 'kitti'

try:
    output_path, rgb_cnt, lid_cnt, ann_cnt = generate_dataset_job(db, job)
    print(f"Output path: {output_path}, RGB: {rgb_cnt}, LiDAR: {lid_cnt}, Ann: {ann_cnt}")
    
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
    print("JOB COMPLETED SUCCESSFULLY!")

except Exception as e:
    print("!!! JOB FAILED WITH EXCEPTION !!!")
    traceback.print_exc()
    db.rollback()
    job.status = 'failed'
    db.commit()

db.close()
