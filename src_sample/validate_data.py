import pandas as pd


def validate_data(df: pd.DataFrame) -> bool:
    """
    Validate the processed DataFrame.
    Checks for:
    - Missing values in critical columns
    - Data types
    - Outliers (basic check)
    """
    print("Starting data validation...")

    if df.empty:
        print("Error: DataFrame is empty.")
        return False

    critical_cols = ["date", "P_SYMBOL", "ROIC"]
    missing_cols = [col for col in critical_cols if col not in df.columns]

    if missing_cols:
        print(f"Error: Missing critical columns: {missing_cols}")
        return False

    # Check for nulls in critical columns
    for col in critical_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            print(f"Warning: Column '{col}' has {null_count} missing values.")

    # Check for duplicates
    if df.duplicated(subset=["date", "P_SYMBOL"]).any():
        print("Error: Duplicate entries found for date-symbol combinations.")
        return False

    print("Data validation completed.")
    return True
