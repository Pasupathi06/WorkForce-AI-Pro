from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ChatMessageCreate(BaseModel):
    receiver_id: int | None = None  # None for general channel
    channel: str = "general"
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int | None = None
    channel: str
    message: str
    is_read: bool
    created_at: datetime
    sender_name: str | None = None
    receiver_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
