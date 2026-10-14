from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from firebase_client import get_firestore
from services.operations import get_menus as get_menu_catalog

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
    db = get_firestore()

    item = r.model_dump()
    item["created_at"] = datetime.now(timezone.utc).isoformat()

    document = db.collection("daily_records").document()
    item["id"] = document.id
    document.set(item)

    return item


@router.get("/history")
def history():
    db = get_firestore()
    documents = db.collection("food_history").stream()

    records = []

    for document in documents:
        source = document.to_dict() or {}

        records.append({
            "date": source.get("date"),
            "day": source.get("day_of_week"),
            "expected_attendance": source.get("expected_attendance"),
            "food_item": source.get("food_item"),
            "food_prepared": source.get("prepared_kg"),
            "food_consumed": source.get("consumed_kg"),
            "food_wasted": (
                (source.get("leftover_kg") or 0)
                + (source.get("plate_waste_kg") or 0)
            ),
            "holiday": source.get("is_holiday"),
            "event": source.get("event_flag"),
            "exam": None,
            "temperature": source.get("temperature_c"),
            "rain_probability": source.get("rain_mm"),
            "actual_attendance": source.get("actual_attendance"),
            "is_weekend": source.get("is_weekend"),
            "leftover_kg": source.get("leftover_kg"),
            "plate_waste_kg": source.get("plate_waste_kg"),
        })

    records.sort(key=lambda item: item.get("date") or "")
    return records


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
    db = get_firestore()

    collections = [
        "food_history",
        "weather_history",
        "events",
        "holidays",
    ]

    summary = {}

    for name in collections:
        documents = list(db.collection(name).stream())
        summary[name] = {"count": len(documents)}

        if name == "food_history":
            dates = [
                str(item.get("date"))
                for document in documents
                if (item := document.to_dict() or {}).get("date")
            ]

            summary[name]["min_date"] = min(dates) if dates else None
            summary[name]["max_date"] = max(dates) if dates else None

    return summary
