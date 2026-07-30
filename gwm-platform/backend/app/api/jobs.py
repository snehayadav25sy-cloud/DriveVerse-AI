import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.project import Project
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate, JobResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
def create_job(
    job_req: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """POST /jobs — creates a job with status=queued."""
    proj = db.query(Project).filter(
        Project.id == job_req.project_id,
        Project.user_id == current_user.id,
    ).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    new_job = Job(
        project_id=job_req.project_id,
        map=job_req.map,
        sensors=job_req.sensors,
        frames=job_req.frames,
        export_format=job_req.export_format,
        status="queued",
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@router.get("", response_model=List[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = (
        db.query(Job)
        .join(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /jobs/{id} — returns status + progress."""
    job = (
        db.query(Job)
        .join(Project)
        .filter(Job.id == job_id, Project.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/download")
def download_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /jobs/{id}/download — streams the dataset ZIP once status=completed."""
    job = (
        db.query(Job)
        .join(Project)
        .filter(Job.id == job_id, Project.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed (status={job.status})")
    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Dataset file not found on server")
    return FileResponse(
        path=job.output_path,
        filename=f"dataset_{job.id}.zip",
        media_type="application/zip",
    )
