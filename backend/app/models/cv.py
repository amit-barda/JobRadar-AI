import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class FileType(str, enum.Enum):
    pdf = "pdf"
    docx = "docx"

class Recommendation(str, enum.Enum):
    apply = "apply"
    maybe = "maybe"
    skip = "skip"

class Confidence(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class CV(Base):
    __tablename__ = "cvs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(SAEnum(FileType), nullable=False)
    is_active = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analysis = relationship("CVAnalysis", back_populates="cv", uselist=False, cascade="all, delete-orphan")
    matches = relationship("JobCVMatch", back_populates="cv", cascade="all, delete-orphan")

class CVAnalysis(Base):
    __tablename__ = "cv_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False, unique=True)
    professional_summary = Column(Text, nullable=True)
    skills = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    work_experience = Column(JSON, default=list)
    education = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    achievements = Column(JSON, default=list)
    product_management_indicators = Column(JSON, default=list)
    project_management_indicators = Column(JSON, default=list)
    weak_areas = Column(JSON, default=list)
    raw_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cv = relationship("CV", back_populates="analysis")

class JobCVMatch(Base):
    __tablename__ = "job_cv_matches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    final_score = Column(Float, default=0.0)
    recommendation = Column(SAEnum(Recommendation), default=Recommendation.skip)
    confidence = Column(SAEnum(Confidence), default=Confidence.low)
    score_breakdown = Column(JSON, default=dict)
    matching_skills = Column(JSON, default=list)
    missing_required_skills = Column(JSON, default=list)
    missing_nice_to_have_skills = Column(JSON, default=list)
    matching_tools = Column(JSON, default=list)
    missing_tools = Column(JSON, default=list)
    matching_keywords = Column(JSON, default=list)
    missing_keywords = Column(JSON, default=list)
    transferable_experience = Column(JSON, default=list)
    experience_gap = Column(Text, nullable=True)
    role_fit_reason = Column(Text, nullable=True)
    ats_feedback = Column(Text, nullable=True)
    cv_improvement_suggestions = Column(JSON, default=list)
    suggested_cv_bullets = Column(JSON, default=list)
    cover_letter_angle = Column(Text, nullable=True)
    cover_letter_text = Column(Text, nullable=True)
    risk_flags = Column(JSON, default=list)
    raw_match = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job = relationship("Job", back_populates="matches")
    cv = relationship("CV", back_populates="matches")
