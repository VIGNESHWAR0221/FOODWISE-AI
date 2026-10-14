from fastapi import APIRouter
from pydantic import BaseModel

from services.operations import get_menus as get_menu_catalog
from services.storage import add, get_history, load, get_dataset_summary


router = APIRouter()


class DailyRecord(BaseModel):
    date: str
    expected_attendance: float
    actual_attendance: float = 0
    food_item: str
    food_prepared: float
    food_consumed: float
    food_remaining: float = 0
    food_wasted: float
    holiday: int = 0
    event: int = 0
    exam: int = 0
    temperature: float = 30
    rain_probability: float = 0
    weather_condition: str = "Clear"


@router.post("/daily-record")
def create_record(r: DailyRecord):
    return add("daily_records", r.model_dump())


@router.get("/history")
def history():
    return get_history()


@router.get("/menus")
def menus():
    unique = []
    seen = set()

    for menu in get_menu_catalog():
        key = (
            menu.get("menu_id"),
            menu.get("menu_name"),
            menu.get("description"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(menu)

    return unique


@router.get("/dataset-summary")
def dataset_summary():
    return get_dataset_summary()