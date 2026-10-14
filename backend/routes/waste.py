from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from firebase_client import get_firestore

router = APIRouter()

COLLECTION = "waste_records"


class Waste(BaseModel):
    date: str
    food_item: str
    quantity: float
    cost_per_unit: float
    reason: str


@router.post("/waste")
def add_waste(w: Waste):
    db = get_firestore()

    item = w.model_dump()
    item["cost"] = item["quantity"] * item["cost_per_unit"]
    item["created_at"] = datetime.now(timezone.utc).isoformat()

    # Create a new document without overwriting existing records.
    document = db.collection(COLLECTION).document()
    item["id"] = document.id
    document.set(item)

    return item


@router.get("/waste")
def get_waste():
    db = get_firestore()

    documents = db.collection(COLLECTION).stream()
    records = [doc.to_dict() for doc in documents]

    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return records
