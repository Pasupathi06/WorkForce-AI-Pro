from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    action: str
    target_type: str
    target_id: int | None = None
    details: str | None = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    action: str
    target_type: str
    target_id: int | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime
    user_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
