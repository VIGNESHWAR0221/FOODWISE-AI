import csv
from pathlib import Path


BASE = Path(__file__).resolve().parents[2]
OPERATIONS_DIR = BASE / "data" / "operations"


def _read_csv(filename):
    path = OPERATIONS_DIR / filename

    with path.open(
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def get_ingredients():
    return _read_csv("ingredients.csv")


def get_menus():
    return _read_csv("menus.csv")


def get_recipes():
    return _read_csv("recipes.csv")


def get_inventory():
    return _read_csv("inventory.csv")


def get_prices():
    return _read_csv("ingredient_prices.csv")