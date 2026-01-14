import datetime
import sqlite3
from pathlib import Path

import pandas as pd
from bloomberg_utils import BlpapiCustom


def verify_bloomberg_utils():
    print("🚀 Starting verification of Bloomberg Utils...")

    api = BlpapiCustom()
    db_path = Path("test_financial_data.db")

    # Clean up previous test db
    if db_path.exists():
        try:
            db_path.unlink()
            print("🗑️ Removed existing test database.")
        except PermissionError:
            print("⚠️ Could not remove test database. It might be in use.")

    # 1. Test get_financial_data
    print("\n1️⃣ Testing get_financial_data...")
    tickers = ["AAPL US Equity", "MSFT US Equity"]
    fields = ["SALES_REV_TURN", "NET_INCOME"]

    try:
        df = api.get_financial_data(
            securities=tickers,
            fields=fields,
            period="Q",
            fiscal_period="-1FY",  # Last fiscal year
            currency="USD",
            chunk_size=1,  # Force chunking
            verbose=True,
        )

        if not df.empty:
            print(f"✅ get_financial_data returned {len(df)} rows.")
            print(df.head())

            # Check columns
            expected_cols = [
                "Ticker",
                "Field",
                "Period_End_Date",
                "Value",
                "Currency",
                "Fiscal_Period",
                "Updated_At",
            ]
            missing_cols = [col for col in expected_cols if col not in df.columns]
            if not missing_cols:
                print("✅ All expected columns are present.")
            else:
                print(f"❌ Missing columns: {missing_cols}")
        else:
            print(
                "⚠️ get_financial_data returned empty DataFrame. (Check Bloomberg connection)"
            )
            # Create dummy data for database test if API fails (e.g. no connection)
            print("⚠️ Creating dummy data for database test...")
            df = pd.DataFrame(
                {
                    "Ticker": ["AAPL US Equity", "MSFT US Equity"],
                    "Field": ["SALES_REV_TURN", "NET_INCOME"],
                    "Period_End_Date": ["2023-09-30", "2023-06-30"],
                    "Value": [100.0, 200.0],
                    "Currency": ["USD", "USD"],
                    "Fiscal_Period": ["-1FY", "-1FY"],
                    "Updated_At": [
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    * 2,
                }
            )

    except Exception as e:
        print(f"❌ Error in get_financial_data: {e}")
        return

    # 2. Test store_to_database
    print("\n2️⃣ Testing store_to_database...")
    table_name = "financial_data"
    primary_keys = ["Ticker", "Field", "Period_End_Date", "Fiscal_Period"]

    try:
        rows = api.store_to_database(
            df=df,
            db_path=db_path,
            table_name=table_name,
            primary_keys=primary_keys,
            conflict_action="REPLACE",
            verbose=True,
        )
        print(f"✅ store_to_database processed {rows} rows.")

        # Verify DB content
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        db_rows = cursor.fetchall()
        print(f"📊 Rows in DB: {len(db_rows)}")
        conn.close()

        if len(db_rows) == len(df):
            print("✅ Database content matches DataFrame length.")
        else:
            print(
                f"❌ Database content mismatch: Expected {len(df)}, got {len(db_rows)}"
            )

    except Exception as e:
        print(f"❌ Error in store_to_database: {e}")

    # 3. Test update (REPLACE)
    print("\n3️⃣ Testing update (REPLACE)...")
    # Modify value
    df.loc[0, "Value"] = 999.9
    df.loc[0, "Updated_At"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        rows = api.store_to_database(
            df=df,
            db_path=db_path,
            table_name=table_name,
            primary_keys=primary_keys,
            conflict_action="REPLACE",
            verbose=True,
        )
        print(f"✅ store_to_database (update) processed {rows} rows.")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT Value FROM {table_name} WHERE Ticker=? AND Field=?",
            (df.loc[0, "Ticker"], df.loc[0, "Field"]),
        )
        val = cursor.fetchone()[0]
        conn.close()

        if val == 999.9:
            print("✅ Value updated correctly.")
        else:
            print(f"❌ Value update failed: Expected 999.9, got {val}")

    except Exception as e:
        print(f"❌ Error in update test: {e}")

    print("\n🎉 Verification completed.")


if __name__ == "__main__":
    verify_bloomberg_utils()
