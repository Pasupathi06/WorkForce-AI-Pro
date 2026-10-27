from math import isfinite
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class AttritionPredictionRequest(BaseModel):
    Age: int = Field(ge=18, le=100)
    MonthlyIncome: float = Field(ge=0, le=100_000_000)
    JobSatisfaction: int = Field(ge=1, le=4)
    WorkLifeBalance: int = Field(ge=1, le=4)
    YearsAtCompany: int = Field(ge=0, le=80)
    YearsInCurrentRole: int = Field(ge=0, le=80)
    YearsSinceLastPromotion: int = Field(ge=0, le=80)
    OverTime: int = Field(ge=0, le=1)

    BusinessTravel: str = Field(min_length=1, max_length=50)
    Department: str = Field(min_length=1, max_length=100)
    JobRole: str = Field(min_length=1, max_length=100)
    MaritalStatus: str = Field(min_length=1, max_length=50)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "Age": 30,
                "MonthlyIncome": 5000,
                "JobSatisfaction": 3,
                "WorkLifeBalance": 3,
                "YearsAtCompany": 5,
                "YearsInCurrentRole": 3,
                "YearsSinceLastPromotion": 1,
                "OverTime": 1,
                "BusinessTravel": "Travel_Rarely",
                "Department": "Research & Development",
                "JobRole": "Research Scientist",
                "MaritalStatus": "Single",
            }
        },
    )

    @field_validator("Age", mode="before")
    @classmethod
    def validate_age_is_integer(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("Age must be a whole number.")

        if isinstance(value, float) and not value.is_integer():
            raise ValueError("Age must be a whole number.")

        return value

    @field_validator("MonthlyIncome", mode="before")
    @classmethod
    def validate_monthly_income_is_finite(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("MonthlyIncome must be a valid number.")

        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError("MonthlyIncome must be a valid number.")

        if not isfinite(number):
            raise ValueError("MonthlyIncome must be a finite number.")

        return number

    @field_validator(
        "JobSatisfaction",
        "WorkLifeBalance",
        "YearsAtCompany",
        "YearsInCurrentRole",
        "YearsSinceLastPromotion",
        "OverTime",
        mode="before",
    )
    @classmethod
    def validate_integer_fields(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("This field must be a whole number.")

        if isinstance(value, float) and not value.is_integer():
            raise ValueError("This field must be a whole number.")

        return value

    @field_validator(
        "BusinessTravel",
        "Department",
        "JobRole",
        "MaritalStatus",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        if not any(character.isalnum() for character in value):
            raise ValueError(
                "This field must contain at least one letter or number."
            )

        return value

    @model_validator(mode="after")
    def validate_year_relationships(self):
        if self.YearsInCurrentRole > self.YearsAtCompany:
            raise ValueError(
                "YearsInCurrentRole cannot exceed YearsAtCompany."
            )

        if self.YearsSinceLastPromotion > self.YearsAtCompany:
            raise ValueError(
                "YearsSinceLastPromotion cannot exceed YearsAtCompany."
            )

        return self


class AttritionPredictionResponse(BaseModel):
    attrition_probability: float = Field(ge=0, le=1)
    attrition_risk_percentage: float = Field(ge=0, le=100)
    risk_level: str = Field(pattern=r"^(LOW|MEDIUM|HIGH)$")
    model_type: str = Field(min_length=1)
    disclaimer: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_probability_consistency(self):
        expected_percentage = round(
            self.attrition_probability * 100,
            2,
        )

        if self.attrition_risk_percentage != expected_percentage:
            raise ValueError(
                "Risk percentage must match the attrition probability."
            )

        expected_level = (
            "LOW"
            if expected_percentage < 40
            else "MEDIUM"
            if expected_percentage < 70
            else "HIGH"
        )

        if self.risk_level != expected_level:
            raise ValueError(
                "Risk level does not match the risk percentage."
            )

        return self


class AttritionTrainingResponse(BaseModel):
    status: str = Field(pattern=r"^success$")
    model_type: str = Field(min_length=1)
    dataset_rows: int = Field(ge=20, strict=True)
    training_rows: int = Field(ge=1, strict=True)
    testing_rows: int = Field(ge=1, strict=True)
    trained_at: str = Field(min_length=1)
    accuracy: float = Field(ge=0, le=1)
    precision: float = Field(ge=0, le=1)
    recall: float = Field(ge=0, le=1)
    f1_score: float = Field(ge=0, le=1)
    roc_auc: float | None = Field(default=None, ge=0, le=1)
    model_path: str = Field(min_length=1)
    features: list[str] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator("trained_at")
    @classmethod
    def validate_trained_at_timezone(cls, value: str) -> str:
        from datetime import datetime

        try:
            timestamp = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                "trained_at must be a valid ISO 8601 timestamp."
            ) from exc

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError(
                "trained_at must include a timezone."
            )

        return value

    @model_validator(mode="after")
    def validate_training_rows(self):
        if self.dataset_rows != self.training_rows + self.testing_rows:
            raise ValueError(
                "Dataset rows must equal training rows plus testing rows."
            )

        if any(
            not isinstance(feature, str) or not feature.strip()
            for feature in self.features
        ):
            raise ValueError(
                "Feature names must be non-empty strings."
            )

        normalized_features = [
            feature.strip() for feature in self.features
        ]

        if len(normalized_features) != len(set(normalized_features)):
            raise ValueError(
                "Feature names must not contain duplicates."
            )

        return self


class AttritionPredictionWithEmployeeRequest(AttritionPredictionRequest):
    employee_id: int | None = Field(default=None, gt=0)
