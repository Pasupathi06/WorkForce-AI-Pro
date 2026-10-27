from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: str  # CASUAL, SICK, ANNUAL, MATERNITY, UNPAID
    start_date: date
    end_date: date
    days_count: float = 1.0
    reason: str


class LeaveStatusUpdate(BaseModel):
    status: str  # APPROVED, REJECTED
    rejection_reason: str | None = None


class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days_count: float
    reason: str
    status: str
    reviewed_by_id: int | None = None
    rejection_reason: str | None = None
    created_at: datetime
    employee_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    year: int
    casual_leave: int
    sick_leave: int
    annual_leave: int
    used_casual: int
    used_sick: int
    used_annual: int
    remaining_casual: int
    remaining_sick: int
    remaining_annual: int

    model_config = ConfigDict(from_attributes=True)
