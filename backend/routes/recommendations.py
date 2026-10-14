
from fastapi import APIRouter
from firebase_client import get_firestore

router = APIRouter()


def to_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


@router.get("/recommendations")
def recommendations():
    db = get_firestore()

    # Read inventory directly from Firebase
    documents = db.collection("inventory").stream()
    inventory = [doc.to_dict() or {} for doc in documents]

    rec = []

    for item in inventory:
        ingredient = item.get("ingredient", "Unknown ingredient")
        required = to_number(item.get("required"))
        available = to_number(item.get("available"))
        unit = item.get("unit", "kg")

        if required > available:
            shortage = round(required - available, 2)
            rec.append(
                f"Purchase {shortage} {unit} of {ingredient}."
            )

    if not rec:
        rec.append(
            "Inventory is currently sufficient based on stored requirements."
        )

    return {"recommendations": rec}
