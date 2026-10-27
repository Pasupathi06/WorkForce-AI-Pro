from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.database import get_db
from app.models.chat import ChatMessage
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/messages", response_model=list[ChatMessageResponse], summary="Retrieve chat messages")
def get_chat_messages(
    db: DatabaseSession,
    current_user: CurrentUser,
    channel: str = "general",
    other_user_id: int | None = None,
    limit: int = Query(default=100, le=300),
):
    if other_user_id:
        # Direct messaging between current_user and other_user
        query = db.query(ChatMessage).filter(
            or_(
                (ChatMessage.sender_id == current_user.id)
                & (ChatMessage.receiver_id == other_user_id),
                (ChatMessage.sender_id == other_user_id)
                & (ChatMessage.receiver_id == current_user.id),
            )
        )
    else:
        # Channel messaging
        query = db.query(ChatMessage).filter(
            ChatMessage.channel == channel, ChatMessage.receiver_id == None
        )

    messages = query.order_by(ChatMessage.created_at.asc()).limit(limit).all()

    result = []
    for m in messages:
        item = ChatMessageResponse.model_validate(m)
        if m.sender:
            item.sender_name = m.sender.full_name
        if m.receiver:
            item.receiver_name = m.receiver.full_name
        result.append(item)
    return result


@router.post(
    "/send",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a chat message",
)
def send_chat_message(
    data: ChatMessageCreate, db: DatabaseSession, current_user: CurrentUser
):
    text = data.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        channel=data.channel,
        message=text,
        is_read=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    item = ChatMessageResponse.model_validate(msg)
    item.sender_name = current_user.full_name
    if data.receiver_id:
        receiver = db.query(User).filter(User.id == data.receiver_id).first()
        if receiver:
            item.receiver_name = receiver.full_name
    return item


@router.get("/contacts", summary="Get list of users for messaging")
def get_contacts(db: DatabaseSession, current_user: CurrentUser):
    users = db.query(User).filter(User.is_active == True).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
        }
        for u in users
    ]
