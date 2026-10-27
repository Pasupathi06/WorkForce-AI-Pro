from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.employee import Employee
from app.models.performance import PerformanceReview
from app.schemas.performance import (
    PerformanceReviewCreate,
    PerformanceReviewResponse,
)

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[PerformanceReviewResponse], summary="List performance reviews")
def list_reviews(
    db: DatabaseSession,
    current_user: CurrentUser,
    employee_id: int | None = None,
    period: str | None = None,
    limit: int = Query(default=100, le=300),
):
    query = db.query(PerformanceReview)
    if employee_id:
        query = query.filter(PerformanceReview.employee_id == employee_id)
    if period:
        query = query.filter(PerformanceReview.review_period == period)

    reviews = query.order_by(PerformanceReview.created_at.desc()).limit(limit).all()

    result = []
    for r in reviews:
        item = PerformanceReviewResponse.model_validate(r)
        if r.employee and r.employee.user:
            item.employee_name = r.employee.user.full_name
        elif r.employee:
            item.employee_name = r.employee.employee_code
        if r.reviewer:
            item.reviewer_name = r.reviewer.full_name
        result.append(item)
    return result


@router.post(
    "/",
    response_model=PerformanceReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a performance review",
)
def create_review(
    data: PerformanceReviewCreate, db: DatabaseSession, current_user: HRUser
):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    review = PerformanceReview(
        employee_id=employee.id,
        reviewer_id=current_user.id,
        review_period=data.review_period,
        rating=data.rating,
        goals=data.goals,
        feedback=data.feedback,
        strengths=data.strengths,
        improvement_areas=data.improvement_areas,
        status=data.status,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    item = PerformanceReviewResponse.model_validate(review)
    item.employee_name = employee.user.full_name if employee.user else employee.employee_code
    item.reviewer_name = current_user.full_name
    return item


@router.get("/summary", summary="Get performance review metrics")
def get_performance_summary(db: DatabaseSession, current_user: CurrentUser):
    avg_rating = db.query(func.avg(PerformanceReview.rating)).scalar() or 0.0
    total_reviews = db.query(PerformanceReview).count()

    top_performers = (
        db.query(PerformanceReview)
        .filter(PerformanceReview.rating >= 4.5)
        .count()
    )
    needs_support = (
        db.query(PerformanceReview)
        .filter(PerformanceReview.rating < 3.0)
        .count()
    )

    return {
        "average_rating": round(float(avg_rating), 2),
        "total_reviews": total_reviews,
        "top_performers": top_performers,
        "needs_support": needs_support,
    }
