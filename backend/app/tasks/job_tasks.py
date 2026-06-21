import asyncio
import logging
from .celery_app import celery_app
from ..database import SessionLocal
from ..models.job import Job, JobAnalysis, JobStatus, SyncStatus
from ..services.ai_service import AIService

logger = logging.getLogger(__name__)


@celery_app.task(name="job_tasks.scrape_job", bind=True, max_retries=2)
def scrape_job_task(self, job_id: str, url: str, user_id: str):
    db = SessionLocal()
    try:
        ai = AIService()
        result = asyncio.run(ai.scrape_job_url(url))
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        job.title = result.get("title") or job.title
        job.company = result.get("company", "") or job.company
        job.location = result.get("location") or job.location
        job.description = result.get("description") or job.description
        job.requirements = result.get("requirements")
        job.responsibilities = result.get("responsibilities")
        wt = result.get("work_type", "unknown")
        job.work_type = wt if wt in ("remote", "hybrid", "onsite", "unknown") else "unknown"
        db.commit()
        analyze_job_task.delay(job_id)
    except Exception as exc:
        logger.error(f"Error scraping job {job_id}: {exc}")
        db.rollback()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job and job.title == "Fetching...":
            job.title = "Failed to fetch"
            db.commit()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(name="job_tasks.analyze_job", bind=True, max_retries=2)
def analyze_job_task(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        job_text = (
            f"Title: {job.title}\nCompany: {job.company}\n"
            f"Location: {job.location or ''}\n\n"
            f"Description:\n{job.description or ''}\n\n"
            f"Requirements:\n{job.requirements or ''}\n\n"
            f"Responsibilities:\n{job.responsibilities or ''}"
        )
        ai = AIService()
        result = asyncio.run(ai.analyze_job(job_text))
        analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()
        if not analysis:
            analysis = JobAnalysis(job_id=job.id)
            db.add(analysis)
        analysis.role_category = result.get("role_category")
        analysis.seniority_level = result.get("seniority_level")
        analysis.required_years_experience = result.get("required_years_experience")
        analysis.required_skills = result.get("required_skills", [])
        analysis.nice_to_have_skills = result.get("nice_to_have_skills", [])
        analysis.tools = result.get("tools", [])
        analysis.responsibilities = result.get("responsibilities", [])
        analysis.ats_keywords = result.get("ats_keywords", [])
        analysis.industry = result.get("industry")
        analysis.red_flags = result.get("red_flags", [])
        analysis.is_junior_fit = result.get("is_junior_fit", True)
        analysis.raw_analysis = result
        job.is_analyzed = True
        db.commit()
        logger.info(f"Job {job_id} analyzed successfully")
    except Exception as exc:
        logger.error(f"Error analyzing job {job_id}: {exc}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="job_tasks.match_cv_job", bind=True)
def match_cv_job_task(self, job_id: str, cv_id: str, user_id: str):
    from sqlalchemy.orm import joinedload
    from ..models.cv import CV, JobCVMatch
    from ..utils.file_utils import extract_text
    db = SessionLocal()
    try:
        job = db.query(Job).options(joinedload(Job.analysis)).filter(Job.id == job_id).first()
        cv = db.query(CV).options(joinedload(CV.analysis)).filter(CV.id == cv_id).first()
        if not job or not cv or not job.analysis or not cv.analysis:
            return
        file_type = cv.file_type.value if hasattr(cv.file_type, "value") else str(cv.file_type)
        cv_text = extract_text(cv.file_path, file_type)
        job_text = f"{job.title}\n{job.company}\n{job.description or ''}\n{job.requirements or ''}"
        cv_data = {
            "skills": cv.analysis.skills,
            "tools": cv.analysis.tools,
            "work_experience": cv.analysis.work_experience,
            "education": cv.analysis.education,
            "certifications": cv.analysis.certifications,
        }
        job_data = {
            "required_skills": job.analysis.required_skills,
            "nice_to_have_skills": job.analysis.nice_to_have_skills,
            "tools": job.analysis.tools,
            "ats_keywords": job.analysis.ats_keywords,
            "role_category": job.analysis.role_category,
            "seniority_level": job.analysis.seniority_level,
            "required_years_experience": job.analysis.required_years_experience,
        }
        ai = AIService()
        result = asyncio.run(ai.match_cv_to_job(cv_data, job_data, cv_text, job_text))
        existing = db.query(JobCVMatch).filter(
            JobCVMatch.job_id == job.id, JobCVMatch.cv_id == cv.id
        ).first()
        if not existing:
            existing = JobCVMatch(job_id=job.id, cv_id=cv.id, user_id=user_id)
            db.add(existing)
        for k, v in result.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        existing.raw_match = result
        db.commit()
    except Exception as exc:
        logger.error(f"Error matching {cv_id} -> {job_id}: {exc}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="job_tasks.sync_source")
def sync_source_task(source_id: str, user_id: str):
    from ..models.job import JobSource
    from datetime import datetime
    db = SessionLocal()
    try:
        source = db.query(JobSource).filter(JobSource.id == source_id).first()
        if not source:
            return
        source.sync_status = SyncStatus.syncing
        db.commit()
        if source.source_type.value == "rss" and source.url:
            import feedparser
            feed = feedparser.parse(source.url)
            for entry in feed.entries[:20]:
                url = entry.get("link", "")
                if url and not db.query(Job).filter(Job.url == url, Job.user_id == user_id).first():
                    job = Job(
                        user_id=user_id,
                        source_id=source_id,
                        title=entry.get("title", "Unknown"),
                        company=entry.get("author", ""),
                        url=url,
                        description=entry.get("summary", ""),
                        source=source.name,
                    )
                    db.add(job)
                    db.flush()
                    scrape_job_task.delay(str(job.id), url, user_id)
            db.commit()
        source.sync_status = SyncStatus.success
        source.last_sync_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        logger.error(f"Error syncing source {source_id}: {exc}")
        db.rollback()
        src = db.query(JobSource).filter(JobSource.id == source_id).first()
        if src:
            src.sync_status = SyncStatus.error
            db.commit()
    finally:
        db.close()
