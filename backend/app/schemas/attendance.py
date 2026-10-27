from datetime import date, datetime, time
from pydantic import BaseModel, ConfigDict


class ShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    is_active: bool = True


class ShiftCreate(ShiftBase):
    pass


class ShiftResponse(ShiftBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CheckInRequest(BaseModel):
    employee_id: int
    shift_id: int | None = None
    notes: str | None = None


class CheckOutRequest(BaseModel):
    employee_id: int
    notes: str | None = None


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    shift_id: int | None = None
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    working_hours: float = 0.0
    overtime_hours: float = 0.0
    status: str
    notes: str | None = None
    created_at: datetime
    employee_name: str | None = None
    shift_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
