from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.attendance import Attendance, Shift
from app.models.employee import Employee
from app.schemas.attendance import (
    AttendanceResponse,
    CheckInRequest,
    CheckOutRequest,
    ShiftCreate,
    ShiftResponse,
)

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/shifts", response_model=list[ShiftResponse], summary="List work shifts")
def list_shifts(db: DatabaseSession, current_user: CurrentUser):
    shifts = db.query(Shift).filter(Shift.is_active == True).all()
    if not shifts:
        # Seed default shifts if none exist
        from datetime import time

        default_shifts = [
            Shift(name="General Shift", start_time=time(9, 0), end_time=time(18, 0)),
            Shift(name="Morning Shift", start_time=time(6, 0), end_time=time(15, 0)),
            Shift(name="Evening Shift", start_time=time(14, 0), end_time=time(23, 0)),
            Shift(name="Night Shift", start_time=time(22, 0), end_time=time(7, 0)),
        ]
        db.add_all(default_shifts)
        db.commit()
        shifts = db.query(Shift).filter(Shift.is_active == True).all()
    return shifts


@router.post(
    "/shifts",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shift",
)
def create_shift(shift_data: ShiftCreate, db: DatabaseSession, current_user: HRUser):
    existing = db.query(Shift).filter(Shift.name == shift_data.name.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Shift with this name already exists.",
        )
    shift = Shift(
        name=shift_data.name.strip(),
        start_time=shift_data.start_time,
        end_time=shift_data.end_time,
        is_active=shift_data.is_active,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.post("/check-in", response_model=AttendanceResponse, summary="Clock in employee")
def clock_in(data: CheckInRequest, db: DatabaseSession, current_user: CurrentUser):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    today = date.today()
    record = (
        db.query(Attendance)
        .filter(Attendance.employee_id == employee.id, Attendance.date == today)
        .first()
    )

    now = datetime.now()
    if record and record.check_in is not None:
        raise HTTPException(status_code=400, detail="Employee has already clocked in today.")

    # Determine status (LATE if checking in after 09:30 AM in General shift)
    punch_status = "PRESENT"
    if now.hour > 9 or (now.hour == 9 and now.minute > 30):
        punch_status = "LATE"

    if not record:
        record = Attendance(
            employee_id=employee.id,
            shift_id=data.shift_id,
            date=today,
            check_in=now,
            status=punch_status,
            notes=data.notes,
        )
        db.add(record)
    else:
        record.check_in = now
        record.status = punch_status
        if data.notes:
            record.notes = data.notes

    db.commit()
    db.refresh(record)

    res = AttendanceResponse.model_validate(record)
    res.employee_name = employee.user.full_name if employee.user else employee.employee_code
    if record.shift:
        res.shift_name = record.shift.name
    return res


@router.post("/check-out", response_model=AttendanceResponse, summary="Clock out employee")
def clock_out(data: CheckOutRequest, db: DatabaseSession, current_user: CurrentUser):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    today = date.today()
    record = (
        db.query(Attendance)
        .filter(Attendance.employee_id == employee.id, Attendance.date == today)
        .first()
    )

    if not record or not record.check_in:
        raise HTTPException(status_code=400, detail="Employee has not clocked in today.")

    now = datetime.now()
    record.check_out = now

    # Calculate hours
    check_in_time = record.check_in
    if check_in_time.tzinfo is not None:
        check_in_time = check_in_time.replace(tzinfo=None)
    elapsed = (now - check_in_time).total_seconds() / 3600.0
    record.working_hours = round(elapsed, 2)
    record.overtime_hours = round(max(0.0, elapsed - 8.0), 2)

    if data.notes:
        record.notes = (record.notes or "") + " | Out: " + data.notes

    db.commit()
    db.refresh(record)

    res = AttendanceResponse.model_validate(record)
    res.employee_name = employee.user.full_name if employee.user else employee.employee_code
    if record.shift:
        res.shift_name = record.shift.name
    return res


@router.get("/", response_model=list[AttendanceResponse], summary="List attendance logs")
def list_attendance(
    db: DatabaseSession,
    current_user: CurrentUser,
    employee_id: int | None = None,
    log_date: date | None = None,
    month: str | None = None,
    status_filter: str | None = None,
    limit: int = Query(default=100, le=500),
):
    query = db.query(Attendance)
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if log_date:
        query = query.filter(Attendance.date == log_date)
    if month:
        # e.g., '2026-10'
        query = query.filter(func.to_char(Attendance.date, "YYYY-MM") == month)
    if status_filter:
        query = query.filter(Attendance.status == status_filter)

    records = query.order_by(Attendance.date.desc(), Attendance.id.desc()).limit(limit).all()

    result = []
    for r in records:
        item = AttendanceResponse.model_validate(r)
        if r.employee and r.employee.user:
            item.employee_name = r.employee.user.full_name
        elif r.employee:
            item.employee_name = r.employee.employee_code
        if r.shift:
            item.shift_name = r.shift.name
        result.append(item)
    return result


@router.get("/summary", summary="Get today's attendance summary")
def get_attendance_summary(db: DatabaseSession, current_user: CurrentUser):
    today = date.today()
    total_employees = db.query(Employee).filter(Employee.is_active == True).count()
    present_count = (
        db.query(Attendance)
        .filter(Attendance.date == today, Attendance.check_in != None)
        .count()
    )
    late_count = (
        db.query(Attendance)
        .filter(Attendance.date == today, Attendance.status == "LATE")
        .count()
    )
    half_day_count = (
        db.query(Attendance)
        .filter(Attendance.date == today, Attendance.status == "HALF_DAY")
        .count()
    )
    absent_count = max(0, total_employees - present_count)

    return {
        "date": today.isoformat(),
        "total_employees": total_employees,
        "present": present_count,
        "late": late_count,
        "half_day": half_day_count,
        "absent": absent_count,
        "attendance_rate": round((present_count / total_employees * 100), 1)
        if total_employees > 0
        else 0.0,
    }
