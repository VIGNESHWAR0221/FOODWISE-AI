from fastapi import APIRouter
from pydantic import BaseModel
from services.storage import add, load

router=APIRouter()

class Waste(BaseModel):
    date:str
    food_item:str
    quantity:float
    cost_per_unit:float
    reason:str

@router.post("/waste")
def add_waste(w:Waste):
    d=w.model_dump()
    d["cost"]=d["quantity"]*d["cost_per_unit"]
    return add("waste_records",d)

@router.get("/waste")
def get_waste():
    return load()["waste_records"]
