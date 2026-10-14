
from fastapi import APIRouter
from pydantic import BaseModel

from services.storage import add, load

router = APIRouter()


class Consumption(BaseModel):
    date: str
    food_item: str
    prepared: float
    consumed: float
    remaining: float
    wasted: float
    meal: str = "Lunch"


@router.post("/consumption")
def log(c: Consumption):
    return add("consumption_logs", c.model_dump())


@router.get("/consumption")
def get():
    return load()["consumption_logs"]
