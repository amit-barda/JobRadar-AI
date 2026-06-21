from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.cv import JobCVMatch, CV
from ..models.job import Job
from ..models.user import User
from ..schemas.cv import JobCVMatchResponse
from ..utils.auth import get_current_active_user
from ..services import match_service

router = APIRouter()


def _get_or_create_match(db: Session, job_id: str, cv_id: str, user_id: str, background_tasks: BackgroundTasks) -> JobCVMatch:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == user_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    existing = db.query(JobCVMatch).filter(
        JobCVMatch.job_id == job_id, JobCVMatch.cv_id == cv_id, JobCVMatch.user_id == user_id
    ).first()
    if existing:
        background_tasks.add_task(match_service.run_match_background, str(existing.id))
        return existing

    match = JobCVMatch(job_id=job_id, cv_id=cv_id, user_id=user_id)
    db.add(match)
    db.commit()
    db.refresh(match)
    background_tasks.add_task(match_service.run_match_background, str(match.id))
    return match


# --- Spec routes ---

@router.post("/job/{job_id}/cv/{cv_id}", response_model=JobCVMatchResponse, status_code=201)
def match_job_cv(
    job_id: str,
    cv_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _get_or_create_match(db, job_id, cv_id, str(current_user.id), background_tasks)


@router.get("/job/{job_id}/cv/{cv_id}", response_model=JobCVMatchResponse)
def get_job_cv_match(
    job_id: str,
    cv_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    match = db.query(JobCVMatch).filter(
        JobCVMatch.job_id == job_id, JobCVMatch.cv_id == cv_id, JobCVMatch.user_id == current_user.id
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.get("/job/{job_id}", response_model=List[JobCVMatchResponse])
def get_job_matches(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return db.query(JobCVMatch).filter(
        JobCVMatch.job_id == job_id, JobCVMatch.user_id == current_user.id
    ).order_by(JobCVMatch.final_score.desc()).all()


@router.get("/cv/{cv_id}", response_model=List[JobCVMatchResponse])
def get_cv_matches(
    cv_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return db.query(JobCVMatch).filter(
        JobCVMatch.cv_id == cv_id, JobCVMatch.user_id == current_user.id
    ).order_by(JobCVMatch.final_score.desc()).all()


@router.post("/cv/{cv_id}/all-jobs")
def match_cv_all_jobs(
    cv_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    jobs = db.query(Job).filter(Job.user_id == current_user.id, Job.is_analyzed == True).all()
    count = 0
    for job in jobs:
        existing = db.query(JobCVMatch).filter(
            JobCVMatch.job_id == str(job.id), JobCVMatch.cv_id == cv_id, JobCVMatch.user_id == current_user.id
        ).first()
        if not existing:
            match = JobCVMatch(job_id=str(job.id), cv_id=cv_id, user_id=current_user.id)
            db.add(match)
            db.flush()
            background_tasks.add_task(match_service.run_match_background, str(match.id))
            count += 1
    db.commit()
    return {"count": count, "message": f"Matching against {count} jobs"}


# --- Legacy / generic routes ---

@router.get("", response_model=List[JobCVMatchResponse])
def list_matches(
    job_id: Optional[str] = None,
    cv_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(JobCVMatch).filter(JobCVMatch.user_id == current_user.id)
    if job_id:
        query = query.filter(JobCVMatch.job_id == job_id)
    if cv_id:
        query = query.filter(JobCVMatch.cv_id == cv_id)
    return query.order_by(JobCVMatch.final_score.desc()).all()


@router.delete("/{match_id}", status_code=204)
def delete_match(
    match_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    match = db.query(JobCVMatch).filter(
        JobCVMatch.id == match_id, JobCVMatch.user_id == current_user.id
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    db.delete(match)
    db.commit()
