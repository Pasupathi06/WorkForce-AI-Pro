from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=2, max_length=30)
    user_id: int = Field(gt=0)
    department_id: int | None = Field(default=None, gt=0)
    designation: str = Field(min_length=2, max_length=100)
    joining_date: date
    salary: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("employee_code", "designation")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("This field must contain at least 2 characters.")
        return value

    @field_validator("joining_date")
    @classmethod
    def validate_joining_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Joining date cannot be in the future.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if not value:
            return None

        if not all(c.isdigit() or c in "+-() " for c in value):
            raise ValueError(
                "Phone number can contain digits, spaces, +, -, and parentheses only."
            )

        if not any(c.isdigit() for c in value):
            raise ValueError("Phone number must contain at least one digit.")

        return value


class EmployeeUpdate(BaseModel):
    @field_validator("designation", "joining_date", "salary", mode="before")
    @classmethod
    def reject_null_for_required_fields(cls, value):
        if value is None:
            raise ValueError("This field cannot be null. Omit it if you do not want to update it.")
        return value

    department_id: int | None = Field(default=None, gt=0)
    designation: str | None = Field(default=None, min_length=2, max_length=100)
    joining_date: date | None = None
    salary: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("designation")
    @classmethod
    def validate_designation(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if len(value) < 2:
            raise ValueError("Designation must contain at least 2 characters.")

        return value

    @field_validator("joining_date")
    @classmethod
    def validate_joining_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Joining date cannot be in the future.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if not value:
            return None

        if not all(c.isdigit() or c in "+-() " for c in value):
            raise ValueError(
                "Phone number can contain digits, spaces, +, -, and parentheses only."
            )

        if not any(c.isdigit() for c in value):
            raise ValueError("Phone number must contain at least one digit.")

        return value


class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    user_id: int

    full_name: str = Field(
        validation_alias=AliasPath("user", "full_name")
    )
    email: EmailStr = Field(
        validation_alias=AliasPath("user", "email")
    )
    department_name: str | None = Field(
        default=None,
        validation_alias=AliasPath("department", "name"),
    )

    department_id: int | None
    designation: str
    joining_date: date
    salary: Decimal
    phone: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
