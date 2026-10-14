import csv
import hashlib
import sqlite3
from pathlib import Path


BASE = Path(__file__).resolve().parents[2]
DB_PATH = BASE / "data" / "foodwise.db"
STAGING = BASE / "data" / "staging"


def row_hash(row):
    text = "\x1f".join(
        "" if value is None else str(value)
        for value in row.values()
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(filename):
    path = STAGING / filename

    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def create_tables(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS food_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            food_item TEXT,
            meal_type TEXT,
            day_of_week TEXT,
            is_weekend INTEGER,
            is_holiday INTEGER,
            event_flag INTEGER,
            expected_attendance REAL,
            actual_attendance REAL,
            temperature_c REAL,
            rain_mm REAL,
            prepared_kg REAL,
            consumed_kg REAL,
            leftover_kg REAL,
            plate_waste_kg REAL,
            record_hash TEXT UNIQUE NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            temperature_c REAL,
            rain_mm REAL,
            record_hash TEXT UNIQUE NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            event_name TEXT,
            record_hash TEXT UNIQUE NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            holiday_name TEXT,
            record_hash TEXT UNIQUE NOT NULL
        )
    """)


def import_food_history(connection):
    rows = read_csv("food_history.csv")
    inserted = 0

    for row in rows:
        record_hash = row_hash(row)

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO food_history (
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
                plate_waste_kg,
                record_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["date"],
                row["food_item"],
                row["meal_type"],
                row["day_of_week"],
                int(row["is_weekend"]) if row["is_weekend"] else None,
                int(row["is_holiday"]) if row["is_holiday"] else None,
                int(row["event_flag"]) if row["event_flag"] else None,
                float(row["expected_attendance"]) if row["expected_attendance"] else None,
                float(row["actual_attendance"]) if row["actual_attendance"] else None,
                float(row["temperature_c"]) if row["temperature_c"] else None,
                float(row["rain_mm"]) if row["rain_mm"] else None,
                float(row["prepared_kg"]) if row["prepared_kg"] else None,
                float(row["consumed_kg"]) if row["consumed_kg"] else None,
                float(row["leftover_kg"]) if row["leftover_kg"] else None,
                float(row["plate_waste_kg"]) if row["plate_waste_kg"] else None,
                record_hash,
            ),
        )

        inserted += cursor.rowcount

    return len(rows), inserted


def import_weather(connection):
    rows = read_csv("weather_history.csv")
    inserted = 0

    for row in rows:
        record_hash = row_hash(row)

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO weather_history (
                date,
                temperature_c,
                rain_mm,
                record_hash
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                row["date"],
                float(row["temperature_c"]) if row["temperature_c"] else None,
                float(row["rain_mm"]) if row["rain_mm"] else None,
                record_hash,
            ),
        )

        inserted += cursor.rowcount

    return len(rows), inserted


def import_events(connection):
    rows = read_csv("events.csv")
    inserted = 0

    for row in rows:
        record_hash = row_hash(row)

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO events (
                date,
                event_name,
                record_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                row["date"],
                row["event_name"],
                record_hash,
            ),
        )

        inserted += cursor.rowcount

    return len(rows), inserted


def import_holidays(connection):
    rows = read_csv("holidays.csv")
    inserted = 0

    for row in rows:
        record_hash = row_hash(row)

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO holidays (
                date,
                holiday_name,
                record_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                row["date"],
                row["holiday_name"],
                record_hash,
            ),
        )

        inserted += cursor.rowcount

    return len(rows), inserted


def main():
    print("FOODWISE staged-data migration")
    print(f"Database: {DB_PATH}")
    print(f"Staging:  {STAGING}")
    print()

    with sqlite3.connect(DB_PATH) as connection:
        create_tables(connection)

        food_total, food_inserted = import_food_history(connection)
        weather_total, weather_inserted = import_weather(connection)
        events_total, events_inserted = import_events(connection)
        holidays_total, holidays_inserted = import_holidays(connection)

        connection.commit()

        print(f"food_history:    {food_inserted}/{food_total} inserted")
        print(f"weather_history: {weather_inserted}/{weather_total} inserted")
        print(f"events:          {events_inserted}/{events_total} inserted")
        print(f"holidays:        {holidays_inserted}/{holidays_total} inserted")

        print()
        print("Final database counts:")

        for table in [
            "historical_records",
            "food_history",
            "weather_history",
            "events",
            "holidays",
        ]:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count}")


if __name__ == "__main__":
    main()





    