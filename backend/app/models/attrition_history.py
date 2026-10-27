from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class AttritionHistory(Base):
    """Store employee attrition prediction history."""

    __tablename__ = "attrition_history"

    __table_args__ = (
        CheckConstraint(
            "attrition_probability >= 0 AND attrition_probability <= 1",
            name="ck_attrition_history_probability_range",
        ),
        CheckConstraint(
            "attrition_risk_percentage >= 0 "
            "AND attrition_risk_percentage <= 100",
            name="ck_attrition_history_risk_percentage_range",
        ),
        CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH')",
            name="ck_attrition_history_risk_level",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    predicted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    attrition_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    attrition_risk_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    model_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    employee = relationship("Employee")
    predicted_by = relationship("User")
