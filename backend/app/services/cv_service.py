from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.cv import CV, CVAnalysis
from ..utils.file_utils import extract_text
from . import openai_service


_CV_ANALYSIS_SYSTEM = """You are an expert resume/CV analyst for Product and Project Manager roles.
Analyze the provided CV text and return a detailed JSON object with these fields:
{
  "professional_summary": "2-3 sentence summary of the candidate",
  "skills": ["Agile", "Scrum", "Roadmapping"],
  "tools": ["Jira", "Confluence", "Figma"],
  "work_experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "duration": "Jan 2021 - Dec 2023",
      "years": 3.0,
      "highlights": ["Achievement 1", "Achievement 2"]
    }
  ],
  "education": [
    {"degree": "BSc Computer Science", "institution": "MIT", "year": "2015"}
  ],
  "certifications": ["PMP", "CSPO"],
  "projects": ["Notable project 1"],
  "languages": ["English", "Hebrew"],
  "achievements": ["Grew revenue by 30%"],
  "product_management_indicators": ["Defined product roadmap", "Led cross-functional teams"],
  "project_management_indicators": ["Managed $2M budget", "Delivered on time"],
  "weak_areas": ["No formal PM certification", "Limited data analysis"]
}"""


def analyze_cv(db: Session, cv_id: str) -> CVAnalysis | None:
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        return None

    text = extract_text(cv.file_path, cv.file_type)
    if not text.strip():
        return None

    result = openai_service.chat_json(_CV_ANALYSIS_SYSTEM, f"CV Text:\n\n{text[:10000]}")

    existing = db.query(CVAnalysis).filter(CVAnalysis.cv_id == cv_id).first()
    if existing:
        analysis = existing
    else:
        analysis = CVAnalysis(cv_id=cv_id)
        db.add(analysis)

    analysis.professional_summary = result.get("professional_summary")
    analysis.skills = result.get("skills") or []
    analysis.tools = result.get("tools") or []
    analysis.work_experience = result.get("work_experience") or []
    analysis.education = result.get("education") or []
    analysis.certifications = result.get("certifications") or []
    analysis.projects = result.get("projects") or []
    analysis.languages = result.get("languages") or []
    analysis.achievements = result.get("achievements") or []
    analysis.product_management_indicators = result.get("product_management_indicators") or []
    analysis.project_management_indicators = result.get("project_management_indicators") or []
    analysis.weak_areas = result.get("weak_areas") or []
    analysis.raw_analysis = result

    cv.is_analyzed = True
    db.commit()
    db.refresh(analysis)
    return analysis


def analyze_cv_background(cv_id: str):
    """Background task wrapper."""
    db = SessionLocal()
    try:
        analyze_cv(db, cv_id)
    except Exception as e:
        print(f"[cv_service] Error analyzing CV {cv_id}: {e}")
    finally:
        db.close()
