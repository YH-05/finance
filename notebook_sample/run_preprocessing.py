import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
script_dir = Path(__file__).resolve().parent
src_path = script_dir.parent / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from roic_analysis.data_loader import ROICDataLoader
from roic_analysis.feature_engineering import FactorEngineer
from validate_data import validate_data


def main():
    print("Starting verification script...")

    # Define paths
    script_dir = Path(__file__).resolve().parent
    DATA_DIR = script_dir.parent / "data"
    FINANCIALS_DB = DATA_DIR / "Factset" / "Financials_and_Price.db"
    INDEX_DB = DATA_DIR / "Factset" / "Index_Constituents.db"
    BLOOMBERG_DB = DATA_DIR / "Bloomberg" / "bloomberg.db"

    # Initialize Loader
    print("Initializing ROICDataLoader...")
    loader = ROICDataLoader(FINANCIALS_DB, INDEX_DB, BLOOMBERG_DB, "MSCI_KOKUSAI")

    # Load Data
    print("Loading data...")
    df = loader.load_and_preprocess()
    print(f"Loaded data shape: {df.shape}")

    if df.empty:
        print("Warning: Loaded DataFrame is empty. Check database paths or mock logic.")
        # Create dummy data if empty for testing feature engineering logic
        dates = pd.date_range(start="2020-01-31", periods=12, freq="M")
        data = {
            "date": dates,
            "P_SYMBOL": ["TEST"] * 12,
            "GICS Sector": ["Information Technology"] * 12,
            "ROIC": np.random.rand(12),
            "Rtn_1M": np.random.rand(12),
            "RD_Expense": np.random.rand(12) * 100,
            "NOPAT": np.random.rand(12) * 1000,
            "Invested_Capital": np.random.rand(12) * 5000,
            "Total_Debt": np.random.rand(12) * 2000,
            "Total_Equity": np.random.rand(12) * 3000,
            "Sales": np.random.rand(12) * 6000,
            "Interest_Expense": np.random.rand(12) * 100,
            "Tax_Rate": [0.25] * 12,
        }
        df = pd.DataFrame(data)
        print("Created dummy data for testing.")

    # Feature Engineering
    engineer = FactorEngineer()

    print("Calculating WACC...")
    df = engineer.calculate_wacc(df)

    print("Calculating Economic Profit...")
    df = engineer.calculate_economic_profit(df)

    print("Calculating Incremental ROIC...")
    df = engineer.calculate_incremental_roic(df)

    print("Decomposing DuPont...")
    df = engineer.decompose_dupont(df)

    print("Capitalizing Intangibles...")
    df = engineer.capitalize_intangibles(df)

    print("Columns after feature engineering:", df.columns.tolist())

    # Validation
    if validate_data(df):
        print("Data validation passed.")
        # Save
        output_path = DATA_DIR / "MSCI_KOKUSAI_enhanced_data.parquet"
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path)
        print(f"Data saved to {output_path}")
    else:
        print("Data validation failed.")


if __name__ == "__main__":
    main()
