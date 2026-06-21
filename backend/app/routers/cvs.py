from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..database import get_db
from ..models.cv import CV
from ..models.user import User
from ..schemas.cv import CVResponse, CVDetailResponse
from ..utils.auth import get_current_active_user
from ..utils.file_utils import save_upload_file
from ..services import cv_service

router = APIRouter()


@router.get("", response_model=List[CVResponse])
def list_cvs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()


@router.post("", response_model=CVResponse, status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    safe_name, file_path, ext = await save_upload_file(file, str(current_user.id))
    cv = CV(
        user_id=current_user.id,
        filename=safe_name,
        original_filename=file.filename or safe_name,
        file_path=file_path,
        file_size=file.size or 0,
        file_type=ext,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    background_tasks.add_task(cv_service.analyze_cv_background, str(cv.id))
    return cv


@router.get("/{cv_id}", response_model=CVDetailResponse)
def get_cv(
    cv_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    cv = (
        db.query(CV)
        .options(joinedload(CV.analysis))
        .filter(CV.id == cv_id, CV.user_id == current_user.id)
        .first()
    )
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.post("/{cv_id}/activate", response_model=CVResponse)
def activate_cv(
    cv_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # deactivate all other CVs
    db.query(CV).filter(CV.user_id == current_user.id).update({"is_active": False})
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    cv.is_active = True
    db.commit()
    db.refresh(cv)
    return cv


@router.post("/{cv_id}/analyze", response_model=CVResponse)
def analyze_cv(
    cv_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    background_tasks.add_task(cv_service.analyze_cv_background, cv_id)
    return cv


@router.delete("/{cv_id}", status_code=204)
def delete_cv(
    cv_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    import os
    if os.path.exists(cv.file_path):
        os.remove(cv.file_path)
    db.delete(cv)
    db.commit()
