from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AttritionHistoryResponse(BaseModel):
    id: int
    employee_id: int | None
    predicted_by_user_id: int
    predicted_by_name: str | None = None
    attrition_probability: float = Field(ge=0, le=1)
    attrition_risk_percentage: float = Field(ge=0, le=100)
    risk_level: str = Field(pattern=r"^(LOW|MEDIUM|HIGH)$")
    model_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttritionHistoryListResponse(BaseModel):
    items: list[AttritionHistoryResponse]
    total: int
    page: int
    page_size: int
