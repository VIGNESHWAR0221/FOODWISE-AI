from fastapi import APIRouter
from pydantic import BaseModel
from datetime import date
from ml.model import demand_prediction, waste_prediction

router=APIRouter()

class Simulation(BaseModel):
    expected_attendance:float
    temperature:float=30
    rain_probability:float=0
    holiday:int=0
    event:int=0
    exam:int=0
    previous_consumption:float=700
    food_prepared:float=750

@router.post("/simulate")
def simulate(s:Simulation):
    d=s.model_dump()
    d["day_of_week"]=date.today().weekday()
    demand=demand_prediction(d)
    d["food_prepared"]=demand["recommended_preparation"]
    waste=waste_prediction(d)
    return {"demand":demand,"waste":waste}
