from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import HRUser
from app.db.database import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)


router = APIRouter()

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_employee_or_404(
    employee_id: int,
    db: Session,
) -> Employee:
    employee = (
        db.query(Employee)
        .options(
            joinedload(Employee.user),
            joinedload(Employee.department),
        )
        .filter(Employee.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        )

    return employee


def validate_department(
    department_id: int | None,
    db: Session,
) -> None:
    if department_id is None:
        return

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected department does not exist or is inactive.",
        )


def build_employee_query(
    db: Session,
    *,
    department_id: int | None,
    active_only: bool,
    search: str | None,
):
    """Build a reusable employee query with the requested filters."""

    query = db.query(Employee)

    if active_only:
        query = query.filter(Employee.is_active.is_(True))

    if department_id is not None:
        query = query.filter(Employee.department_id == department_id)

    if search:
        search_term = f"%{search.strip()}%"
        query = (
            query
            .join(User, Employee.user_id == User.id)
            .outerjoin(Department, Employee.department_id == Department.id)
            .filter(
                (Employee.employee_code.ilike(search_term))
                | (Employee.designation.ilike(search_term))
                | (User.full_name.ilike(search_term))
                | (User.email.ilike(search_term))
                | (Department.name.ilike(search_term))
                | (cast(Employee.user_id, String).ilike(search_term))
            )
        )

    return query


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an employee record",
)
def create_employee(
    employee_data: EmployeeCreate,
    current_user: HRUser,
    db: DatabaseSession,
) -> Employee:
    """
    Admin and HR users can create employee records.

    The linked user account must already exist and be active.
    """

    employee_code = employee_data.employee_code.strip()

    existing_employee = (
        db.query(Employee)
        .filter(Employee.employee_code == employee_code)
        .first()
    )

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This employee code already exists.",
        )

    linked_user = (
        db.query(User)
        .filter(User.id == employee_data.user_id)
        .first()
    )

    if linked_user is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The linked user account does not exist.",
        )

    if not linked_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot create an employee profile for an inactive user.",
        )

    existing_profile = (
        db.query(Employee)
        .filter(Employee.user_id == employee_data.user_id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already has an employee profile.",
        )

    validate_department(employee_data.department_id, db)

    employee = Employee(
        employee_code=employee_code,
        user_id=employee_data.user_id,
        department_id=employee_data.department_id,
        designation=employee_data.designation.strip(),
        joining_date=employee_data.joining_date,
        salary=employee_data.salary,
        phone=employee_data.phone,
        is_active=True,
    )

    try:
        db.add(employee)
        db.commit()
        db.refresh(employee)

        return employee

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Employee code or user account conflicts with an existing record."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.get(
    "/",
    response_model=list[EmployeeResponse],
    summary="List employee records",
)
def list_employees(
    current_user: HRUser,
    db: DatabaseSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    department_id: int | None = Query(default=None, gt=0),
    active_only: bool = Query(default=True),
    search: str | None = Query(default=None, min_length=1, max_length=100),
) -> list[Employee]:
    """
    Retrieve employees with pagination and optional filters.
    """

    query = build_employee_query(
        db,
        department_id=department_id,
        active_only=active_only,
        search=search,
    )

    offset = (page - 1) * page_size

    return (
        query.order_by(Employee.id.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


@router.get("/count", summary="Count employee records")
def count_employees(
    current_user: HRUser,
    db: DatabaseSession,
    department_id: int | None = Query(default=None, gt=0),
    active_only: bool = Query(default=True),
    search: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, int]:
    """Return the total number of employees matching the supplied filters."""

    query = build_employee_query(
        db,
        department_id=department_id,
        active_only=active_only,
        search=search,
    )

    return {"count": query.count()}

@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee details",
)
def get_employee(
    employee_id: int,
    current_user: HRUser,
    db: DatabaseSession,
) -> Employee:
    """
    Retrieve a single employee record.
    """

    return get_employee_or_404(employee_id, db)


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee details",
)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: HRUser,
    db: DatabaseSession,
) -> Employee:
    """
    Admin and HR users can update active employee records.
    """

    employee = get_employee_or_404(employee_id, db)

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update an inactive employee record.",
        )

    changes = employee_data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update.",
        )

    if "department_id" in changes:
        validate_department(changes["department_id"], db)

    if "designation" in changes and changes["designation"] is not None:
        changes["designation"] = changes["designation"].strip()

    if "phone" in changes and changes["phone"] is not None:
        changes["phone"] = changes["phone"].strip() or None

    for field, value in changes.items():
        setattr(employee, field, value)

    try:
        db.commit()
        db.refresh(employee)

        return employee

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The employee update conflicts with existing data.",
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.patch(
    "/{employee_id}/deactivate",
    response_model=EmployeeResponse,
    summary="Deactivate an employee",
)
def deactivate_employee(
    employee_id: int,
    current_user: HRUser,
    db: DatabaseSession,
) -> Employee:
    """
    Deactivate an employee without permanently deleting the record.
    """

    employee = get_employee_or_404(employee_id, db)

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This employee is already inactive.",
        )

    employee.is_active = False

    try:
        db.commit()
        db.refresh(employee)

        return employee

    except Exception:
        db.rollback()
        raise





