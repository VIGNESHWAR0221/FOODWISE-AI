
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from firebase_client import get_firestore

router = APIRouter()

COLLECTION = "consumption_logs"


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
    db = get_firestore()

    item = c.model_dump()
    item["created_at"] = datetime.now(timezone.utc).isoformat()

    # Create a new document without overwriting migrated records.
    document = db.collection(COLLECTION).document()
    item["id"] = document.id
    document.set(item)

    return item


@router.get("/consumption")
def get():
    db = get_firestore()

    documents = db.collection(COLLECTION).stream()
    records = [doc.to_dict() for doc in documents]

    # Preserve a predictable newest-first order.
    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return records
