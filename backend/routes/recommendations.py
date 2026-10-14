from fastapi import APIRouter
from services.storage import load

router=APIRouter()

@router.get("/recommendations")
def recommendations():
    db=load()
    inv=db["inventory"]
    rec=[]
    for x in inv:
        req=float(x.get("required",0))
        avail=float(x.get("available",0))
        if req>avail:
            rec.append(f"Purchase {round(req-avail,2)} {x.get('unit','kg')} of {x['ingredient']}.")
    if not rec:
        rec.append("Inventory is currently sufficient based on stored requirements.")
    return {"recommendations":rec}
