from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.api.deps import HRUser
from app.db.database import get_db
from app.models.attrition_history import AttritionHistory
from app.models.department import Department
from app.models.employee import Employee

router = APIRouter()

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/overview", summary="Get live workforce analytics")
def get_workforce_analytics(
    current_user: HRUser,
    db: DatabaseSession,
) -> dict:
    """Return workforce analytics aggregated from database records."""

    # Employee overview
    active_employees = (
        db.query(func.count(Employee.id))
        .filter(Employee.is_active.is_(True))
        .scalar()
        or 0
    )

    inactive_employees = (
        db.query(func.count(Employee.id))
        .filter(Employee.is_active.is_(False))
        .scalar()
        or 0
    )

    total_employees = active_employees + inactive_employees

    # Active employee distribution across active departments
    department_rows = (
        db.query(
            Department.id,
            Department.name,
            func.count(Employee.id).label("employee_count"),
        )
        .outerjoin(
            Employee,
            (Employee.department_id == Department.id)
            & (Employee.is_active.is_(True)),
        )
        .filter(Department.is_active.is_(True))
        .group_by(Department.id, Department.name)
        .order_by(Department.name.asc())
        .all()
    )

    department_distribution = [
        {
            "department_id": row.id,
            "department": row.name,
            "active_employees": int(row.employee_count or 0),
        }
        for row in department_rows
    ]

    # Monthly hiring based on employee joining dates
    hiring_rows = (
        db.query(
            extract("year", Employee.joining_date).label("year"),
            extract("month", Employee.joining_date).label("month"),
            func.count(Employee.id).label("total"),
        )
        .group_by(
            extract("year", Employee.joining_date),
            extract("month", Employee.joining_date),
        )
        .order_by(
            extract("year", Employee.joining_date),
            extract("month", Employee.joining_date),
        )
        .all()
    )

    monthly_hiring = [
        {
            "year": int(row.year),
            "month": int(row.month),
            "label": f"{int(row.year)}-{int(row.month):02d}",
            "employees_joined": int(row.total or 0),
        }
        for row in hiring_rows
        if row.year is not None and row.month is not None
    ]

    # Monthly saved attrition predictions
    prediction_rows = (
        db.query(
            extract("year", AttritionHistory.created_at).label("year"),
            extract("month", AttritionHistory.created_at).label("month"),
            func.count(AttritionHistory.id).label("total"),
            func.avg(
                AttritionHistory.attrition_risk_percentage
            ).label("average_risk"),
        )
        .group_by(
            extract("year", AttritionHistory.created_at),
            extract("month", AttritionHistory.created_at),
        )
        .order_by(
            extract("year", AttritionHistory.created_at),
            extract("month", AttritionHistory.created_at),
        )
        .all()
    )

    monthly_predictions = [
        {
            "year": int(row.year),
            "month": int(row.month),
            "label": f"{int(row.year)}-{int(row.month):02d}",
            "prediction_count": int(row.total or 0),
            "average_predicted_risk_percentage": (
                round(float(row.average_risk), 2)
                if row.average_risk is not None
                else None
            ),
        }
        for row in prediction_rows
        if row.year is not None and row.month is not None
    ]

    # Prediction count and risk distribution
    total_predictions = (
        db.query(func.count(AttritionHistory.id)).scalar() or 0
    )

    risk_rows = (
        db.query(
            AttritionHistory.risk_level,
            func.count(AttritionHistory.id).label("total"),
        )
        .group_by(AttritionHistory.risk_level)
        .all()
    )

    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for row in risk_rows:
        level = str(row.risk_level).upper()
        if level in risk_counts:
            risk_counts[level] = int(row.total or 0)

    average_risk = (
        db.query(func.avg(AttritionHistory.attrition_risk_percentage))
        .scalar()
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "employee_overview": {
            "total_employees": int(total_employees),
            "active_employees": int(active_employees),
            "inactive_employees": int(inactive_employees),
        },
        "department_distribution": department_distribution,
        "monthly_hiring": monthly_hiring,
        "prediction_overview": {
            "total_predictions": int(total_predictions),
            "average_predicted_risk_percentage": (
                round(float(average_risk), 2)
                if average_risk is not None
                else None
            ),
            "risk_distribution": risk_counts,
        },
        "monthly_predictions": monthly_predictions,
        "data_notes": {
            "hiring": "Based on employee joining dates in the database.",
            "predictions": (
                "Based on saved AI prediction records, not actual employee "
                "resignations."
            ),
            "attrition_rate": (
                "Actual attrition rate is unavailable because actual "
                "employee exit records are not currently stored."
            ),
        },
    }
