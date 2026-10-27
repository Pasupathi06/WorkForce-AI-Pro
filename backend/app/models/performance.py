from datetime import datetime

from sqlalchemy import (
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


class PerformanceReview(Base):
    """Performance appraisal, rating, and goal tracking."""

    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    review_period: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., 'Q3 2026', 'Annual 2026'
    rating: Mapped[float] = mapped_column(Float, nullable=False)  # 1.0 - 5.0
    goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_areas: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="COMPLETED", nullable=False
    )  # DRAFT, COMPLETED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    employee = relationship("Employee")
    reviewer = relationship("User")
