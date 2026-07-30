import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.dataset import Dataset
from app.models.job import Job
from app.models.project import Project
from app.models.user import User
from app.schemas.dataset import DatasetResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    datasets = (
        db.query(Dataset)
        .join(Job)
        .join(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .all()
    )
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = (
        db.query(Dataset)
        .join(Job)
        .join(Project)
        .filter(Dataset.id == dataset_id, Project.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/download")
def download_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = (
        db.query(Dataset)
        .join(Job)
        .join(Project)
        .filter(Dataset.id == dataset_id, Project.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.path or not os.path.exists(dataset.path):
        raise HTTPException(status_code=404, detail="Dataset file not found on server")
    return FileResponse(
        path=dataset.path,
        filename=f"dataset_{dataset.id}.zip",
        media_type="application/zip",
    )
