from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest
from app.schemas.leave import (
    LeaveBalanceResponse,
    LeaveRequestCreate,
    LeaveResponse,
    LeaveStatusUpdate,
)

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[LeaveResponse], summary="List leave requests")
def list_leaves(
    db: DatabaseSession,
    current_user: CurrentUser,
    employee_id: int | None = None,
    status_filter: str | None = None,
    limit: int = Query(default=100, le=500),
):
    query = db.query(LeaveRequest)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)

    leaves = query.order_by(LeaveRequest.created_at.desc()).limit(limit).all()

    result = []
    for leave in leaves:
        item = LeaveResponse.model_validate(leave)
        if leave.employee and leave.employee.user:
            item.employee_name = leave.employee.user.full_name
        elif leave.employee:
            item.employee_name = leave.employee.employee_code
        result.append(item)
    return result


@router.post(
    "/",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for leave",
)
def apply_leave(
    data: LeaveRequestCreate, db: DatabaseSession, current_user: CurrentUser
):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    if data.end_date < data.start_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be earlier than start date."
        )

    leave = LeaveRequest(
        employee_id=employee.id,
        leave_type=data.leave_type.upper(),
        start_date=data.start_date,
        end_date=data.end_date,
        days_count=data.days_count,
        reason=data.reason,
        status="PENDING",
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)

    item = LeaveResponse.model_validate(leave)
    item.employee_name = employee.user.full_name if employee.user else employee.employee_code
    return item


@router.patch("/{leave_id}/status", response_model=LeaveResponse, summary="Approve or reject leave")
def update_leave_status(
    leave_id: int,
    data: LeaveStatusUpdate,
    db: DatabaseSession,
    current_user: HRUser,
):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found.")

    valid_statuses = ["APPROVED", "REJECTED", "PENDING"]
    new_status = data.status.upper()
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value.")

    leave.status = new_status
    leave.reviewed_by_id = current_user.id
    if data.rejection_reason:
        leave.rejection_reason = data.rejection_reason

    # If approved, update LeaveBalance
    if new_status == "APPROVED":
        balance = (
            db.query(LeaveBalance)
            .filter(
                LeaveBalance.employee_id == leave.employee_id,
                LeaveBalance.year == leave.start_date.year,
            )
            .first()
        )
        if not balance:
            balance = LeaveBalance(employee_id=leave.employee_id, year=leave.start_date.year)
            db.add(balance)

        days = int(leave.days_count)
        if leave.leave_type == "CASUAL":
            balance.used_casual += days
        elif leave.leave_type == "SICK":
            balance.used_sick += days
        elif leave.leave_type == "ANNUAL":
            balance.used_annual += days

    db.commit()
    db.refresh(leave)

    item = LeaveResponse.model_validate(leave)
    if leave.employee and leave.employee.user:
        item.employee_name = leave.employee.user.full_name
    return item


@router.get("/balance/{employee_id}", response_model=LeaveBalanceResponse, summary="Get leave balance")
def get_leave_balance(
    employee_id: int, db: DatabaseSession, current_user: CurrentUser, year: int = 2026
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    balance = (
        db.query(LeaveBalance)
        .filter(LeaveBalance.employee_id == employee_id, LeaveBalance.year == year)
        .first()
    )
    if not balance:
        balance = LeaveBalance(employee_id=employee_id, year=year)
        db.add(balance)
        db.commit()
        db.refresh(balance)

    return LeaveBalanceResponse(
        id=balance.id,
        employee_id=balance.employee_id,
        year=balance.year,
        casual_leave=balance.casual_leave,
        sick_leave=balance.sick_leave,
        annual_leave=balance.annual_leave,
        used_casual=balance.used_casual,
        used_sick=balance.used_sick,
        used_annual=balance.used_annual,
        remaining_casual=max(0, balance.casual_leave - balance.used_casual),
        remaining_sick=max(0, balance.sick_leave - balance.used_sick),
        remaining_annual=max(0, balance.annual_leave - balance.used_annual),
    )
