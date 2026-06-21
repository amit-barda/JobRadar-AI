from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.interview import InterviewPreparation
from ..models.job import Job, JobAnalysis
from ..models.cv import CV, CVAnalysis
from . import openai_service


_PREP_SYSTEM = """You are an expert interview coach for Product and Project Manager roles.
Given a job posting, generate comprehensive interview preparation material as JSON:
{
  "hr_questions": ["Tell me about yourself", "Why do you want this role?"],
  "product_questions": ["How do you prioritize features?", "Walk me through a product you built"],
  "technical_questions": ["How do you handle sprint planning?"],
  "behavioral_questions": ["Tell me about a time you failed", "How do you handle conflict?"],
  "star_suggestions": [
    "For 'Tell me about a time you failed': Use the STAR method — Situation: describe the project, Task: your role, Action: what you did, Result: what you learned.",
    "For behavioral questions: Always quantify impact (e.g. '30% faster', 'reduced churn by X')."
  ],
  "company_preparation": [
    "Research the company's latest product launches",
    "Review their LinkedIn for recent news and headcount changes",
    "Understand their competitive landscape"
  ]
}
Provide 5-8 questions per category. star_suggestions should be a list of STAR-method tips. company_preparation should be a list of research actions."""

_EVAL_SYSTEM = """You are an expert interview coach.
Evaluate the candidate's interview answer and provide structured feedback as JSON:
{
  "score": 75,
  "strengths": ["Clear structure", "Good use of metrics"],
  "improvements": ["Add more context about the impact", "Mention stakeholder communication"],
  "star_assessment": {
    "situation": "Good",
    "task": "Could be clearer",
    "action": "Strong",
    "result": "Needs quantification"
  },
  "example_better_answer": "A brief example of a stronger answer"
}
score is 0-100."""


def generate_prep(db: Session, prep_id: str) -> InterviewPreparation | None:
    prep = db.query(InterviewPreparation).filter(InterviewPreparation.id == prep_id).first()
    if not prep:
        return None

    job = db.query(Job).filter(Job.id == prep.job_id).first()
    if not job:
        return None

    job_analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()

    # Try to get the user's active CV
    cv_analysis = (
        db.query(CVAnalysis)
        .join(CV, CVAnalysis.cv_id == CV.id)
        .filter(CV.user_id == prep.user_id, CV.is_active == True)
        .first()
    )

    job_context = f"Job Title: {job.title}\nCompany: {job.company}\n"
    if job.description:
        job_context += f"Description:\n{job.description[:3000]}\n"
    if job_analysis:
        job_context += f"Required Skills: {', '.join(job_analysis.required_skills or [])}\n"
        job_context += f"Role Category: {job_analysis.role_category}\n"

    cv_context = ""
    if cv_analysis:
        cv_context = f"\nCandidate Skills: {', '.join(cv_analysis.skills or [])}\n"
        if cv_analysis.product_management_indicators:
            cv_context += f"PM Experience: {', '.join(cv_analysis.product_management_indicators)}\n"

    result = openai_service.chat_json(
        _PREP_SYSTEM, f"Job:\n{job_context}{cv_context}"
    )

    prep.hr_questions = result.get("hr_questions") or []
    prep.product_questions = result.get("product_questions") or []
    prep.technical_questions = result.get("technical_questions") or []
    prep.behavioral_questions = result.get("behavioral_questions") or []
    # Normalize star_suggestions to list
    raw_stars = result.get("star_suggestions") or []
    if isinstance(raw_stars, dict):
        raw_stars = [f"For '{k}': {v}" for k, v in raw_stars.items()]
    prep.star_suggestions = raw_stars
    # Normalize company_preparation to list
    raw_cp = result.get("company_preparation") or []
    if isinstance(raw_cp, str):
        raw_cp = [raw_cp] if raw_cp else []
    prep.company_preparation = raw_cp

    db.commit()
    db.refresh(prep)
    return prep


def generate_prep_background(prep_id: str):
    db = SessionLocal()
    try:
        generate_prep(db, prep_id)
    except Exception as e:
        print(f"[interview_service] Error generating prep {prep_id}: {e}")
    finally:
        db.close()


def get_mock_questions(db: Session, job_id: str, user_id: str) -> list[str]:
    prep = db.query(InterviewPreparation).filter(
        InterviewPreparation.job_id == job_id,
        InterviewPreparation.user_id == user_id,
    ).first()
    if not prep:
        return []
    questions = []
    for q_list in [prep.hr_questions, prep.product_questions, prep.behavioral_questions]:
        if q_list:
            questions.extend(q_list[:3])
    return questions[:10]


def evaluate_answer(question: str, answer: str) -> dict:
    try:
        result = openai_service.chat_json(
            _EVAL_SYSTEM,
            f"Question: {question}\n\nCandidate Answer: {answer}",
        )
        return result
    except Exception as e:
        return {"error": str(e), "score": 0}
