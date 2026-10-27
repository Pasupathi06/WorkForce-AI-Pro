from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AdminUser, CurrentUser, HRUser
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse, UserRoleUpdate

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: DatabaseSession) -> User:
    email = str(user_data.email).strip().lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    try:
        new_user = User(
            full_name=user_data.full_name.strip(),
            email=email,
            hashed_password=hash_password(user_data.password),
            role=UserRole.EMPLOYEE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
    except Exception:
        db.rollback()
        raise


@router.post("/login", response_model=TokenResponse)
def login_user(credentials: UserLogin, db: DatabaseSession) -> TokenResponse:
    email = str(credentials.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated.")

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: CurrentUser) -> User:
    return current_user


@router.get("/users/available-for-employees", response_model=list[UserResponse])
def list_available_employee_users(
    current_user: HRUser,
    db: DatabaseSession,
) -> list[User]:
    employee_exists = exists().where(Employee.user_id == User.id)

    return (
        db.query(User)
        .filter(User.is_active.is_(True), ~employee_exists)
        .order_by(User.full_name.asc(), User.id.asc())
        .all()
    )


@router.get("/users", response_model=list[UserResponse])
def list_users(current_user: HRUser, db: DatabaseSession) -> list[User]:
    return db.query(User).order_by(User.id.asc()).all()


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    admin_user: AdminUser,
    db: DatabaseSession,
) -> User:
    target_user = db.query(User).filter(User.id == user_id).first()

    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if not target_user.is_active:
        raise HTTPException(status_code=409, detail="Cannot change the role of an inactive user.")

    if target_user.id == admin_user.id and role_data.role != UserRole.ADMIN:
        raise HTTPException(status_code=409, detail="Administrators cannot change their own role.")

    # Prevent downgrading the last active administrator.
    if target_user.role == UserRole.ADMIN and role_data.role != UserRole.ADMIN:
        active_admin_count = (
            db.query(User)
            .filter(
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
            )
            .count()
        )

        if active_admin_count <= 1:
            raise HTTPException(
                status_code=409,
                detail="Cannot downgrade the last active administrator. Promote another active user to Admin first.",
            )

    target_user.role = role_data.role

    try:
        db.commit()
        db.refresh(target_user)
        return target_user
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The role update conflicts with existing data.") from exc
