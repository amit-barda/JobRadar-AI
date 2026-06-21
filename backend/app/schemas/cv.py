from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import uuid


class CVResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    is_active: bool
    is_analyzed: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class CVAnalysisResponse(BaseModel):
    id: uuid.UUID
    cv_id: uuid.UUID
    professional_summary: Optional[str]
    skills: List[str]
    tools: List[str]
    work_experience: List[Any]
    education: List[Any]
    certifications: List[str]
    projects: List[str]
    languages: List[str]
    achievements: List[str]
    product_management_indicators: List[str]
    project_management_indicators: List[str]
    weak_areas: List[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class CVDetailResponse(CVResponse):
    analysis: Optional[CVAnalysisResponse] = None


class JobCVMatchResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    cv_id: uuid.UUID
    final_score: float
    recommendation: str
    confidence: str
    score_breakdown: dict
    matching_skills: List[str]
    missing_required_skills: List[str]
    missing_nice_to_have_skills: List[str]
    matching_tools: List[str]
    missing_tools: List[str]
    matching_keywords: List[str]
    missing_keywords: List[str]
    transferable_experience: List[str]
    experience_gap: Optional[str]
    role_fit_reason: Optional[str]
    ats_feedback: Optional[str]
    cv_improvement_suggestions: List[str]
    suggested_cv_bullets: List[str]
    cover_letter_angle: Optional[str]
    cover_letter_text: Optional[str]
    risk_flags: List[str]
    created_at: datetime
    model_config = {"from_attributes": True}
