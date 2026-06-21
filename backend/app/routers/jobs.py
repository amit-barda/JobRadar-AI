from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from ..database import get_db
from ..models.job import Job, JobStatus, WorkType
from ..models.user import User
from ..schemas.job import (
    JobResponse, JobListResponse, JobStatusUpdate,
    AddJobUrlRequest, AddJobEmailRequest
)
from ..utils.auth import get_current_active_user
from ..services import job_service

router = APIRouter()


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    work_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(Job).options(joinedload(Job.analysis)).filter(Job.user_id == current_user.id)
    if status:
        query = query.filter(Job.status == status)
    if work_type:
        query = query.filter(Job.work_type == work_type)
    if search:
        term = f"%{search}%"
        query = query.filter(
            Job.title.ilike(term) | Job.company.ilike(term) | Job.description.ilike(term)
        )
    total = query.count()
    items = query.order_by(Job.date_added.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return JobListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .options(joinedload(Job.analysis))
        .filter(Job.id == job_id, Job.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/from-url", response_model=JobResponse, status_code=201)
def add_job_from_url(
    data: AddJobUrlRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = job_service.create_job_from_url(db, str(current_user.id), data.url)
    background_tasks.add_task(job_service.analyze_job_background, str(job.id))
    return job


@router.post("/from-email", response_model=JobResponse, status_code=201)
def add_job_from_email(
    data: AddJobEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = job_service.create_job_from_email(db, str(current_user.id), data.content, data.source_name)
    background_tasks.add_task(job_service.analyze_job_background, str(job.id))
    return job


@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: str,
    data: JobStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        job.status = JobStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {data.status}")
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/analyze", response_model=JobResponse)
def analyze_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    background_tasks.add_task(job_service.analyze_job_background, job_id)
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
