import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # ROIC Preprocessing Ver.2

    This notebook executes the data preprocessing pipeline for ROIC analysis using the `roic_analysis` package.

    **Steps:**

    1. Load Data (Factset, Bloomberg, Index Constituents)
    2. Feature Engineering (WACC, Economic Profit, iROIC, etc.)
    3. Data Validation
    4. Save Processed Data
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import os
    import sys
    from pathlib import Path

    from dotenv import load_dotenv

    # Add project root to path
    current_dir = Path.cwd()
    if current_dir.name == "notebook":
        root_dir = current_dir.parent
    else:
        root_dir = current_dir

    sys.path.append(str(root_dir))

    from src.roic_analysis.data_loader import ROICDataLoader
    from src.roic_analysis.feature_engineering import FactorEngineer
    from src.validate_data import validate_data

    load_dotenv(root_dir / ".env")
    return FactorEngineer, Path, ROICDataLoader, os, root_dir, validate_data


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Load Data
    """)


@app.cell
def _(Path, os, root_dir):
    # Define Paths (Load from env or set defaults)
    UNIVERSE_CODE = "MSXJPN_AD"

    FACTSET_FINANCIALS_DIR = Path(
        os.environ.get("FACTSET_FINANCIALS_DIR", root_dir / "data/Factset/Financials")
    )
    FACTSET_INDEX_CONSTITUENTS_DIR = Path(
        os.environ.get(
            "FACTSET_INDEX_CONSTITUENTS_DIR", root_dir / "data/Factset/Index"
        )
    )
    BLOOMBERG_DATA_DIR = Path(
        os.environ.get("BLOOMBERG_DATA_DIR", root_dir / "data/Bloomberg")
    )

    financials_db_path = (
        FACTSET_FINANCIALS_DIR / UNIVERSE_CODE / "Financials_and_Price.db"
    )
    index_constituents_db_path = (
        FACTSET_INDEX_CONSTITUENTS_DIR / "Index_Constituents.db"
    )
    bloomberg_db_path = BLOOMBERG_DATA_DIR / "Index_Price_and_Returns.db"

    print(f"Financials DB: {financials_db_path}")
    print(f"Index DB: {index_constituents_db_path}")
    print(f"Bloomberg DB: {bloomberg_db_path}")
    return (
        UNIVERSE_CODE,
        bloomberg_db_path,
        financials_db_path,
        index_constituents_db_path,
    )


@app.cell
def _(
    ROICDataLoader,
    UNIVERSE_CODE,
    bloomberg_db_path,
    display,
    financials_db_path,
    index_constituents_db_path,
):
    # Initialize Loader
    loader = ROICDataLoader(
        financials_db_path=financials_db_path,
        index_constituents_db_path=index_constituents_db_path,
        bloomberg_db_path=bloomberg_db_path,
        universe_code=UNIVERSE_CODE,
    )

    # Load and Preprocess
    df = loader.load_and_preprocess()
    print(f"Loaded Data Shape: {df.shape}")
    display(df.head())
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Feature Engineering
    """)


@app.cell
def _(FactorEngineer, df, display):
    engineer = FactorEngineer()
    print("Calculating WACC and Economic Profit...")
    # 1. WACC & Economic Profit
    df_1 = engineer.calculate_wacc(df)
    df_1 = engineer.calculate_economic_profit(df_1)
    print("Calculating Incremental ROIC...")
    df_1 = engineer.calculate_incremental_roic(df_1)
    # 2. Incremental ROIC
    print("Performing DuPont Decomposition...")
    df_1 = engineer.decompose_dupont(df_1)
    print("Adding ROIC Ranks...")
    # 3. DuPont Decomposition
    df_1 = engineer.add_roic_rank_cols(df_1)
    if "RD_Expense" in df_1.columns:
        print("Capitalizing R&D...")
        # 4. ROIC Ranks
        df_1 = engineer.capitalize_intangibles(df_1)
    # 5. Intangible Capitalization (Optional/Advanced)
    display(df_1.head())
    return (df_1,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Validation
    """)


@app.cell
def _(df_1, validate_data):
    is_valid = validate_data(df_1)
    if not is_valid:
        print("WARNING: Data validation found issues. Check logs.")
    else:
        print("Data validation passed.")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Save Data
    """)


@app.cell
def _(df_1, root_dir):
    output_path = root_dir / "data" / "MSCI_KOKUSAI_enhanced_data.parquet"
    df_1.to_parquet(output_path)
    print(f"Saved processed data to: {output_path}")


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
