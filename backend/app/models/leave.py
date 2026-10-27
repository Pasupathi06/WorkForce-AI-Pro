from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class LeaveRequest(Base):
    """Employee leave application and approval workflow."""

    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # CASUAL, SICK, ANNUAL, MATERNITY, UNPAID
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_count: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False, index=True
    )  # PENDING, APPROVED, REJECTED
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    employee = relationship("Employee")
    reviewed_by = relationship("User")


class LeaveBalance(Base):
    """Annual leave quota and consumption tracker."""

    __tablename__ = "leave_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, default=2026, nullable=False)
    casual_leave: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    sick_leave: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    annual_leave: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    used_casual: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_sick: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_annual: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    employee = relationship("Employee")
