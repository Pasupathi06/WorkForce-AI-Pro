from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.schemas.payroll import (
    PayrollGenerateRequest,
    PayrollResponse,
    PayrollStatusUpdate,
)

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[PayrollResponse], summary="List payroll records")
def list_payrolls(
    db: DatabaseSession,
    current_user: CurrentUser,
    employee_id: int | None = None,
    month: str | None = None,
    status_filter: str | None = None,
    limit: int = Query(default=100, le=500),
):
    query = db.query(Payroll)
    if employee_id:
        query = query.filter(Payroll.employee_id == employee_id)
    if month:
        query = query.filter(Payroll.month == month)
    if status_filter:
        query = query.filter(Payroll.status == status_filter)

    records = query.order_by(Payroll.month.desc(), Payroll.id.desc()).limit(limit).all()

    result = []
    for p in records:
        item = PayrollResponse.model_validate(p)
        if p.employee:
            item.employee_code = p.employee.employee_code
            if p.employee.user:
                item.employee_name = p.employee.user.full_name
            if p.employee.department:
                item.department_name = p.employee.department.name
        result.append(item)
    return result


@router.post(
    "/generate",
    response_model=PayrollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate payroll for employee",
)
def generate_payroll(
    data: PayrollGenerateRequest, db: DatabaseSession, current_user: HRUser
):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    existing = (
        db.query(Payroll)
        .filter(Payroll.employee_id == employee.id, Payroll.month == data.month)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Payroll for {data.month} already exists for this employee.",
        )

    basic_salary = employee.salary
    allowances = data.allowances
    bonus = data.bonus
    deductions = data.deductions

    # Standard tax estimation (approx 10% of basic + allowances)
    gross = basic_salary + allowances + bonus
    tax = round(gross * Decimal("0.10"), 2)
    net_salary = max(Decimal("0.00"), gross - deductions - tax)

    payroll = Payroll(
        employee_id=employee.id,
        month=data.month,
        basic_salary=basic_salary,
        allowances=allowances,
        bonus=bonus,
        deductions=deductions,
        tax=tax,
        net_salary=net_salary,
        status="DRAFT",
        notes=data.notes,
    )
    db.add(payroll)
    db.commit()
    db.refresh(payroll)

    item = PayrollResponse.model_validate(payroll)
    item.employee_code = employee.employee_code
    if employee.user:
        item.employee_name = employee.user.full_name
    if employee.department:
        item.department_name = employee.department.name
    return item


@router.patch("/{payroll_id}/status", response_model=PayrollResponse, summary="Update payroll status")
def update_payroll_status(
    payroll_id: int,
    data: PayrollStatusUpdate,
    db: DatabaseSession,
    current_user: HRUser,
):
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found.")

    valid_statuses = ["DRAFT", "PROCESSED", "PAID"]
    new_status = data.status.upper()
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value.")

    payroll.status = new_status
    if data.payment_method:
        payroll.payment_method = data.payment_method
    if new_status == "PAID":
        payroll.payment_date = data.payment_date or date.today()

    db.commit()
    db.refresh(payroll)

    item = PayrollResponse.model_validate(payroll)
    if payroll.employee:
        item.employee_code = payroll.employee.employee_code
        if payroll.employee.user:
            item.employee_name = payroll.employee.user.full_name
        if payroll.employee.department:
            item.department_name = payroll.employee.department.name
    return item


@router.get("/summary", summary="Get payroll summary metrics")
def get_payroll_summary(db: DatabaseSession, current_user: CurrentUser, month: str | None = None):
    query = db.query(Payroll)
    if month:
        query = query.filter(Payroll.month == month)

    records = query.all()
    total_payroll = sum(p.net_salary for p in records)
    total_tax = sum(p.tax for p in records)
    total_bonus = sum(p.bonus for p in records)
    paid_count = sum(1 for p in records if p.status == "PAID")
    processed_count = sum(1 for p in records if p.status == "PROCESSED")
    draft_count = sum(1 for p in records if p.status == "DRAFT")

    return {
        "record_count": len(records),
        "total_disbursed": float(total_payroll),
        "total_tax_deducted": float(total_tax),
        "total_bonuses": float(total_bonus),
        "paid_count": paid_count,
        "processed_count": processed_count,
        "draft_count": draft_count,
    }
