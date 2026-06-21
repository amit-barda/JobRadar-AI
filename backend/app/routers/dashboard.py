from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.job import Job, JobStatus
from ..models.cv import CV, JobCVMatch
from ..models.user import User
from ..utils.auth import get_current_active_user

router = APIRouter()


@router.get("")
def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id

    total_jobs = db.query(func.count(Job.id)).filter(Job.user_id == uid).scalar() or 0
    status_counts = (
        db.query(Job.status, func.count(Job.id))
        .filter(Job.user_id == uid)
        .group_by(Job.status)
        .all()
    )
    status_breakdown = {str(s): c for s, c in status_counts}

    active_cv = db.query(CV).filter(CV.user_id == uid, CV.is_active == True).first()
    total_cvs = db.query(func.count(CV.id)).filter(CV.user_id == uid).scalar() or 0

    top_matches = (
        db.query(JobCVMatch)
        .filter(JobCVMatch.user_id == uid)
        .order_by(JobCVMatch.final_score.desc())
        .limit(5)
        .all()
    )

    recent_jobs = (
        db.query(Job)
        .filter(Job.user_id == uid)
        .order_by(Job.date_added.desc())
        .limit(5)
        .all()
    )

    return {
        "total_jobs": total_jobs,
        "status_breakdown": status_breakdown,
        "total_cvs": total_cvs,
        "active_cv_id": str(active_cv.id) if active_cv else None,
        "top_matches": [
            {
                "match_id": str(m.id),
                "job_id": str(m.job_id),
                "cv_id": str(m.cv_id),
                "final_score": m.final_score,
                "recommendation": m.recommendation,
            }
            for m in top_matches
        ],
        "recent_jobs": [
            {
                "job_id": str(j.id),
                "title": j.title,
                "company": j.company,
                "status": j.status,
                "date_added": j.date_added.isoformat() if j.date_added else None,
            }
            for j in recent_jobs
        ],
    }
