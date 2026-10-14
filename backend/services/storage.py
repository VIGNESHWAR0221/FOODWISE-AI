import json
import csv
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parents[2]
STORE = BASE / "data" / "store.json"
HISTORY_CSV = BASE / "data" / "food_history.csv"
HISTORY_DB = BASE / "data" / "foodwise.db"
STORE.parent.mkdir(parents=True, exist_ok=True)

HISTORY_COLUMNS = [
    "date", "day", "expected_attendance", "food_item", "food_prepared",
    "food_consumed", "food_wasted", "holiday", "event", "exam",
    "temperature", "rain_probability",
]

HISTORY_NUMERIC_COLUMNS = {
    "expected_attendance",
    "food_prepared",
    "food_consumed",
    "food_wasted",
    "temperature",
    "rain_probability",
}

HISTORY_INTEGER_COLUMNS = {
    "holiday",
    "event",
    "exam",
}

DEFAULT = {
    "daily_records": [],
    "inventory": [
        {"ingredient": "Rice", "required": 0, "available": 60, "unit": "kg"},
        {"ingredient": "Dal", "required": 0, "available": 25, "unit": "kg"},
        {"ingredient": "Curd", "required": 0, "available": 35, "unit": "kg"},
        {"ingredient": "Vegetables", "required": 0, "available": 50, "unit": "kg"}
    ],
    "consumption_logs": [],
    "waste_records": [],
    "predictions": [],
    "recommendations": [],
    "menus": [
        {"menu_id": "M001", "item_name": "Rice", "portion_kg": 0.10},
        {"menu_id": "M002", "item_name": "Sambar", "portion_kg": 0.08},
        {"menu_id": "M003", "item_name": "Curd", "portion_kg": 0.05},
        {"menu_id": "M004", "item_name": "Vegetables", "portion_kg": 0.07}
    ]
}


def load():
    if not STORE.exists():
        save(DEFAULT)

    return json.loads(STORE.read_text(encoding="utf-8"))


def save(data):
    STORE.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8"
    )


def add(collection, item):
    db = load()

    item = dict(item)

    item["id"] = item.get("id") or (
        f"{collection}-{len(db.get(collection, [])) + 1}"
    )

    item["created_at"] = datetime.utcnow().isoformat()

    db.setdefault(collection, []).append(item)

    save(db)

    return item


def _history_value(column, value):
    if value is None or value == "":
        return None

    if column in HISTORY_INTEGER_COLUMNS:
        return int(value)

    if column in HISTORY_NUMERIC_COLUMNS:
        return float(value)

    return value


def _history_hash(row):
    values = [
        "" if row.get(column) in (None, "") else str(row[column])
        for column in HISTORY_COLUMNS
    ]

    return hashlib.sha256(
        "\x1f".join(values).encode("utf-8")
    ).hexdigest()


def initialize_history_database():
    with sqlite3.connect(HISTORY_DB) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS historical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                day TEXT,
                expected_attendance REAL,
                food_item TEXT,
                food_prepared REAL,
                food_consumed REAL,
                food_wasted REAL,
                holiday INTEGER,
                event INTEGER,
                exam INTEGER,
                temperature REAL,
                rain_probability REAL,
                record_hash TEXT NOT NULL UNIQUE
            )
        """)

        inserted = 0
        skipped = 0

        with HISTORY_CSV.open(
            newline="",
            encoding="utf-8"
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            if reader.fieldnames != HISTORY_COLUMNS:
                raise ValueError(
                    f"Unexpected historical CSV columns: {reader.fieldnames}"
                )

            for source_row in reader:

                row = {
                    column: _history_value(
                        column,
                        source_row.get(column)
                    )
                    for column in HISTORY_COLUMNS
                }

                record_hash = _history_hash(source_row)

                values = [
                    row[column]
                    for column in HISTORY_COLUMNS
                ] + [record_hash]

                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO historical_records (
                        date,
                        day,
                        expected_attendance,
                        food_item,
                        food_prepared,
                        food_consumed,
                        food_wasted,
                        holiday,
                        event,
                        exam,
                        temperature,
                        rain_probability,
                        record_hash
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )

                if cursor.rowcount:
                    inserted += 1
                else:
                    skipped += 1

        return {
            "inserted": inserted,
            "skipped": skipped
        }


def get_history():
    
    with sqlite3.connect(HISTORY_DB) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                date,
                food_item,
                meal_type,
                day_of_week,
                is_weekend,
                is_holiday,
                event_flag,
                expected_attendance,
                actual_attendance,
                temperature_c,
                rain_mm,
                prepared_kg,
                consumed_kg,
                leftover_kg,
                plate_waste_kg
            FROM food_history
            ORDER BY date
            """
        ).fetchall()

        history = []

        for row in rows:
            record = dict(row)

            history.append({
                "date": record["date"],
                "day": record["day_of_week"],
                "expected_attendance": record["expected_attendance"],
                "food_item": record["food_item"],
                "food_prepared": record["prepared_kg"],
                "food_consumed": record["consumed_kg"],
                "food_wasted": (
                    (record["leftover_kg"] or 0)
                    + (record["plate_waste_kg"] or 0)
                ),
                "holiday": record["is_holiday"],
                "event": record["event_flag"],
                "exam": None,
                "temperature": record["temperature_c"],
                "rain_probability": record["rain_mm"],
                "actual_attendance": record["actual_attendance"],
                "is_weekend": record["is_weekend"],
                "leftover_kg": record["leftover_kg"],
                "plate_waste_kg": record["plate_waste_kg"],
            })

        return history


def get_dataset_summary():
    with sqlite3.connect(HISTORY_DB) as connection:

        tables = [
            "food_history",
            "weather_history",
            "events",
            "holidays",
        ]

        summary = {}

        for table in tables:

            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            summary[table] = {
                "count": count
            }

        date_range = connection.execute(
            """
            SELECT MIN(date), MAX(date)
            FROM food_history
            """
        ).fetchone()

        summary["food_history"]["min_date"] = date_range[0]
        summary["food_history"]["max_date"] = date_range[1]

        return summary