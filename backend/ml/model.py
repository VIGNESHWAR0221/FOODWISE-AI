from pathlib import Path
import math

import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from xgboost import XGBRegressor


BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "data" / "staging" / "food_history.csv"

MODEL_DIR = BASE / "backend" / "ml"

DEMAND_MODEL = MODEL_DIR / "demand_model.pkl"
WASTE_MODEL = MODEL_DIR / "waste_model.pkl"


FEATURES = [
    "day_of_week",
    "holiday",
    "event",
    "expected_attendance",
    "temperature",
    "rain_probability",
    "previous_consumption",
]


MODEL_ARTIFACTS = {
    "random_forest_demand": DEMAND_MODEL,
    "xgboost_waste": WASTE_MODEL,
    "linear_regression_baseline": MODEL_DIR / "linear_regression_model.pkl",
}


def _load_artifact(path):
    if not path.exists():
        return None

    try:
        return joblib.load(path)
    except Exception:
        return None


def get_model_metrics():
    details = []

    for name, path in MODEL_ARTIFACTS.items():
        artifact = _load_artifact(path)
        entry = {
            "name": name,
            "path": str(path),
            "exists": path.exists(),
            "type": type(artifact).__name__ if artifact is not None else None,
            "feature_count": getattr(artifact, "n_features_in_", None),
        }

        if artifact is not None and hasattr(artifact, "feature_importances_"):
            entry["feature_importances"] = [
                round(float(value), 6)
                for value in artifact.feature_importances_
            ]

        details.append(entry)

    return {
        "status": "ok" if any(item["exists"] for item in details) else "missing",
        "artifacts": details,
    }


def get_feature_importance():
    model = _load_artifact(DEMAND_MODEL)
    if model is None or not hasattr(model, "feature_importances_"):
        return {
            "status": "not_available",
            "model": "random_forest_demand",
            "feature_importances": [],
        }

    pairs = []
    for feature, importance in zip(FEATURES, model.feature_importances_):
        pairs.append({
            "feature": feature,
            "importance": round(float(importance), 6),
        })

    return {
        "status": "ok",
        "model": "random_forest_demand",
        "feature_importances": sorted(
            pairs,
            key=lambda item: item["importance"],
            reverse=True,
        ),
    }


def prepare(df):
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["day_of_week"] = df["date"].dt.dayofweek

    df["holiday"] = df["is_holiday"].astype(int)
    df["event"] = df["event_flag"].astype(int)

    df["expected_attendance"] = pd.to_numeric(
        df["expected_attendance"],
        errors="coerce"
    )

    df["temperature"] = pd.to_numeric(
        df["temperature_c"],
        errors="coerce"
    )

    df["rain_probability"] = pd.to_numeric(
        df["rain_mm"],
        errors="coerce"
    )

    df["food_consumed"] = pd.to_numeric(
        df["consumed_kg"],
        errors="coerce"
    )

    df["food_prepared"] = pd.to_numeric(
        df["prepared_kg"],
        errors="coerce"
    )

    df["food_wasted"] = (
        pd.to_numeric(df["leftover_kg"], errors="coerce").fillna(0)
        + pd.to_numeric(df["plate_waste_kg"], errors="coerce").fillna(0)
    )

    # Previous day's actual consumption.
    df["previous_consumption"] = (
        df["food_consumed"].shift(1)
    )

    # First row has no previous day.
    df["previous_consumption"] = (
        df["previous_consumption"]
        .fillna(df["food_consumed"].median())
    )

    df = df.dropna(
        subset=[
            "expected_attendance",
            "temperature",
            "rain_probability",
            "food_consumed",
            "food_prepared",
            "food_wasted",
        ]
    )

    return df


