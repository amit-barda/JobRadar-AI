import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class SourceType(str, enum.Enum):
    email = "email"
    api = "api"
    rss = "rss"
    manual_url = "manual_url"
    manual = "manual"

class SyncStatus(str, enum.Enum):
    idle = "idle"
    syncing = "syncing"
    error = "error"
    success = "success"

class WorkType(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    unknown = "unknown"

class JobStatus(str, enum.Enum):
    new = "new"
    saved = "saved"
    applied = "applied"
    interview = "interview"
    rejected = "rejected"
    offer = "offer"
    archived = "archived"
    not_relevant = "not_relevant"

class JobSource(Base):
    __tablename__ = "job_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    source_type = Column(SAEnum(SourceType), nullable=False)
    url = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    keywords = Column(JSON, default=list)
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(SAEnum(SyncStatus), default=SyncStatus.idle)
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False, default="")
    location = Column(String, nullable=True)
    work_type = Column(SAEnum(WorkType), default=WorkType.unknown)
    source = Column(String, nullable=True)
    url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)
    required_experience = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    date_posted = Column(DateTime, nullable=True)
    date_added = Column(DateTime, default=datetime.utcnow)
    status = Column(SAEnum(JobStatus), default=JobStatus.new)
    is_analyzed = Column(Boolean, default=False)
    raw_html = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analysis = relationship("JobAnalysis", back_populates="job", uselist=False, cascade="all, delete-orphan")
    matches = relationship("JobCVMatch", back_populates="job", cascade="all, delete-orphan")

class JobAnalysis(Base):
    __tablename__ = "job_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    role_category = Column(String, nullable=True)
    seniority_level = Column(String, nullable=True)
    required_years_experience = Column(Float, nullable=True)
    required_skills = Column(JSON, default=list)
    nice_to_have_skills = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    responsibilities = Column(JSON, default=list)
    ats_keywords = Column(JSON, default=list)
    industry = Column(String, nullable=True)
    red_flags = Column(JSON, default=list)
    is_junior_fit = Column(Boolean, default=True)
    raw_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job = relationship("Job", back_populates="analysis")
