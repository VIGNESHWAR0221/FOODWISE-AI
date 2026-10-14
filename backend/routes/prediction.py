from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone

from ml.model import (
    demand_prediction,
    waste_prediction,
    train,
    get_feature_importance,
    get_model_metrics,
)
from firebase_client import get_firestore

router = APIRouter()

COLLECTION = "predictions"


class PredictionInput(BaseModel):
    date: str
    expected_attendance: float
    food_item: str = "Rice"
    holiday: int = 0
    event: int = 0
    exam: int = 0
    temperature: float = 30
    rain_probability: float = 0
    previous_consumption: float = 700
    food_prepared: float = 750


@router.post("/predict")
def predict(p: PredictionInput):
    d = p.model_dump()
    d["day_of_week"] = datetime.fromisoformat(p.date).weekday()

    result = demand_prediction(d)
    result["food_item"] = p.food_item
    result["date"] = p.date
    result["created_at"] = datetime.now(timezone.utc).isoformat()

    # Save as a new Firestore document; preserve existing predictions.
    db = get_firestore()
    document = db.collection(COLLECTION).document()
    result["id"] = document.id
    document.set(result)

    return result


@router.get("/predictions")
def predictions():
    db = get_firestore()
    documents = db.collection(COLLECTION).stream()
    records = [doc.to_dict() for doc in documents]

    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )
    return records


@router.get("/model-metrics")
def model_metrics():
    return get_model_metrics()


@router.get("/feature-importance")
def feature_importance():
    return get_feature_importance()


@router.post("/waste-risk")
def waste_risk(p: PredictionInput):
    d = p.model_dump()
    d["day_of_week"] = datetime.fromisoformat(p.date).weekday()
    return waste_prediction(d)



@router.get("/prediction-performance")
def performance():
    db = get_firestore()

    # Load predictions and historical actual consumption from Firebase
    prediction_docs = db.collection("predictions").stream()
    history_docs = db.collection("food_history").stream()

    predictions_data = [
        doc.to_dict() or {} for doc in prediction_docs
    ]
    history_data = [
        doc.to_dict() or {} for doc in history_docs
    ]

    # Index actual consumption by date and food item.
    # Ignore ambiguous duplicate date/item combinations.
    actual_values = {}

    for row in history_data:
        date = str(row.get("date") or "")[:10]
        food_item = str(row.get("food_item") or "").strip().casefold()
        actual = row.get("consumed_kg")

        if not date or not food_item or actual is None:
            continue

        try:
            actual = float(actual)
        except (TypeError, ValueError):
            continue

        key = (date, food_item)
        actual_values.setdefault(key, []).append(actual)

    errors = []
    percentage_errors = []

    for prediction in predictions_data:
        date = str(prediction.get("date") or "")[:10]
        food_item = str(
            prediction.get("food_item") or ""
        ).strip().casefold()

        predicted = prediction.get("predicted_demand")
        key = (date, food_item)

        # Only evaluate predictions with one unambiguous actual value.
        actual_matches = actual_values.get(key, [])

        if not date or not food_item or predicted is None:
            continue

        if len(actual_matches) != 1:
            continue

        try:
            predicted = float(predicted)
            actual = actual_matches[0]
        except (TypeError, ValueError):
            continue

        error = abs(predicted - actual)
        errors.append(error)

        if actual != 0:
            percentage_errors.append(error / abs(actual) * 100)

    return {
        "count": len(errors),
        "mae": round(sum(errors) / len(errors), 2) if errors else None,
        "mape": (
            round(sum(percentage_errors) / len(percentage_errors), 2)
            if percentage_errors else None
        ),
        "message": (
            "Metrics use predictions matched to one historical actual value."
            if errors else
            "No unambiguous prediction/actual matches found. "
            "MAE and MAPE are unavailable until matching data exists."
        ),
    }



@router.post("/retrain")
def retrain():
    return train()