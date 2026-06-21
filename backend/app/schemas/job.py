from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import uuid


class JobSourceCreate(BaseModel):
    name: str
    source_type: str
    url: Optional[str] = None
    is_enabled: bool = True
    keywords: List[str] = []
    config: Optional[dict] = None


class JobSourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    url: Optional[str] = None
    is_enabled: Optional[bool] = None
    keywords: Optional[List[str]] = None
    config: Optional[dict] = None


class JobSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    url: Optional[str]
    is_enabled: bool
    keywords: List[str] = []
    last_sync_at: Optional[datetime]
    sync_status: str
    config: Optional[dict]
    created_at: datetime
    model_config = {"from_attributes": True}


class AddJobUrlRequest(BaseModel):
    url: str


class AddJobEmailRequest(BaseModel):
    content: str
    source_name: Optional[str] = "Email Alert"


class JobStatusUpdate(BaseModel):
    status: str


class JobAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    role_category: Optional[str]
    seniority_level: Optional[str]
    required_years_experience: Optional[float]
    required_skills: List[str]
    nice_to_have_skills: List[str]
    tools: List[str]
    responsibilities: List[str]
    ats_keywords: List[str]
    industry: Optional[str]
    red_flags: List[str]
    is_junior_fit: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_id: Optional[uuid.UUID]
    title: str
    company: str
    location: Optional[str]
    work_type: str
    source: Optional[str]
    url: Optional[str]
    description: Optional[str]
    requirements: Optional[str]
    responsibilities: Optional[str]
    required_experience: Optional[str]
    salary: Optional[str]
    date_posted: Optional[datetime]
    date_added: datetime
    status: str
    is_analyzed: bool
    created_at: datetime
    updated_at: datetime
    analysis: Optional[JobAnalysisResponse] = None
    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    per_page: int
