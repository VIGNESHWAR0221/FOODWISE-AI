from fastapi import APIRouter
from services.storage import get_history, load

router=APIRouter()

@router.get("/analytics")
def analytics():
    history = get_history()
    waste_records = load().get("waste_records", [])

    total_consumed = sum(float(row.get("food_consumed", 0) or 0) for row in history)
    total_wasted = sum(float(row.get("food_wasted", 0) or 0) for row in history)
    waste_cost = sum(float(record.get("cost", 0) or 0) for record in waste_records)

    waste_by_reason = {}
    for record in waste_records:
        reason = str(record.get("reason", "Other"))
        quantity = float(record.get("quantity", 0) or 0)
        waste_by_reason[reason] = waste_by_reason.get(reason, 0.0) + quantity

    return {
        "total_consumed": round(total_consumed, 2),
        "total_wasted": round(total_wasted, 2),
        "waste_cost": round(waste_cost, 2),
        "waste_by_reason": waste_by_reason,
        "records": len(history),
    }
