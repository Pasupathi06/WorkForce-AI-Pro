from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    user_id: int | None = None  # None for broadcast
    title: str
    message: str
    type: str = "INFO"  # INFO, WARNING, ALERT, SUCCESS
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT


class NotificationResponse(BaseModel):
    id: int
    user_id: int | None = None
    title: str
    message: str
    type: str
    priority: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
