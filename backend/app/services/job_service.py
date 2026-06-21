import json
from datetime import datetime
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.job import Job, JobAnalysis, JobStatus, WorkType
from . import scraper_service, openai_service


# ─── Prompts ────────────────────────────────────────────────────────────────

_JOB_PARSE_SYSTEM = """You are a job-listing parser.
Given raw text from a job posting, extract structured data and return a JSON object with these fields:
{
  "title": "Job Title",
  "company": "Company Name",
  "location": "City, Country or Remote",
  "work_type": "remote|hybrid|onsite|unknown",
  "description": "Full job description text",
  "requirements": "Requirements/qualifications text",
  "responsibilities": "Key responsibilities text",
  "required_experience": "e.g. 3-5 years",
  "salary": "Salary range or null",
  "date_posted": "ISO date string or null"
}
If a field cannot be determined, use null."""

_JOB_ANALYSIS_SYSTEM = """You are a senior technical recruiter analyzing job postings.
Given a job description, return a detailed JSON analysis with these fields:
{
  "role_category": "Product Manager|Project Manager|Engineering|Design|...",
  "seniority_level": "Junior|Mid|Senior|Lead|Director|VP|...",
  "required_years_experience": 3.0,
  "required_skills": ["skill1", "skill2"],
  "nice_to_have_skills": ["skill1"],
  "tools": ["Jira", "Figma"],
  "responsibilities": ["Responsibility 1"],
  "ats_keywords": ["keyword1"],
  "industry": "FinTech|HealthTech|...",
  "red_flags": ["any concerns about the role or company"],
  "is_junior_fit": true
}"""


# ─── Helpers ────────────────────────────────────────────────────────────────

def _determine_work_type(text: str) -> WorkType:
    text_lower = text.lower()
    if "remote" in text_lower:
        if "hybrid" in text_lower:
            return WorkType.hybrid
        return WorkType.remote
    if "hybrid" in text_lower:
        return WorkType.hybrid
    if "on-site" in text_lower or "onsite" in text_lower or "office" in text_lower:
        return WorkType.onsite
    return WorkType.unknown


def _parse_date(date_str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
    except Exception:
        return None


# ─── Public API ─────────────────────────────────────────────────────────────

def create_job_from_url(db: Session, user_id: str, url: str) -> Job:
    raw_html, text = scraper_service.scrape_job_page(url)

    if text:
        parsed = openai_service.chat_json(_JOB_PARSE_SYSTEM, f"Job page text:\n\n{text[:8000]}")
    else:
        parsed = {}

    work_type = _determine_work_type(
        f"{parsed.get('location', '')} {parsed.get('work_type', '')} {parsed.get('description', '')}"
    )

    job = Job(
        user_id=user_id,
        title=parsed.get("title") or "Unknown Title",
        company=parsed.get("company") or "Unknown Company",
        location=parsed.get("location"),
        work_type=work_type,
        source="url",
        url=url,
        description=parsed.get("description"),
        requirements=parsed.get("requirements"),
        responsibilities=parsed.get("responsibilities"),
        required_experience=parsed.get("required_experience"),
        salary=parsed.get("salary"),
        date_posted=_parse_date(parsed.get("date_posted")),
        raw_html=raw_html[:50000] if raw_html else None,
        status=JobStatus.new,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_job_from_email(
    db: Session, user_id: str, content: str, source_name: str = "Email Alert"
) -> Job:
    parsed = openai_service.chat_json(
        _JOB_PARSE_SYSTEM, f"Job email content:\n\n{content[:8000]}"
    )

    work_type = _determine_work_type(
        f"{parsed.get('location', '')} {parsed.get('work_type', '')} {parsed.get('description', '')}"
    )

    job = Job(
        user_id=user_id,
        title=parsed.get("title") or "Unknown Title",
        company=parsed.get("company") or "Unknown Company",
        location=parsed.get("location"),
        work_type=work_type,
        source=source_name,
        url=parsed.get("url"),
        description=parsed.get("description") or content,
        requirements=parsed.get("requirements"),
        responsibilities=parsed.get("responsibilities"),
        required_experience=parsed.get("required_experience"),
        salary=parsed.get("salary"),
        date_posted=_parse_date(parsed.get("date_posted")),
        status=JobStatus.new,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def analyze_job(db: Session, job_id: str) -> JobAnalysis | None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return None

    text_parts = [job.title or "", job.description or "", job.requirements or "", job.responsibilities or ""]
    full_text = "\n".join(p for p in text_parts if p)

    result = openai_service.chat_json(_JOB_ANALYSIS_SYSTEM, f"Job posting:\n\n{full_text[:8000]}")

    existing = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    if existing:
        analysis = existing
    else:
        analysis = JobAnalysis(job_id=job_id)
        db.add(analysis)

    analysis.role_category = result.get("role_category")
    analysis.seniority_level = result.get("seniority_level")
    analysis.required_years_experience = result.get("required_years_experience")
    analysis.required_skills = result.get("required_skills") or []
    analysis.nice_to_have_skills = result.get("nice_to_have_skills") or []
    analysis.tools = result.get("tools") or []
    analysis.responsibilities = result.get("responsibilities") or []
    analysis.ats_keywords = result.get("ats_keywords") or []
    analysis.industry = result.get("industry")
    analysis.red_flags = result.get("red_flags") or []
    analysis.is_junior_fit = bool(result.get("is_junior_fit", True))
    analysis.raw_analysis = result

    job.is_analyzed = True
    db.commit()
    db.refresh(analysis)
    return analysis


def analyze_job_background(job_id: str):
    """Background task wrapper."""
    db = SessionLocal()
    try:
        analyze_job(db, job_id)
    except Exception as e:
        print(f"[job_service] Error analyzing job {job_id}: {e}")
    finally:
        db.close()
