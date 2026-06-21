from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.job import JobSource
from ..models.user import User
from ..schemas.job import JobSourceCreate, JobSourceUpdate, JobSourceResponse
from ..utils.auth import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[JobSourceResponse])
def list_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(JobSource).filter(JobSource.user_id == current_user.id).all()


@router.post("", response_model=JobSourceResponse, status_code=201)
def create_source(data: JobSourceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # #region agent log
    import json, time
    try:
        with open("/app/debug-1d3f66.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"1d3f66","runId":"post-fix","hypothesisId":"H1","location":"sources.py:create_source","message":"backend create reached","data":{"source_type":data.source_type.value if hasattr(data.source_type,'value') else str(data.source_type),"name":data.name},"timestamp":int(time.time()*1000)}) + "\n")
    except Exception:
        pass
    # #endregion
    source = JobSource(user_id=current_user.id, **data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/{source_id}", response_model=JobSourceResponse)
def get_source(source_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    source = db.query(JobSource).filter(JobSource.id == source_id, JobSource.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.put("/{source_id}", response_model=JobSourceResponse)
def update_source(source_id: str, data: JobSourceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    source = db.query(JobSource).filter(JobSource.id == source_id, JobSource.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(source, k, v)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    source = db.query(JobSource).filter(JobSource.id == source_id, JobSource.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()


@router.post("/{source_id}/sync")
def sync_source(source_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    source = db.query(JobSource).filter(JobSource.id == source_id, JobSource.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    from ..tasks.job_tasks import sync_source_task
    sync_source_task.delay(str(source.id), str(current_user.id))
    return {"message": "Sync started", "source_id": source_id}
