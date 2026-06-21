from datetime import datetime
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.job import JobSource, Job, SyncStatus, SourceType, JobStatus
from . import scraper_service, openai_service, job_service


def sync_source(db: Session, source_id: str) -> int:
    """
    Sync a job source and return number of jobs imported.
    Supports: rss, manual_url, api (stub).
    """
    source = db.query(JobSource).filter(JobSource.id == source_id).first()
    if not source or not source.is_enabled:
        return 0

    try:
        if source.source_type == SourceType.rss:
            count = _sync_rss(db, source)
        elif source.source_type == SourceType.manual_url:
            count = _sync_manual_url(db, source)
        else:
            count = 0

        source.last_sync_at = datetime.utcnow()
        source.sync_status = SyncStatus.success
        db.commit()
        return count
    except Exception as e:
        source.sync_status = SyncStatus.error
        db.commit()
        print(f"[source_service] Sync error for source {source_id}: {e}")
        return 0


def _sync_rss(db: Session, source: JobSource) -> int:
    if not source.url:
        return 0
    try:
        import feedparser
        feed = feedparser.parse(source.url)
        count = 0
        for entry in feed.entries[:20]:
            url = entry.get("link", "")
            if not url:
                continue
            # Skip if already imported
            existing = db.query(Job).filter(
                Job.user_id == source.user_id, Job.url == url
            ).first()
            if existing:
                continue
            try:
                job = job_service.create_job_from_url(db, str(source.user_id), url)
                job.source_id = source.id
                job.source = source.name
                db.commit()
                count += 1
            except Exception:
                continue
        return count
    except ImportError:
        print("[source_service] feedparser not installed")
        return 0


def _sync_manual_url(db: Session, source: JobSource) -> int:
    if not source.url:
        return 0
    existing = db.query(Job).filter(
        Job.user_id == source.user_id, Job.url == source.url
    ).first()
    if existing:
        return 0
    job = job_service.create_job_from_url(db, str(source.user_id), source.url)
    job.source_id = source.id
    job.source = source.name
    db.commit()
    return 1


def sync_source_background(source_id: str):
    db = SessionLocal()
    try:
        sync_source(db, source_id)
    except Exception as e:
        print(f"[source_service] Background sync error for {source_id}: {e}")
    finally:
        db.close()