def train():
    df = prepare(pd.read_csv(DATA))

    if len(df) < 20:
        raise ValueError(
            f"Not enough training data. Found {len(df)} rows."
        )

    X = df[FEATURES]
    y = df["food_consumed"]

    split = max(
        10,
        int(len(df) * 0.8)
    )

    Xtr = X.iloc[:split]
    Xte = X.iloc[split:]

    ytr = y.iloc[:split]
    yte = y.iloc[split:]

    # --------------------------------
    # Random Forest Demand Model
    # --------------------------------

    rf = RandomForestRegressor(
        n_estimators=250,
        random_state=42,
        min_samples_leaf=2,
        n_jobs=-1,
    )

    rf.fit(Xtr, ytr)

    pred = rf.predict(Xte)

    mae = float(
        mean_absolute_error(yte, pred)
    )

    rmse = float(
        np.sqrt(
            mean_squared_error(yte, pred)
        )
    )

    joblib.dump(
        rf,
        DEMAND_MODEL
    )

    # --------------------------------
    # Linear Regression Baseline
    # --------------------------------

    base = LinearRegression()

    base.fit(
        Xtr,
        ytr
    )

    base_pred = base.predict(Xte)

    base_mae = float(
        mean_absolute_error(
            yte,
            base_pred
        )
    )

    # --------------------------------
    # XGBoost Waste Model
    # --------------------------------

    waste_features = FEATURES + [
        "food_prepared"
    ]

    Xw = df[waste_features]
    yw = df["food_wasted"]

    Xw_tr = Xw.iloc[:split]
    Xw_te = Xw.iloc[split:]

    yw_tr = yw.iloc[:split]
    yw_te = yw.iloc[split:]

    xgb = XGBRegressor(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
    )

    xgb.fit(
        Xw_tr,
        yw_tr
    )

    waste_pred = xgb.predict(
        Xw_te
    )

    waste_mae = float(
        mean_absolute_error(
            yw_te,
            waste_pred
        )
    )

    joblib.dump(
        xgb,
        WASTE_MODEL
    )

    return {
        "status": "trained",
        "demand_model": "Random Forest Regressor",
        "waste_model": "XGBoost Regressor",
        "baseline": "Linear Regression",
        "random_forest_mae": round(mae, 4),
        "random_forest_rmse": round(rmse, 4),
        "linear_regression_mae": round(base_mae, 4),
        "xgboost_waste_mae": round(waste_mae, 4),
        "training_rows": len(df),
    }


def ensure_models():
    if (
        not DEMAND_MODEL.exists()
        or not WASTE_MODEL.exists()
    ):
        return train()

    return {
        "status": "models_ready"
    }


def demand_prediction(payload):
    ensure_models()

    model = joblib.load(
        DEMAND_MODEL
    )

    row = pd.DataFrame([{
        "day_of_week": int(
            payload.get("day_of_week", 0)
        ),
        "holiday": int(
            payload.get("holiday", 0)
        ),
        "event": int(
            payload.get("event", 0)
        ),
        "expected_attendance": float(
            payload.get("expected_attendance", 0)
        ),
        "temperature": float(
            payload.get("temperature", 30)
        ),
        "rain_probability": float(
            payload.get("rain_probability", 0)
        ),
        "previous_consumption": float(
            payload.get("previous_consumption", 0)
        ),
    }])

    pred = max(
        0,
        float(model.predict(row)[0])
    )

    # Historical residuals are used to construct
    # a prediction range.
    df = prepare(
        pd.read_csv(DATA)
    )

    X = df[FEATURES]
    y = df["food_consumed"]

    historical_predictions = model.predict(X)

    residuals = np.abs(
        y - historical_predictions
    )

    margin = max(
        0.5,
        float(
            np.quantile(
                residuals,
                0.75
            )
        )
    )

    low = max(
        0,
        pred - margin
    )

    high = pred + margin

    buffer = max(
        0,
        margin * 0.35
    )

    recommended = math.ceil(
        pred + buffer
    )

    return {
        "predicted_demand": round(
            pred,
            2
        ),
        "range_low": round(
            low,
            2
        ),
        "range_high": round(
            high,
            2
        ),
        "recommended_preparation": recommended,
        "margin": round(
            margin,
            2
        ),
    }


def waste_prediction(payload):
    ensure_models()

    model = joblib.load(
        WASTE_MODEL
    )

    row = pd.DataFrame([{
        "day_of_week": int(
            payload.get("day_of_week", 0)
        ),
        "holiday": int(
            payload.get("holiday", 0)
        ),
        "event": int(
            payload.get("event", 0)
        ),
        "expected_attendance": float(
            payload.get("expected_attendance", 0)
        ),
        "temperature": float(
            payload.get("temperature", 30)
        ),
        "rain_probability": float(
            payload.get("rain_probability", 0)
        ),
        "previous_consumption": float(
            payload.get("previous_consumption", 0)
        ),
        "food_prepared": float(
            payload.get("food_prepared", 0)
        ),
    }])

    predicted_waste = max(
        0,
        float(
            model.predict(row)[0]
        )
    )

    risk = (
        "LOW"
        if predicted_waste < 20
        else (
            "MEDIUM"
            if predicted_waste < 50
            else "HIGH"
        )
    )

    return {
        "predicted_waste": round(
            predicted_waste,
            2
        ),
        "risk": risk,
    }