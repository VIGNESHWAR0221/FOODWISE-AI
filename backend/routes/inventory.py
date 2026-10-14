
import csv
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from services.storage import load, save

router = APIRouter()

BASE = Path(__file__).resolve().parents[2]
INVENTORY_CSV = BASE / "data" / "operations" / "inventory.csv"


class InventoryUpdate(BaseModel):
    ingredient: str
    available: float
    required: float = 0
    unit: str = "kg"


def load_csv_inventory():
    """Read the ingredient inventory from the operations CSV."""
    if not INVENTORY_CSV.exists():
        return []

    with INVENTORY_CSV.open(
        newline="",
        encoding="utf-8-sig"
    ) as file:
        rows = csv.DictReader(file)

        return [
            {
                "ingredient": row["ingredient_name"].strip(),
                "available": float(row["available_quantity"] or 0),
                "required": 0,
                "unit": row["unit"].strip() or "kg",
            }
            for row in rows
        ]


def get_combined_inventory(db):
    """Combine CSV ingredients with saved inventory values."""
    saved_items = db.get("inventory", [])
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
            # Keep the saved stock values for matching ingredients.
            item = {**csv_item, **saved}
        else:
            item = csv_item

        combined.append(item)
        seen.add(key)

    # Preserve saved items that are not present in the CSV.
    for item in saved_items:
        name = item.get("ingredient", "").strip()
        key = name.casefold()

        if name and key not in seen:
            combined.append(item)
            seen.add(key)

    return combined


@router.get("/inventory")
def get_inventory():
    db = load()
    return get_combined_inventory(db)


@router.post("/inventory/update")
def update_inventory(x: InventoryUpdate):
    db = load()
    payload = x.model_dump()

    for item in db.setdefault("inventory", []):
        if item["ingredient"].strip().casefold() == x.ingredient.strip().casefold():
            item["available"] = x.available
            item["required"] = x.required
            item["unit"] = x.unit
            break
    else:
        db["inventory"].append(payload)

    save(db)

    return {
        "message": "Inventory updated",
        "inventory": get_combined_inventory(db),
    }
