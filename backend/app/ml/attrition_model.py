from pathlib import Path
from typing import Any
from datetime import datetime, timezone
import logging

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = MODEL_DIR / "attrition_pipeline.joblib"

TARGET_COLUMN = "Attrition"

NUMERIC_FEATURES = [
    "Age",
    "MonthlyIncome",
    "JobSatisfaction",
    "WorkLifeBalance",
    "YearsAtCompany",
    "YearsInCurrentRole",
    "YearsSinceLastPromotion",
    "OverTime",
]

CATEGORICAL_FEATURES = [
    "BusinessTravel",
    "Department",
    "JobRole",
    "MaritalStatus",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

DISCLAIMER = (
    "This prediction is an estimate based on a sample HR analytics dataset. "
    "It is not a certainty or a substitute for human judgment. "
    "Do not use this score alone to make employment decisions."
)

MODEL_TYPE = "Logistic Regression"
MODEL_VERSION = 1

NUMERIC_RANGES = {
    "Age": (18, 100),
    "MonthlyIncome": (0, None),
    "JobSatisfaction": (1, 4),
    "WorkLifeBalance": (1, 4),
    "YearsAtCompany": (0, 80),
    "YearsInCurrentRole": (0, 80),
    "YearsSinceLastPromotion": (0, 80),
}


class AttritionModelError(Exception):
    """Raised when attrition model training or prediction fails."""


def _normalize_overtime(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()

    if "OverTime" not in result.columns:
        raise AttritionModelError(
            "The dataset or request is missing OverTime."
        )

    overtime = (
        result["OverTime"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    normalized = overtime.map({
        "yes": 1,
        "no": 0,
        "1": 1,
        "0": 0,
        "1.0": 1,
        "0.0": 0,
    })

    if normalized.isna().any():
        raise AttritionModelError(
            "OverTime must contain Yes/No or 1/0 values."
        )

    result["OverTime"] = normalized.astype(int)
    return result


def _prepare_features(
    data: pd.DataFrame,
    *,
    training: bool = False,
) -> pd.DataFrame:
    if data.empty:
        raise AttritionModelError(
            "No employee records were provided."
        )

    missing_columns = [
        column for column in FEATURES
        if column not in data.columns
    ]

    if missing_columns:
        raise AttritionModelError(
            "Missing required feature columns: "
            + ", ".join(missing_columns)
        )

    prepared = data[FEATURES].copy()
    prepared = _normalize_overtime(prepared)

    for column in NUMERIC_FEATURES:
        original = prepared[column]
        converted = pd.to_numeric(original, errors="coerce")

        if (original.notna() & converted.isna()).any():
            raise AttritionModelError(
                f"{column} must contain valid numeric values."
            )

        finite_values = converted.dropna()

        if not np.isfinite(finite_values.to_numpy(dtype=float)).all():
            raise AttritionModelError(
                f"{column} must contain finite numeric values."
            )

        bounds = NUMERIC_RANGES.get(column)

        if bounds is not None:
            minimum, maximum = bounds

            if minimum is not None and (converted.dropna() < minimum).any():
                raise AttritionModelError(
                    f"{column} must be at least {minimum}."
                )

            if maximum is not None and (converted.dropna() > maximum).any():
                raise AttritionModelError(
                    f"{column} must not exceed {maximum}."
                )

        if not training and converted.isna().any():
            raise AttritionModelError(
                f"{column} is required for attrition prediction."
            )

        prepared[column] = converted

    for column in CATEGORICAL_FEATURES:
        prepared[column] = (
            prepared[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

        if not training and prepared[column].isna().any():
            raise AttritionModelError(
                f"{column} is required for attrition prediction."
            )

    for _, row in prepared.iterrows():
        if (
            pd.notna(row["YearsInCurrentRole"])
            and pd.notna(row["YearsAtCompany"])
            and row["YearsInCurrentRole"] > row["YearsAtCompany"]
        ):
            raise AttritionModelError(
                "YearsInCurrentRole cannot exceed YearsAtCompany."
            )

        if (
            pd.notna(row["YearsSinceLastPromotion"])
            and pd.notna(row["YearsAtCompany"])
            and row["YearsSinceLastPromotion"] > row["YearsAtCompany"]
        ):
            raise AttritionModelError(
                "YearsSinceLastPromotion cannot exceed YearsAtCompany."
            )

    return prepared


def _build_pipeline() -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def _normalize_target(target: pd.Series) -> pd.Series:
    normalized = (
        target.astype("string")
        .str.strip()
        .str.lower()
        .map({
            "yes": 1,
            "no": 0,
            "1": 1,
            "0": 0,
            "1.0": 1,
            "0.0": 0,
            "true": 1,
            "false": 0,
        })
    )

    if normalized.isna().any():
        raise AttritionModelError(
            "Attrition must contain only Yes/No or 1/0 labels."
        )

    if normalized.nunique() != 2:
        raise AttritionModelError(
            "The dataset must contain both attrition classes: Yes and No."
        )

    return normalized.astype(int)


def _load_model_artifact() -> dict[str, Any]:
    if not MODEL_PATH.is_file():
        raise AttritionModelError(
            "The attrition model has not been trained yet. "
            "An administrator must train the model first."
        )

    try:
        artifact = joblib.load(MODEL_PATH)
    except Exception as exc:
        logger.exception("Unable to load the attrition model artifact.")
        raise AttritionModelError(
            "The saved attrition model could not be loaded. "
            "Train the model again."
        ) from exc

    if not isinstance(artifact, dict):
        raise AttritionModelError(
            "The saved model artifact has an invalid format."
        )

    if not isinstance(artifact.get("pipeline"), Pipeline):
        raise AttritionModelError(
            "The saved model pipeline is invalid. Train the model again."
        )

    pipeline = artifact["pipeline"]

    if set(pipeline.named_steps.keys()) != {"preprocessor", "classifier"}:
        raise AttritionModelError(
            "The saved model pipeline structure is invalid. "
            "Train the model again."
        )

    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    if not isinstance(preprocessor, ColumnTransformer):
        raise AttritionModelError(
            "The saved model preprocessor is invalid. "
            "Train the model again."
        )

    transformer_map = {
        name: list(columns)
        for name, _, columns in preprocessor.transformers
        if name in {"numeric", "categorical"}
    }

    if (
        transformer_map.get("numeric") != NUMERIC_FEATURES
        or transformer_map.get("categorical") != CATEGORICAL_FEATURES
        or preprocessor.remainder != "drop"
    ):
        raise AttritionModelError(
            "The saved model preprocessor feature configuration is invalid. "
            "Train the model again."
        )

    if not hasattr(preprocessor, "feature_names_in_"):
        raise AttritionModelError(
            "The saved model preprocessor is not fitted. "
            "Train the model again."
        )

    if list(preprocessor.feature_names_in_) != FEATURES:
        raise AttritionModelError(
            "The saved model preprocessor input features do not match. "
            "Train the model again."
        )

    if not isinstance(classifier, LogisticRegression):
        raise AttritionModelError(
            "The saved model classifier is invalid. "
            "Train the model again."
        )

    if not hasattr(pipeline, "n_features_in_"):
        raise AttritionModelError(
            "The saved model pipeline is not fitted. "
            "Train the model again."
        )

    if pipeline.n_features_in_ != len(FEATURES):
        raise AttritionModelError(
            "The saved model input feature count is invalid. "
            "Train the model again."
        )

    if not hasattr(classifier, "classes_") or set(classifier.classes_) != {0, 1}:
        raise AttritionModelError(
            "The saved model classifier classes are invalid. "
            "Train the model again."
        )

    if artifact.get("model_type") != MODEL_TYPE:
        raise AttritionModelError(
            "The saved model type is unsupported. Train the model again."
        )

    if artifact.get("model_version") != MODEL_VERSION:
        raise AttritionModelError(
            "The saved model version is outdated or unsupported. "
            "Train the model again."
        )

    if artifact.get("features") != FEATURES:
        raise AttritionModelError(
            "The saved model feature configuration is outdated. "
            "Train the model again."
        )

    for key in ("dataset_rows", "training_rows", "testing_rows"):
        value = artifact.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise AttritionModelError(
                f"The saved model metadata '{key}' is invalid. "
                "Train the model again."
            )

    if artifact["dataset_rows"] != (
        artifact["training_rows"] + artifact["testing_rows"]
    ):
        raise AttritionModelError(
            "The saved model dataset row counts are inconsistent. "
            "Train the model again."
        )

    trained_at = artifact.get("trained_at")
    if not isinstance(trained_at, str) or not trained_at.strip():
        raise AttritionModelError(
            "The saved model training timestamp is invalid. "
            "Train the model again."
        )

    try:
        timestamp = datetime.fromisoformat(trained_at)
    except ValueError as exc:
        raise AttritionModelError(
            "The saved model training timestamp is invalid. "
            "Train the model again."
        ) from exc

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise AttritionModelError(
            "The saved model training timestamp must include a timezone. "
            "Train the model again."
        )

    for key in ("accuracy", "precision", "recall", "f1_score"):
        value = artifact.get(key)

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not np.isfinite(value)
            or not 0 <= value <= 1
        ):
            raise AttritionModelError(
                f"The saved model metric '{key}' is invalid. "
                "Train the model again."
            )

    roc_auc = artifact.get("roc_auc")

    if roc_auc is not None and (
        isinstance(roc_auc, bool)
        or not isinstance(roc_auc, (int, float))
        or not np.isfinite(roc_auc)
        or not 0 <= roc_auc <= 1
    ):
        raise AttritionModelError(
            "The saved model metric 'roc_auc' is invalid. "
            "Train the model again."
        )

    return artifact


def train_model(dataset_path: Path) -> dict[str, Any]:
    dataset_path = Path(dataset_path)

    if not dataset_path.is_file():
        raise AttritionModelError(
            f"Dataset file was not found: {dataset_path}"
        )

    try:
        dataset = pd.read_csv(dataset_path)
    except Exception as exc:
        logger.exception("Unable to read the attrition dataset.")
        raise AttritionModelError(
            "The attrition dataset could not be read as a CSV file."
        ) from exc

    if dataset.empty:
        raise AttritionModelError(
            "The attrition dataset contains no records."
        )

    if TARGET_COLUMN not in dataset.columns:
        raise AttritionModelError(
            f"The dataset must contain a '{TARGET_COLUMN}' column."
        )

    if len(dataset) < 20:
        raise AttritionModelError(
            "At least 20 records are required to train the model."
        )

    missing_features = [
        column for column in FEATURES
        if column not in dataset.columns
    ]

    if missing_features:
        raise AttritionModelError(
            "Dataset is missing required feature columns: "
            + ", ".join(missing_features)
        )

    # Remove completely duplicated records before splitting the dataset.
    # This reduces the risk of identical records appearing in both sets.
    dataset = dataset.drop_duplicates().reset_index(drop=True)

    if len(dataset) < 20:
        raise AttritionModelError(
            "At least 20 unique records are required to train the model."
        )

    features = _prepare_features(dataset, training=True)
    target = _normalize_target(dataset[TARGET_COLUMN])

    if len(features) != len(target):
        raise AttritionModelError(
            "Feature and target record counts do not match."
        )

    if target.value_counts().min() < 2:
        raise AttritionModelError(
            "Each attrition class must contain at least two records."
        )

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=42,
            stratify=target,
        )

        pipeline = _build_pipeline()
        pipeline.fit(X_train, y_train)

        predictions = pipeline.predict(X_test)
        probabilities = pipeline.predict_proba(X_test)[:, 1]

        accuracy = float(accuracy_score(y_test, predictions))
        precision = float(
            precision_score(y_test, predictions, zero_division=0)
        )
        recall = float(
            recall_score(y_test, predictions, zero_division=0)
        )
        f1 = float(
            f1_score(y_test, predictions, zero_division=0)
        )

        try:
            roc_auc = float(roc_auc_score(y_test, probabilities))
        except ValueError:
            roc_auc = None

        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        trained_at = datetime.now(timezone.utc).isoformat()

        artifact = {
            "pipeline": pipeline,
            "features": FEATURES.copy(),
            "model_type": MODEL_TYPE,
            "model_version": MODEL_VERSION,
            "dataset_rows": int(len(features)),
            "training_rows": int(len(X_train)),
            "testing_rows": int(len(X_test)),
            "trained_at": trained_at,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "roc_auc": roc_auc,
        }

        # Save to a temporary file first so a failed write does not
        # overwrite the existing trained model artifact.
        temporary_model_path = MODEL_PATH.with_name(
            MODEL_PATH.name + ".tmp"
        )

        try:
            joblib.dump(artifact, temporary_model_path)
            temporary_model_path.replace(MODEL_PATH)
        finally:
            if temporary_model_path.exists():
                temporary_model_path.unlink()

        logger.info(
            "Attrition model training completed. "
            "Dataset rows=%s, training rows=%s, testing rows=%s, "
            "trained_at=%s, accuracy=%.4f, precision=%.4f, "
            "recall=%.4f, f1_score=%.4f, roc_auc=%s",
            len(features),
            len(X_train),
            len(X_test),
            trained_at,
            accuracy,
            precision,
            recall,
            f1,
            f"{roc_auc:.4f}" if roc_auc is not None else "N/A",
        )

        return {
            "status": "success",
            "model_type": MODEL_TYPE,
            "dataset_rows": int(len(features)),
            "training_rows": int(len(X_train)),
            "testing_rows": int(len(X_test)),
            "trained_at": trained_at,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
            "model_path": str(MODEL_PATH.resolve()),
            "features": FEATURES.copy(),
        }

    except AttritionModelError:
        raise
    except Exception as exc:
        logger.exception("Attrition model training failed.")
        raise AttritionModelError(
            "Model training failed. Check the dataset format and values."
        ) from exc


def predict_attrition(data: dict[str, Any]) -> dict[str, Any]:
    try:
        features = _prepare_features(
            pd.DataFrame([data]),
            training=False,
        )

        artifact = _load_model_artifact()
        pipeline = artifact["pipeline"]

        probabilities = np.asarray(
            pipeline.predict_proba(features),
            dtype=float,
        )
        classes = list(pipeline.named_steps["classifier"].classes_)

        if (
            probabilities.ndim != 2
            or probabilities.shape[0] != len(features)
            or probabilities.shape[1] != len(classes)
            or not np.isfinite(probabilities).all()
            or (probabilities < 0).any()
            or (probabilities > 1).any()
            or not np.allclose(probabilities.sum(axis=1), 1.0)
        ):
            raise AttritionModelError(
                "The model returned invalid class probabilities."
            )

        if 1 not in classes:
            raise AttritionModelError(
                "The trained model does not contain the attrition class."
            )

        probability = float(probabilities[0][classes.index(1)])

        if not np.isfinite(probability):
            raise AttritionModelError(
                "The model returned an invalid attrition probability."
            )

        probability = round(min(max(probability, 0.0), 1.0), 6)
        percentage = round(probability * 100, 2)

        if percentage < 40:
            risk_level = "LOW"
        elif percentage < 70:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "attrition_probability": probability,
            "attrition_risk_percentage": percentage,
            "risk_level": risk_level,
            "model_type": artifact.get("model_type", MODEL_TYPE),
            "disclaimer": DISCLAIMER,
        }

    except AttritionModelError:
        raise
    except Exception as exc:
        logger.exception("Attrition prediction failed.")
        raise AttritionModelError(
            "Attrition prediction failed. Check the model and input data."
        ) from exc
