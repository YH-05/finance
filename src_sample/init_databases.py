import sqlite3
from pathlib import Path


def init_databases():
    base_dir = Path(__file__).parent.parent / "data"
    base_dir.mkdir(parents=True, exist_ok=True)

    market_db_path = base_dir / "Market_Data.db"
    valuation_db_path = base_dir / "Valuation_History.db"

    schema_path = Path(__file__).parent / "database_schema.sql"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split schema by database comments or just execute all?
    # The schema file contains SQL for both DBs. I need to split it or execute relevant parts.
    # Actually, the schema file I wrote has comments "-- Market_Data.db Schema" and "-- Valuation_History.db Schema".
    # I will parse it simply.

    market_sql = ""
    valuation_sql = ""

    current_target = None
    for line in schema_sql.splitlines():
        if "Market_Data.db" in line:
            current_target = "market"
            continue
        elif "Valuation_History.db" in line:
            current_target = "valuation"
            continue

        if current_target == "market":
            market_sql += line + "\n"
        elif current_target == "valuation":
            valuation_sql += line + "\n"

    print(f"Initializing {market_db_path}...")
    with sqlite3.connect(market_db_path) as conn:
        conn.executescript(market_sql)

    print(f"Initializing {valuation_db_path}...")
    with sqlite3.connect(valuation_db_path) as conn:
        conn.executescript(valuation_sql)

    print("Databases initialized successfully.")


if __name__ == "__main__":
    init_databases()
