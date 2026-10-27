from pathlib import Path
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import AdminUser, HRUser
from app.db.database import get_db
from app.ml.attrition_model import (
    AttritionModelError,
    predict_attrition,
    train_model,
)
from app.models.attrition_history import AttritionHistory
from app.models.employee import Employee
from app.schemas.attrition import (
    AttritionPredictionWithEmployeeRequest,
    AttritionPredictionResponse,
    AttritionTrainingResponse,
)
from app.schemas.attrition_history import AttritionHistoryListResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/attrition",
    tags=["AI Attrition Prediction"],
)

BACKEND_DIR = Path(__file__).resolve().parents[3]
DATASET_PATH = BACKEND_DIR / "dataset" / "attrition.csv"

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/predict",
    response_model=AttritionPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict employee attrition risk",
)
def predict_employee_attrition(
    payload: AttritionPredictionWithEmployeeRequest,
    current_user: HRUser,
    db: DatabaseSession,
) -> AttritionPredictionResponse:
    """Predict attrition and persist its result for ADMIN/HR."""

    if payload.employee_id is not None:
        employee = db.query(Employee).filter(
            Employee.id == payload.employee_id
        ).first()

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found.",
            )

    model_features = payload.model_dump(exclude={"employee_id"})

    try:
        result = predict_attrition(model_features)
        prediction = AttritionPredictionResponse.model_validate(result)

        history = AttritionHistory(
            employee_id=payload.employee_id,
            predicted_by_user_id=current_user.id,
            attrition_probability=prediction.attrition_probability,
            attrition_risk_percentage=prediction.attrition_risk_percentage,
            risk_level=prediction.risk_level,
            model_type=prediction.model_type,
        )

        db.add(history)
        db.commit()

        return prediction

    except AttritionModelError as exc:
        db.rollback()
        message = str(exc)
        logger.warning("Attrition prediction failed: %s", message)

        if "has not been trained yet" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "The attrition model has not been trained yet. "
                    "An administrator must train the model first."
                ),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected attrition prediction error.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate or save the attrition prediction.",
        ) from exc


@router.get(
    "/history",
    response_model=AttritionHistoryListResponse,
    summary="List attrition prediction history",
)
def get_attrition_history(
    current_user: HRUser,
    db: DatabaseSession,
    employee_id: Annotated[int | None, Query(gt=0)] = None,
    risk_level: Annotated[
        str | None,
        Query(pattern=r"^(LOW|MEDIUM|HIGH)$"),
    ] = None,
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
    model_type: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AttritionHistoryListResponse:
    """Return paginated prediction history with optional filters."""

    from datetime import date, datetime, time, timedelta, timezone

    query = db.query(AttritionHistory).options(
        joinedload(AttritionHistory.predicted_by)
    )

    if employee_id is not None:
        query = query.filter(AttritionHistory.employee_id == employee_id)

    if risk_level is not None:
        query = query.filter(AttritionHistory.risk_level == risk_level)

    if model_type is not None:
        normalized_model_type = model_type.strip()

        if not normalized_model_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="model_type cannot be empty.",
            )

        query = query.filter(
            AttritionHistory.model_type == normalized_model_type
        )

    parsed_start_date = None
    parsed_end_date = None

    try:
        if start_date:
            parsed_start_date = date.fromisoformat(start_date)

        if end_date:
            parsed_end_date = date.fromisoformat(end_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dates must use YYYY-MM-DD format.",
        ) from exc

    if (
        parsed_start_date is not None
        and parsed_end_date is not None
        and parsed_start_date > parsed_end_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be on or before end_date.",
        )

    if parsed_start_date is not None:
        start_datetime = datetime.combine(
            parsed_start_date,
            time.min,
            tzinfo=timezone.utc,
        )
        query = query.filter(
            AttritionHistory.created_at >= start_datetime
        )

    if parsed_end_date is not None:
        end_exclusive = datetime.combine(
            parsed_end_date + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )
        query = query.filter(
            AttritionHistory.created_at < end_exclusive
        )

    total = query.count()

    items = (
        query.order_by(
            AttritionHistory.created_at.desc(),
            AttritionHistory.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    response_items = [
        {
            "id": item.id,
            "employee_id": item.employee_id,
            "predicted_by_user_id": item.predicted_by_user_id,
            "predicted_by_name": (
                item.predicted_by.full_name if item.predicted_by else None
            ),
            "attrition_probability": item.attrition_probability,
            "attrition_risk_percentage": item.attrition_risk_percentage,
            "risk_level": item.risk_level,
            "model_type": item.model_type,
            "created_at": item.created_at,
        }
        for item in items
    ]

    return AttritionHistoryListResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
    )

@router.post(
    "/train",
    response_model=AttritionTrainingResponse,
    status_code=status.HTTP_200_OK,
    summary="Train the attrition prediction model",
)
def train_attrition_model(
    current_user: AdminUser,
) -> AttritionTrainingResponse:
    """Train the attrition model. Accessible to ADMIN only."""

    if not DATASET_PATH.is_file():
        logger.error("Attrition dataset not found: %s", DATASET_PATH)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Training dataset was not found. "
                "Expected location: backend/dataset/attrition.csv"
            ),
        )

    try:
        result = train_model(DATASET_PATH)
        return AttritionTrainingResponse.model_validate(result)

    except AttritionModelError as exc:
        logger.warning("Attrition model training failed: %s", str(exc))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Unexpected attrition training error.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to train the attrition prediction model.",
        ) from exc
