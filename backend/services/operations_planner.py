from services.operations import (
    get_recipes,
    get_inventory,
    get_prices,
)


def get_menu_portion_size(menu_item: str):
    recipes = get_recipes()

    menu_recipes = [
        row for row in recipes
        if row["menu_item"].strip().lower() == menu_item.strip().lower()
    ]

    if not menu_recipes:
        raise ValueError(f"No recipe found for menu item: {menu_item}")

    total_per_portion = sum(
        float(row["quantity_per_portion"])
        for row in menu_recipes
    )

    return round(total_per_portion, 4)


def calculate_portions_from_demand(
    menu_item: str,
    predicted_demand_kg: float,
):
    if predicted_demand_kg <= 0:
        raise ValueError("Predicted demand must be greater than zero.")

    portion_size = get_menu_portion_size(menu_item)

    if portion_size <= 0:
        raise ValueError(
            f"Invalid portion size for menu item: {menu_item}"
        )

    predicted_portions = predicted_demand_kg / portion_size

    return {
        "menu_item": menu_item,
        "predicted_demand_kg": round(predicted_demand_kg, 3),
        "recipe_quantity_per_portion_kg": portion_size,
        "predicted_portions": round(predicted_portions),
    }


def calculate_plan(menu_item: str, portions: float):
    recipes = get_recipes()
    inventory = get_inventory()
    prices = get_prices()

    if portions <= 0:
        raise ValueError("Portions must be greater than zero.")

    menu_recipes = [
        row for row in recipes
        if row["menu_item"].strip().lower() == menu_item.strip().lower()
    ]

    if not menu_recipes:
        raise ValueError(f"No recipe found for menu item: {menu_item}")

    inventory_by_id = {
        row["ingredient_id"]: row
        for row in inventory
    }

    prices_by_id = {
        row["ingredient_id"]: row
        for row in prices
    }

    ingredients = []

    for recipe in menu_recipes:
        ingredient_id = recipe["ingredient_id"]
        required = float(recipe["quantity_per_portion"]) * portions

        inventory_row = inventory_by_id.get(ingredient_id, {})
        price_row = prices_by_id.get(ingredient_id, {})

        available = float(
            inventory_row.get("available_quantity", 0)
        )

        cost_per_unit = float(
            price_row.get("cost_per_unit", 0)
        )

        purchase = max(required - available, 0)
        estimated_cost = purchase * cost_per_unit

        ingredients.append({
            "ingredient_id": ingredient_id,
            "ingredient_name": inventory_row.get(
                "ingredient_name",
                ingredient_id
            ),
            "required_quantity": round(required, 3),
            "available_quantity": round(available, 3),
            "purchase_quantity": round(purchase, 3),
            "unit": recipe["unit"],
            "cost_per_unit": round(cost_per_unit, 2),
            "estimated_purchase_cost": round(estimated_cost, 2),
        })

    return {
        "menu_item": menu_item,
        "portions": portions,
        "ingredients": ingredients,
        "total_estimated_purchase_cost": round(
            sum(x["estimated_purchase_cost"] for x in ingredients),
            2,
        ),
    }