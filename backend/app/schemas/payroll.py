from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class PayrollGenerateRequest(BaseModel):
    employee_id: int
    month: str  # 'YYYY-MM'
    allowances: Decimal = Decimal("0.00")
    bonus: Decimal = Decimal("0.00")
    deductions: Decimal = Decimal("0.00")
    notes: str | None = None


class PayrollStatusUpdate(BaseModel):
    status: str  # PROCESSED, PAID
    payment_method: str | None = "Direct Deposit"
    payment_date: date | None = None


class PayrollResponse(BaseModel):
    id: int
    employee_id: int
    month: str
    basic_salary: Decimal
    allowances: Decimal
    bonus: Decimal
    deductions: Decimal
    tax: Decimal
    net_salary: Decimal
    status: str
    payment_date: date | None = None
    payment_method: str | None = None
    notes: str | None = None
    created_at: datetime
    employee_name: str | None = None
    employee_code: str | None = None
    department_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
