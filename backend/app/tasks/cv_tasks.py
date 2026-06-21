import asyncio
import logging
from .celery_app import celery_app
from ..database import SessionLocal
from ..models.cv import CV, CVAnalysis
from ..services.ai_service import AIService
from ..utils.file_utils import extract_text

logger = logging.getLogger(__name__)


@celery_app.task(name="cv_tasks.analyze_cv", bind=True, max_retries=2)
def analyze_cv_task(self, cv_id: str):
    db = SessionLocal()
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            return
        file_type = cv.file_type.value if hasattr(cv.file_type, "value") else str(cv.file_type)
        cv_text = extract_text(cv.file_path, file_type)
        if not cv_text.strip():
            logger.warning(f"No text extracted from CV {cv_id}")
            return
        ai = AIService()
        result = asyncio.run(ai.analyze_cv(cv_text))
        analysis = db.query(CVAnalysis).filter(CVAnalysis.cv_id == cv.id).first()
        if not analysis:
            analysis = CVAnalysis(cv_id=cv.id)
            db.add(analysis)
        analysis.professional_summary = result.get("professional_summary")
        analysis.skills = result.get("skills", [])
        analysis.tools = result.get("tools", [])
        analysis.work_experience = result.get("work_experience", [])
        analysis.education = result.get("education", [])
        analysis.certifications = result.get("certifications", [])
        analysis.projects = result.get("projects", [])
        analysis.languages = result.get("languages", [])
        analysis.achievements = result.get("achievements", [])
        analysis.product_management_indicators = result.get("product_management_indicators", [])
        analysis.project_management_indicators = result.get("project_management_indicators", [])
        analysis.weak_areas = result.get("weak_areas", [])
        analysis.raw_analysis = result
        cv.is_analyzed = True
        db.commit()
        logger.info(f"CV {cv_id} analyzed successfully")
    except Exception as exc:
        logger.error(f"Error analyzing CV {cv_id}: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
