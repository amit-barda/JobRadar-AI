from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.cv import CV, JobCVMatch
from ..models.job import Job
from ..models.user import User
from ..schemas.interview import CoverLetterRequest
from ..utils.auth import get_current_active_user
from ..services import cover_letter_service

router = APIRouter()


@router.post("/generate")
def generate_cover_letter(
    data: CoverLetterRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == data.job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv = db.query(CV).filter(CV.id == data.cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    text = cover_letter_service.generate_cover_letter(db, job, cv)

    # Persist to existing match if available
    match = db.query(JobCVMatch).filter(
        JobCVMatch.job_id == data.job_id,
        JobCVMatch.cv_id == data.cv_id,
        JobCVMatch.user_id == current_user.id,
    ).first()
    if match:
        match.cover_letter_text = text
        db.commit()

    return {"cover_letter": text, "job_id": data.job_id, "cv_id": data.cv_id}


@router.get("/job/{job_id}")
def get_cover_letter_for_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    match = db.query(JobCVMatch).filter(
        JobCVMatch.job_id == job_id,
        JobCVMatch.user_id == current_user.id,
        JobCVMatch.cover_letter_text.isnot(None),
    ).order_by(JobCVMatch.created_at.desc()).first()

    if not match or not match.cover_letter_text:
        raise HTTPException(status_code=404, detail="No cover letter found for this job")

    return {"cover_letter": match.cover_letter_text, "job_id": job_id}
