
from fastapi import APIRouter
from firebase_client import get_firestore

router = APIRouter()


def to_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


@router.get("/analytics")
def analytics():
    db = get_firestore()

    # Read historical food records from Firebase
    history_docs = db.collection("food_history").stream()
    history = [doc.to_dict() or {} for doc in history_docs]

    # Read recorded waste entries from Firebase
    waste_docs = db.collection("waste_records").stream()
    waste_records = [doc.to_dict() or {} for doc in waste_docs]

    total_consumed = sum(
        to_number(row.get("consumed_kg"))
        for row in history
    )

    # Total food waste = leftover food + plate waste
    total_wasted = sum(
        to_number(row.get("leftover_kg"))
        + to_number(row.get("plate_waste_kg"))
        for row in history
    )

    waste_cost = sum(
        to_number(record.get("cost"))
        for record in waste_records
    )

    waste_by_reason = {}

    for record in waste_records:
        reason = str(record.get("reason") or "Other")
        quantity = to_number(record.get("quantity"))

        waste_by_reason[reason] = (
            waste_by_reason.get(reason, 0.0) + quantity
        )

    return {
        "total_consumed": round(total_consumed, 2),
        "total_wasted": round(total_wasted, 2),
        "waste_cost": round(waste_cost, 2),
        "waste_by_reason": {
            reason: round(quantity, 2)
            for reason, quantity in waste_by_reason.items()
        },
        "records": len(history),
    }
