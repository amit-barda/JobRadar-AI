from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.cv import CV, CVAnalysis, JobCVMatch
from ..models.job import Job, JobAnalysis
from ..utils.file_utils import extract_text
from . import openai_service


_MATCH_SYSTEM = """You are an expert ATS and talent-matching system for Product and Project Manager roles.
Given a job analysis and a candidate CV analysis, produce a detailed match report as JSON:
{
  "final_score": 78.5,
  "recommendation": "apply|maybe|skip",
  "confidence": "low|medium|high",
  "score_breakdown": {
    "skills": 80,
    "tools": 70,
    "experience": 75,
    "keywords": 85,
    "seniority": 90
  },
  "matching_skills": ["Agile", "Roadmapping"],
  "missing_required_skills": ["SQL"],
  "missing_nice_to_have_skills": ["Tableau"],
  "matching_tools": ["Jira"],
  "missing_tools": ["Confluence"],
  "matching_keywords": ["cross-functional", "stakeholder"],
  "missing_keywords": ["OKR"],
  "transferable_experience": ["B2B SaaS experience transfers well"],
  "experience_gap": "Candidate has 3 years but role asks for 5+",
  "role_fit_reason": "Strong product sense and delivery track record",
  "ats_feedback": "CV should include more quantified achievements",
  "cv_improvement_suggestions": ["Add metrics to each role", "Mention OKR experience"],
  "suggested_cv_bullets": ["Led 0-to-1 product launch generating $1.2M ARR"],
  "cover_letter_angle": "Emphasize cross-functional leadership and B2B experience",
  "risk_flags": ["Short tenures at last two companies"]
}
final_score is 0-100. recommendation must be apply (>70), maybe (50-70), or skip (<50)."""


def run_match(db: Session, match_id: str) -> JobCVMatch | None:
    match = db.query(JobCVMatch).filter(JobCVMatch.id == match_id).first()
    if not match:
        return None

    job = db.query(Job).filter(Job.id == match.job_id).first()
    cv = db.query(CV).filter(CV.id == match.cv_id).first()
    if not job or not cv:
        return None

    job_analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()
    cv_analysis = db.query(CVAnalysis).filter(CVAnalysis.cv_id == cv.id).first()

    # Build context texts
    job_context = _build_job_context(job, job_analysis)
    cv_context = _build_cv_context(cv, cv_analysis)

    prompt = f"JOB:\n{job_context}\n\nCANDIDATE CV:\n{cv_context}"
    result = openai_service.chat_json(_MATCH_SYSTEM, prompt)

    match.final_score = float(result.get("final_score") or 0)
    match.recommendation = result.get("recommendation", "skip")
    match.confidence = result.get("confidence", "low")
    match.score_breakdown = result.get("score_breakdown") or {}
    match.matching_skills = result.get("matching_skills") or []
    match.missing_required_skills = result.get("missing_required_skills") or []
    match.missing_nice_to_have_skills = result.get("missing_nice_to_have_skills") or []
    match.matching_tools = result.get("matching_tools") or []
    match.missing_tools = result.get("missing_tools") or []
    match.matching_keywords = result.get("matching_keywords") or []
    match.missing_keywords = result.get("missing_keywords") or []
    match.transferable_experience = result.get("transferable_experience") or []
    match.experience_gap = result.get("experience_gap")
    match.role_fit_reason = result.get("role_fit_reason")
    match.ats_feedback = result.get("ats_feedback")
    match.cv_improvement_suggestions = result.get("cv_improvement_suggestions") or []
    match.suggested_cv_bullets = result.get("suggested_cv_bullets") or []
    match.cover_letter_angle = result.get("cover_letter_angle")
    match.risk_flags = result.get("risk_flags") or []
    match.raw_match = result

    db.commit()
    db.refresh(match)
    return match


def run_match_background(match_id: str):
    db = SessionLocal()
    try:
        run_match(db, match_id)
    except Exception as e:
        print(f"[match_service] Error running match {match_id}: {e}")
    finally:
        db.close()


def _build_job_context(job: Job, analysis: JobAnalysis | None) -> str:
    parts = [f"Title: {job.title}", f"Company: {job.company}"]
    if job.location:
        parts.append(f"Location: {job.location}")
    if job.description:
        parts.append(f"Description:\n{job.description[:3000]}")
    if analysis:
        parts += [
            f"Role Category: {analysis.role_category}",
            f"Seniority: {analysis.seniority_level}",
            f"Required Experience: {analysis.required_years_experience} years",
            f"Required Skills: {', '.join(analysis.required_skills or [])}",
            f"Nice-to-Have: {', '.join(analysis.nice_to_have_skills or [])}",
            f"Tools: {', '.join(analysis.tools or [])}",
            f"ATS Keywords: {', '.join(analysis.ats_keywords or [])}",
        ]
    return "\n".join(parts)


def _build_cv_context(cv: CV, analysis: CVAnalysis | None) -> str:
    if not analysis:
        text = extract_text(cv.file_path, cv.file_type)
        return text[:5000]
    parts = []
    if analysis.professional_summary:
        parts.append(f"Summary: {analysis.professional_summary}")
    if analysis.skills:
        parts.append(f"Skills: {', '.join(analysis.skills)}")
    if analysis.tools:
        parts.append(f"Tools: {', '.join(analysis.tools)}")
    if analysis.certifications:
        parts.append(f"Certifications: {', '.join(analysis.certifications)}")
    if analysis.product_management_indicators:
        parts.append(f"PM Indicators: {', '.join(analysis.product_management_indicators)}")
    if analysis.project_management_indicators:
        parts.append(f"PjM Indicators: {', '.join(analysis.project_management_indicators)}")
    if analysis.work_experience:
        exp_lines = []
        for exp in analysis.work_experience:
            if isinstance(exp, dict):
                exp_lines.append(f"  - {exp.get('title')} at {exp.get('company')} ({exp.get('duration', '')})")
        parts.append("Experience:\n" + "\n".join(exp_lines))
    return "\n".join(parts)
