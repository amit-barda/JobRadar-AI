from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import uuid


class InterviewPrepResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    hr_questions: List[str]
    product_questions: List[str]
    technical_questions: List[str]
    behavioral_questions: List[str]
    star_suggestions: List[Any]
    company_preparation: List[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class MockInterviewResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: str
    current_question_index: int
    questions: List[str]
    answers: List[str]
    feedbacks: List[Any]
    current_question: Optional[str] = None
    is_complete: bool = False
    model_config = {"from_attributes": True}


class MockAnswerRequest(BaseModel):
    answer: str


class StartMockRequest(BaseModel):
    job_id: str


class CoverLetterRequest(BaseModel):
    job_id: str
    cv_id: str
