from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[NotificationResponse], summary="List notifications")
def list_notifications(
    db: DatabaseSession,
    current_user: CurrentUser,
    unread_only: bool = False,
    limit: int = Query(default=50, le=200),
):
    query = db.query(Notification).filter(
        or_(
            Notification.user_id == current_user.id,
            Notification.user_id == None,
        )
    )
    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = (
        query.order_by(Notification.created_at.desc()).limit(limit).all()
    )
    return notifications


@router.get("/unread-count", summary="Get unread notification count")
def get_unread_count(db: DatabaseSession, current_user: CurrentUser):
    count = (
        db.query(Notification)
        .filter(
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id == None,
            ),
            Notification.is_read == False,
        )
        .count()
    )
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification read")
def mark_as_read(
    notification_id: int, db: DatabaseSession, current_user: CurrentUser
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.patch("/read-all", summary="Mark all notifications read")
def mark_all_as_read(db: DatabaseSession, current_user: CurrentUser):
    db.query(Notification).filter(
        or_(
            Notification.user_id == current_user.id,
            Notification.user_id == None,
        ),
        Notification.is_read == False,
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read."}


@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and dispatch notification",
)
def create_notification(
    data: NotificationCreate, db: DatabaseSession, current_user: HRUser
):
    notif = Notification(
        user_id=data.user_id,
        title=data.title,
        message=data.message,
        type=data.type.upper(),
        priority=data.priority.upper(),
        is_read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
