from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.database import get_db
from app.models.attendance import Attendance
from app.models.attrition_history import AttritionHistory
from app.models.department import Department
from app.models.employee import Employee
from app.models.payroll import Payroll

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/workforce-summary", summary="Workforce headcount & department report")
def get_workforce_report(db: DatabaseSession, current_user: CurrentUser):
    total = db.query(Employee).count()
    active = db.query(Employee).filter(Employee.is_active == True).count()
    inactive = total - active

    departments = db.query(Department).all()
    dept_stats = []
    for d in departments:
        emp_count = (
            db.query(Employee)
            .filter(Employee.department_id == d.id, Employee.is_active == True)
            .count()
        )
        dept_stats.append({
            "department_id": d.id,
            "department_name": d.name,
            "employee_count": emp_count,
        })

    return {
        "total_employees": total,
        "active_employees": active,
        "inactive_employees": inactive,
        "departments": dept_stats,
    }


@router.get("/attendance-summary", summary="Workforce attendance analytics report")
def get_attendance_report(db: DatabaseSession, current_user: CurrentUser):
    records = db.query(Attendance).all()
    total_punches = len(records)
    total_hours = sum(r.working_hours for r in records)
    total_overtime = sum(r.overtime_hours for r in records)
    late_punches = sum(1 for r in records if r.status == "LATE")

    avg_hours = round(total_hours / total_punches, 2) if total_punches > 0 else 0.0

    return {
        "total_attendance_records": total_punches,
        "total_hours_worked": round(total_hours, 1),
        "total_overtime_hours": round(total_overtime, 1),
        "total_late_arrivals": late_punches,
        "average_hours_per_shift": avg_hours,
    }


@router.get("/payroll-summary", summary="Financial payroll expenditure report")
def get_payroll_report(db: DatabaseSession, current_user: CurrentUser):
    payrolls = db.query(Payroll).all()
    total_expenditure = sum(p.net_salary for p in payrolls)
    total_tax = sum(p.tax for p in payrolls)
    total_bonuses = sum(p.bonus for p in payrolls)
    avg_net = (
        round(float(total_expenditure) / len(payrolls), 2)
        if len(payrolls) > 0
        else 0.0
    )

    return {
        "total_payrolls_processed": len(payrolls),
        "total_net_expenditure": float(total_expenditure),
        "total_tax_deducted": float(total_tax),
        "total_bonuses_paid": float(total_bonuses),
        "average_net_salary": avg_net,
    }


@router.get("/attrition-summary", summary="Attrition predictions summary report")
def get_attrition_report(db: DatabaseSession, current_user: CurrentUser):
    records = db.query(AttritionHistory).all()
    high_risk = sum(1 for r in records if r.risk_level == "HIGH")
    medium_risk = sum(1 for r in records if r.risk_level == "MEDIUM")
    low_risk = sum(1 for r in records if r.risk_level == "LOW")

    avg_risk = (
        round(sum(r.attrition_risk_percentage for r in records) / len(records), 2)
        if records
        else 0.0
    )

    return {
        "total_predictions": len(records),
        "high_risk_count": high_risk,
        "medium_risk_count": medium_risk,
        "low_risk_count": low_risk,
        "average_risk_percentage": avg_risk,
    }
