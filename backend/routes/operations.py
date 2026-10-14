from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.operations import (
    get_ingredients,
    get_menus,
    get_recipes,
    get_inventory,
    get_prices,
)

from services.operations_planner import (
    calculate_plan,
    calculate_portions_from_demand,
)

from ml.model import demand_prediction


router = APIRouter()


@router.get("/operations/ingredients")
def ingredients():
    return get_ingredients()


@router.get("/operations/menus")
def menus():
    return get_menus()


@router.get("/operations/recipes")
def recipes():
    return get_recipes()


@router.get("/operations/inventory")
def inventory():
    return get_inventory()


@router.get("/operations/prices")
def prices():
    return get_prices()


class OperationsPlanRequest(BaseModel):
    menu_item: str
    portions: float


@router.post("/operations/plan")
def operations_plan(request: OperationsPlanRequest):
    try:
        return calculate_plan(
            request.menu_item,
            request.portions,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


class AIPlanRequest(BaseModel):
    date: str
    expected_attendance: float
    menu_item: str

    holiday: int = 0
    event: int = 0
    exam: int = 0

    temperature: float = 30
    rain_probability: float = 0

    previous_consumption: float = 700
    food_prepared: float = 750


@router.post("/operations/ai-plan")
def operations_ai_plan(request: AIPlanRequest):
    try:
        prediction_input = {
            "date": request.date,
            "expected_attendance": request.expected_attendance,
            "food_item": request.menu_item,
            "holiday": request.holiday,
            "event": request.event,
            "exam": request.exam,
            "temperature": request.temperature,
            "rain_probability": request.rain_probability,
            "previous_consumption": request.previous_consumption,
            "food_prepared": request.food_prepared,
        }

        prediction_input["day_of_week"] = (
            __import__("datetime")
            .datetime
            .fromisoformat(request.date)
            .weekday()
        )

        demand = demand_prediction(prediction_input)

        predicted_demand_kg = float(
            demand["predicted_demand"]
        )

        portion_conversion = calculate_portions_from_demand(
            request.menu_item,
            predicted_demand_kg,
        )

        portions = portion_conversion["predicted_portions"]

        plan = calculate_plan(
            request.menu_item,
            portions,
        )

        return {
            "ai_prediction": demand,
            "portion_conversion": portion_conversion,
            "operations_plan": plan,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )