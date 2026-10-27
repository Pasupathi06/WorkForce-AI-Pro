from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AdminUser, HRUser
from app.db.database import get_db
from app.models.department import Department
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)


router = APIRouter()


DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department",
)
def create_department(
    department_data: DepartmentCreate,
    current_user: HRUser,
    db: DatabaseSession,
) -> DepartmentResponse:
    """
    Admin and HR users can create departments.
    """

    name = department_data.name.strip()

    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Department name must contain at least 2 characters.",
        )

    existing_department = (
        db.query(Department)
        .filter(Department.name.ilike(name))
        .first()
    )

    if existing_department:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A department with this name already exists.",
        )

    department = Department(
        name=name,
        description=department_data.description,
        is_active=True,
    )

    try:
        db.add(department)
        db.commit()
        db.refresh(department)

        return department

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A department with this name already exists.",
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.get(
    "/",
    response_model=list[DepartmentResponse],
    summary="List departments",
)
def list_departments(
    current_user: HRUser,
    db: DatabaseSession,
    include_inactive: bool = Query(default=False),
) -> list[DepartmentResponse]:
    """
    Admin and HR users can list departments.
    Inactive departments are excluded by default.
    """

    query = db.query(Department)

    if not include_inactive:
        query = query.filter(Department.is_active.is_(True))

    return query.order_by(Department.name.asc()).all()


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Get a department",
)
def get_department(
    department_id: int,
    current_user: HRUser,
    db: DatabaseSession,
) -> DepartmentResponse:
    """
    Retrieve a department by its ID.
    """

    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    return department


@router.patch(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update a department",
)
def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    current_user: HRUser,
    db: DatabaseSession,
) -> DepartmentResponse:
    """
    Admin and HR users can update department details.
    """

    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    changes = department_data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update.",
        )

    if "name" in changes:
        new_name = changes["name"]

        if new_name is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Department name cannot be null.",
            )

        new_name = new_name.strip()

        if len(new_name) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Department name must contain at least 2 characters.",
            )

        duplicate = (
            db.query(Department)
            .filter(
                Department.name.ilike(new_name),
                Department.id != department_id,
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A department with this name already exists.",
            )

        changes["name"] = new_name

    for field, value in changes.items():
        setattr(department, field, value)

    try:
        db.commit()
        db.refresh(department)

        return department

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The department update conflicts with existing data.",
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.patch(
    "/{department_id}/deactivate",
    response_model=DepartmentResponse,
    summary="Deactivate a department (Admin only)",
)
def deactivate_department(
    department_id: int,
    admin_user: AdminUser,
    db: DatabaseSession,
) -> DepartmentResponse:
    """
    Only administrators can deactivate departments.

    The record is retained instead of being permanently deleted.
    """

    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    department.is_active = False

    try:
        db.commit()
        db.refresh(department)

        return department

    except Exception:
        db.rollback()
        raise