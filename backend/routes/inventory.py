
import csv
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from firebase_client import get_firestore

router = APIRouter()

BASE = Path(__file__).resolve().parents[2]
INVENTORY_CSV = BASE / "data" / "operations" / "inventory.csv"
COLLECTION = "inventory"


class InventoryUpdate(BaseModel):
    ingredient: str
    available: float
    required: float = 0
    unit: str = "kg"


def load_csv_inventory():
    """Read optional default ingredients from the operations CSV."""
    if not INVENTORY_CSV.exists():
        return []

    with INVENTORY_CSV.open(
        newline="",
        encoding="utf-8-sig",
    ) as file:
        rows = csv.DictReader(file)
        result = []

        for row in rows:
            name = (row.get("ingredient_name") or "").strip()
            if not name:
                continue

            try:
                available = float(row.get("available_quantity") or 0)
            except (ValueError, TypeError):
                available = 0

            result.append({
                "ingredient": name,
                "available": available,
                "required": 0,
                "unit": (row.get("unit") or "kg").strip() or "kg",
            })

        return result


def read_firestore_inventory():
    """Read inventory documents from Firestore."""
    db = get_firestore()
    documents = db.collection(COLLECTION).stream()

    items = []
    for document in documents:
        item = document.to_dict() or {}
        item["_document_id"] = document.id
        items.append(item)

    return items


def get_combined_inventory(saved_items):
    """Combine optional CSV defaults with Firestore inventory."""
    saved_by_name = {
        item["ingredient"].strip().casefold(): item
        for item in saved_items
        if item.get("ingredient")
    }

    combined = []
    seen = set()

    for csv_item in load_csv_inventory():
        key = csv_item["ingredient"].casefold()
        saved = saved_by_name.get(key)

        if saved:
            item = {**csv_item, **saved}
        else:
            item = csv_item

        item.pop("_document_id", None)
        combined.append(item)
        seen.add(key)

    for saved in saved_items:
        name = (saved.get("ingredient") or "").strip()
        key = name.casefold()

        if name and key not in seen:
            item = dict(saved)
            item.pop("_document_id", None)
            combined.append(item)
            seen.add(key)

    return combined


@router.get("/inventory")
def get_inventory():
    saved_items = read_firestore_inventory()
    return get_combined_inventory(saved_items)


@router.post("/inventory/update")
def update_inventory(x: InventoryUpdate):
    db = get_firestore()
    collection = db.collection(COLLECTION)

    target = x.ingredient.strip().casefold()
    if not target:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Ingredient name cannot be empty",
        )

    matching_doc = None

    for document in collection.stream():
        item = document.to_dict() or {}
        name = (item.get("ingredient") or "").strip().casefold()

        if name == target:
            matching_doc = document
            break

    payload = {
        "ingredient": x.ingredient.strip(),
        "available": x.available,
        "required": x.required,
        "unit": x.unit,
    }

    if matching_doc:
        matching_doc.reference.update(payload)
    else:
        collection.add(payload)

    saved_items = read_firestore_inventory()

    return {
        "message": "Inventory updated",
        "inventory": get_combined_inventory(saved_items),
    }
