from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate, AuditLogResponse

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[AuditLogResponse], summary="List audit logs")
def list_audit_logs(
    db: DatabaseSession,
    current_user: HRUser,
    action: str | None = None,
    target_type: str | None = None,
    limit: int = Query(default=100, le=500),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    result = []
    for log in logs:
        item = AuditLogResponse.model_validate(log)
        if log.user:
            item.user_name = log.user.full_name
        result.append(item)
    return result


@router.post(
    "/",
    response_model=AuditLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an audit log entry",
)
def record_audit_log(
    data: AuditLogCreate,
    request: Request,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    client_ip = request.client.host if request.client else None
    log = AuditLog(
        user_id=current_user.id,
        action=data.action,
        target_type=data.target_type,
        target_id=data.target_id,
        details=data.details,
        ip_address=client_ip,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    item = AuditLogResponse.model_validate(log)
    item.user_name = current_user.full_name
    return item
