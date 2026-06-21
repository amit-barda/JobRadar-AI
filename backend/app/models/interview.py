import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base
import enum

class InterviewStatus(str, enum.Enum):
    active = "active"
    completed = "completed"

class InterviewPreparation(Base):
    __tablename__ = "interview_preparations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hr_questions = Column(JSON, default=list)
    product_questions = Column(JSON, default=list)
    technical_questions = Column(JSON, default=list)
    behavioral_questions = Column(JSON, default=list)
    star_suggestions = Column(JSON, default=list)
    company_preparation = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MockInterview(Base):
    __tablename__ = "mock_interviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum(InterviewStatus), default=InterviewStatus.active)
    current_question_index = Column(Integer, default=0)
    questions = Column(JSON, default=list)
    answers = Column(JSON, default=list)
    feedbacks = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
