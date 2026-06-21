from sqlalchemy.orm import Session
from ..models.job import Job, JobAnalysis
from ..models.cv import CV, CVAnalysis
from ..utils.file_utils import extract_text
from . import openai_service


_COVER_LETTER_SYSTEM = """You are an expert career coach specializing in Product and Project Manager roles.
Write a compelling, personalized cover letter for the candidate applying to this job.
The cover letter should:
- Be 3-4 paragraphs, professional but engaging
- Open with a strong hook
- Highlight 2-3 specific skills/achievements that match the role
- Show knowledge of the company/role
- Close with a clear call to action
- NOT use generic phrases like "I am writing to apply"
- Use first person and be conversational yet professional
Return ONLY the cover letter text, no JSON."""


def generate_cover_letter(db: Session, job: Job, cv: CV) -> str:
    job_analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()
    cv_analysis = db.query(CVAnalysis).filter(CVAnalysis.cv_id == cv.id).first()

    job_context = f"Job Title: {job.title}\nCompany: {job.company}\n"
    if job.location:
        job_context += f"Location: {job.location}\n"
    if job.description:
        job_context += f"Description:\n{job.description[:2500]}\n"
    if job_analysis:
        job_context += f"Key Required Skills: {', '.join((job_analysis.required_skills or [])[:10])}\n"
        job_context += f"ATS Keywords: {', '.join((job_analysis.ats_keywords or [])[:10])}\n"

    cv_context = ""
    if cv_analysis:
        cv_context = f"\nCandidate Summary: {cv_analysis.professional_summary or ''}\n"
        cv_context += f"Top Skills: {', '.join((cv_analysis.skills or [])[:12])}\n"
        cv_context += f"Tools: {', '.join((cv_analysis.tools or [])[:8])}\n"
        if cv_analysis.achievements:
            cv_context += f"Key Achievements: {'; '.join(cv_analysis.achievements[:3])}\n"
        if cv_analysis.product_management_indicators:
            cv_context += f"PM Experience: {'; '.join(cv_analysis.product_management_indicators[:3])}\n"
    else:
        raw_text = extract_text(cv.file_path, cv.file_type)
        cv_context = f"\nCV Text:\n{raw_text[:3000]}\n"

    prompt = f"JOB TO APPLY FOR:\n{job_context}\n\nCANDIDATE BACKGROUND:\n{cv_context}\n\nWrite the cover letter:"
    return openai_service.chat_completion(_COVER_LETTER_SYSTEM, prompt)
