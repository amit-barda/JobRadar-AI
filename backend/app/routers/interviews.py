from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.interview import InterviewPreparation, MockInterview, InterviewStatus
from ..models.job import Job
from ..models.user import User
from ..schemas.interview import (
    InterviewPrepResponse, MockInterviewResponse,
    MockAnswerRequest, StartMockRequest
)
from ..utils.auth import get_current_active_user
from ..services import interview_service

router = APIRouter()


def _get_or_create_prep(db: Session, job_id: str, user_id: str, background_tasks: BackgroundTasks) -> InterviewPreparation:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    prep = db.query(InterviewPreparation).filter(
        InterviewPreparation.job_id == job_id, InterviewPreparation.user_id == user_id
    ).first()

    if prep:
        return prep

    prep = InterviewPreparation(
        job_id=job_id,
        user_id=user_id,
        hr_questions=[],
        product_questions=[],
        technical_questions=[],
        behavioral_questions=[],
        star_suggestions=[],
        company_preparation=[],
    )
    db.add(prep)
    db.commit()
    db.refresh(prep)
    background_tasks.add_task(interview_service.generate_prep_background, str(prep.id))
    return prep


# --- Spec routes ---

@router.post("/job/{job_id}/prepare", response_model=InterviewPrepResponse, status_code=201)
def prepare_interview(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    prep = db.query(InterviewPreparation).filter(
        InterviewPreparation.job_id == job_id, InterviewPreparation.user_id == current_user.id
    ).first()

    if prep:
        # Regenerate
        background_tasks.add_task(interview_service.generate_prep_background, str(prep.id))
        return prep

    return _get_or_create_prep(db, job_id, str(current_user.id), background_tasks)


@router.get("/job/{job_id}", response_model=InterviewPrepResponse)
def get_interview_prep(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    prep = db.query(InterviewPreparation).filter(
        InterviewPreparation.job_id == job_id, InterviewPreparation.user_id == current_user.id
    ).first()
    if not prep:
        raise HTTPException(status_code=404, detail="Interview prep not found")
    return prep


@router.post("/mock/start", response_model=MockInterviewResponse, status_code=201)
def start_mock_interview(
    data: StartMockRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == data.job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    questions = interview_service.get_mock_questions(db, data.job_id, str(current_user.id))
    if not questions:
        raise HTTPException(
            status_code=400,
            detail="No interview questions available. Generate interview prep first."
        )

    mock = MockInterview(
        job_id=data.job_id,
        user_id=current_user.id,
        questions=questions,
        answers=[],
        feedbacks=[],
        current_question_index=0,
        status=InterviewStatus.active,
    )
    db.add(mock)
    db.commit()
    db.refresh(mock)
    return _format_mock(mock)


@router.get("/mock/{mock_id}", response_model=MockInterviewResponse)
def get_mock_interview(
    mock_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    mock = db.query(MockInterview).filter(
        MockInterview.id == mock_id, MockInterview.user_id == current_user.id
    ).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock interview not found")
    return _format_mock(mock)


@router.post("/mock/{mock_id}/answer", response_model=MockInterviewResponse)
def submit_answer(
    mock_id: str,
    data: MockAnswerRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    mock = db.query(MockInterview).filter(
        MockInterview.id == mock_id, MockInterview.user_id == current_user.id
    ).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock interview not found")
    if mock.status == InterviewStatus.completed:
        raise HTTPException(status_code=400, detail="Interview already completed")

    idx = mock.current_question_index
    if idx >= len(mock.questions):
        raise HTTPException(status_code=400, detail="No more questions")

    question = mock.questions[idx]
    feedback = interview_service.evaluate_answer(question, data.answer)

    mock.answers = list(mock.answers) + [data.answer]
    mock.feedbacks = list(mock.feedbacks) + [feedback]
    mock.current_question_index = idx + 1
    if mock.current_question_index >= len(mock.questions):
        mock.status = InterviewStatus.completed

    db.commit()
    db.refresh(mock)
    return _format_mock(mock)


@router.get("/mock", response_model=List[MockInterviewResponse])
def list_mock_interviews(
    job_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(MockInterview).filter(MockInterview.user_id == current_user.id)
    if job_id:
        query = query.filter(MockInterview.job_id == job_id)
    return [_format_mock(m) for m in query.order_by(MockInterview.created_at.desc()).all()]


def _format_mock(mock: MockInterview) -> dict:
    idx = mock.current_question_index
    questions = mock.questions or []
    return {
        "id": str(mock.id),
        "job_id": str(mock.job_id),
        "status": mock.status,
        "current_question_index": idx,
        "questions": questions,
        "answers": mock.answers or [],
        "feedbacks": mock.feedbacks or [],
        "current_question": questions[idx] if idx < len(questions) else None,
        "is_complete": mock.status == InterviewStatus.completed,
    }
