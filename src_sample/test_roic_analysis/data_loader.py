import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent directory to path to import bloomberg_utils if needed
sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from bloomberg_utils import BlpapiCustom
except ImportError:
    pass


class ROICDataLoader:
    def __init__(
        self,
        financials_db_path: Path,
        index_constituents_db_path: Path,
        bloomberg_db_path: Path,
        universe_code: str,
    ):
        self.financials_db_path = financials_db_path
        self.index_constituents_db_path = index_constituents_db_path
        self.bloomberg_db_path = bloomberg_db_path
        self.universe_code = universe_code

    def load_factset_data(self) -> pd.DataFrame:
        """
        Load Factset data from SQLite databases.
        This is a placeholder implementation. You need to adjust the SQL query
        based on your actual schema in Financials_and_Price.db.
        """
        if not self.financials_db_path.exists():
            print(f"Financials DB not found: {self.financials_db_path}")
            return pd.DataFrame()

        try:
            with sqlite3.connect(self.financials_db_path) as conn:
                # Example query - adjust table names and columns
                query = "SELECT * FROM financials"
                # If table name is unknown, you might need to inspect the DB first.
                # For now, returning an empty DF or a mock if DB structure is unknown.
                # Assuming a standard structure for now.
                try:
                    df = pd.read_sql(query, conn)
                except:
                    # Fallback if table 'financials' doesn't exist
                    df = pd.DataFrame()
            return df
        except Exception as e:
            print(f"Error loading Factset data: {e}")
            return pd.DataFrame()

    def load_index_constituents(self) -> pd.DataFrame:
        """
        Load index constituents.
        """
        if not self.index_constituents_db_path.exists():
            print(f"Index DB not found: {self.index_constituents_db_path}")
            return pd.DataFrame()

        try:
            with sqlite3.connect(self.index_constituents_db_path) as conn:
                query = "SELECT * FROM constituents"  # Adjust table name
                try:
                    df = pd.read_sql(query, conn)
                except:
                    df = pd.DataFrame()
            return df
        except Exception as e:
            print(f"Error loading index constituents: {e}")
            return pd.DataFrame()

    def load_bloomberg_data(self) -> pd.DataFrame:
        """
        Load Bloomberg data.
        """
        if not self.bloomberg_db_path.exists():
            print(f"Bloomberg DB not found: {self.bloomberg_db_path}")
            return pd.DataFrame()

        try:
            with sqlite3.connect(self.bloomberg_db_path) as conn:
                query = "SELECT * FROM bloomberg_data"  # Adjust table name
                try:
                    df = pd.read_sql(query, conn)
                except:
                    df = pd.DataFrame()
            return df
        except Exception as e:
            print(f"Error loading Bloomberg data: {e}")
            return pd.DataFrame()

    def load_and_preprocess(self) -> pd.DataFrame:
        """
        Main method to load all data and merge/preprocess it.
        """
        print("Loading index constituents...")
        df_index = self.load_index_constituents()

        print("Loading financials...")
        df_financials = self.load_factset_data()

        print("Loading Bloomberg data...")
        df_bloomberg = self.load_bloomberg_data()

        print("Merging data...")
        # Placeholder merge logic.
        # In a real scenario, you would merge on date and symbol/ticker.
        # Since we don't have the exact schema, we'll return a dummy DataFrame
        # matching the shape expected by the notebook for demonstration if loading fails.

        if df_financials.empty and df_index.empty:
            # Return a mock dataframe for testing if DBs are empty/missing
            dates = pd.date_range(start="2000-01-31", periods=10, freq="M")
            data = {
                "date": dates,
                "P_SYMBOL": ["TEST"] * 10,
                "GICS Sector": ["Information Technology"] * 10,
                "ROIC": np.random.rand(10),
                "Rtn_1M": np.random.rand(10),
                "RD_Expense": np.random.rand(10) * 100,
                "NOPAT": np.random.rand(10) * 1000,
                "Invested_Capital": np.random.rand(10) * 5000,
                "Total_Debt": np.random.rand(10) * 2000,
                "Total_Equity": np.random.rand(10) * 3000,
            }
            return pd.DataFrame(data)

        # Actual merge logic would go here
        df = df_financials  # Placeholder

        return df
