from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    assigned_to_id: int
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    due_date: date | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    assigned_to_id: int
    created_by_id: int
    priority: str
    status: str
    due_date: date | None = None
    created_at: datetime
    updated_at: datetime
    assigned_to_name: str | None = None
    created_by_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
