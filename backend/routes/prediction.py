from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from ml.model import demand_prediction, waste_prediction, train, get_feature_importance, get_model_metrics
from services.storage import load, add

router = APIRouter()

class PredictionInput(BaseModel):
    date:str
    expected_attendance:float
    food_item:str = "Rice"
    holiday:int = 0
    event:int = 0
    exam:int = 0
    temperature:float = 30
    rain_probability:float = 0
    previous_consumption:float = 700
    food_prepared:float = 750

@router.post("/predict")
def predict(p:PredictionInput):
    d = p.model_dump()
    d["day_of_week"] = datetime.fromisoformat(p.date).weekday()
    result = demand_prediction(d)
    result["food_item"] = p.food_item
    result["date"] = p.date
    add("predictions", result)
    return result

@router.get("/predictions")
def predictions():
    return load()["predictions"]

@router.get("/model-metrics")
def model_metrics():
    return get_model_metrics()

@router.get("/feature-importance")
def feature_importance():
    return get_feature_importance()

@router.post("/waste-risk")
def waste_risk(p:PredictionInput):
    d = p.model_dump()
    d["day_of_week"] = datetime.fromisoformat(p.date).weekday()
    return waste_prediction(d)

@router.get("/prediction-performance")
def performance():
    db = load()
    records = db["daily_records"]
    if not records:
        return {"count":0,"mae":0,"mape":0}
    errors = []
    apes = []
    for r in records:
        pred = float(r.get("predicted_demand", r.get("food_consumed",0)))
        actual = float(r.get("food_consumed",0))
        errors.append(abs(pred-actual))
        if actual:
            apes.append(abs(pred-actual)/actual*100)
    return {
        "count":len(records),
        "mae":round(sum(errors)/len(errors),2),
        "mape":round(sum(apes)/len(apes),2) if apes else 0
    }

@router.post("/retrain")
def retrain():
    return train()
