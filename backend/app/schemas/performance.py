from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PerformanceReviewCreate(BaseModel):
    employee_id: int
    review_period: str
    rating: float = Field(ge=1.0, le=5.0)
    goals: str | None = None
    feedback: str | None = None
    strengths: str | None = None
    improvement_areas: str | None = None
    status: str = "COMPLETED"


class PerformanceReviewResponse(BaseModel):
    id: int
    employee_id: int
    reviewer_id: int
    review_period: str
    rating: float
    goals: str | None = None
    feedback: str | None = None
    strengths: str | None = None
    improvement_areas: str | None = None
    status: str
    created_at: datetime
    employee_name: str | None = None
    reviewer_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
