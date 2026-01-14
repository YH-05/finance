import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # ROIC Analysis Ver.2

    This notebook executes the analysis phase of the ROIC project.

    **Steps:**

    1. Load Processed Data
    2. Performance Analysis (Returns, Sharpe, Drawdowns)
    3. Factor Analysis (Double Sorts, Heatmaps)
    4. Macro Analysis (Conditional Performance)
    5. Visualization
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import sys
    from pathlib import Path

    import pandas as pd
    from dotenv import load_dotenv

    # Add project root to path
    current_dir = Path.cwd()
    if current_dir.name == "notebook":
        root_dir = current_dir.parent
    else:
        root_dir = current_dir

    sys.path.append(str(root_dir))

    from src.roic_analysis.factor_analysis import FactorAnalyzer
    from src.roic_analysis.macro_analyzer import MacroAnalyzer
    from src.roic_analysis.performance_analysis import PerformanceAnalyzer
    from src.roic_analysis.visualization import ROICVisualizer

    load_dotenv(root_dir / ".env")
    return (
        FactorAnalyzer,
        MacroAnalyzer,
        PerformanceAnalyzer,
        ROICVisualizer,
        pd,
        root_dir,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Load Data
    """)


@app.cell
def _(display, pd, root_dir):
    DATA_DIR = root_dir / "data"
    data_path = DATA_DIR / "MSCI_KOKUSAI_enhanced_data.parquet"

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        print("Please run ROIC_Preprocessing_ver2.ipynb first.")
    else:
        df = pd.read_parquet(data_path)
        print(f"Loaded Data Shape: {df.shape}")
        display(df.head())
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Performance Analysis
    """)


@app.cell
def _(PerformanceAnalyzer, ROICVisualizer, df, display, pd):
    perf_analyzer = PerformanceAnalyzer()
    visualizer = ROICVisualizer()

    # Analyze by ROIC Rank
    if "ROIC_Rank" in df.columns:
        print("Analyzing Performance by ROIC Rank...")
        ranks = sorted(df["ROIC_Rank"].unique())

        metrics_list = []
        for rank in ranks:
            rank_df = (
                df[df["ROIC_Rank"] == rank]
                .groupby("date")["Return_1M"]
                .mean()
                .reset_index()
            )
            metrics = perf_analyzer.calculate_metrics(rank_df, return_col="Return_1M")
            metrics["Rank"] = rank
            metrics_list.append(metrics)

        metrics_df = pd.DataFrame(metrics_list).set_index("Rank")
        display(metrics_df)

        # Plot Cumulative Returns
        cum_returns = pd.DataFrame()
        for rank in ranks:
            rank_df = (
                df[df["ROIC_Rank"] == rank]
                .groupby("date")["Return_1M"]
                .mean()
                .reset_index()
            )
            cum_returns[rank] = perf_analyzer.calculate_cumulative_returns(
                rank_df, "Return_1M"
            )

        cum_returns.index = rank_df["date"]
        visualizer.plot_cumulative_returns(
            cum_returns, title="Cumulative Returns by ROIC Rank"
        )
    return (visualizer,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Factor Analysis (Double Sort)
    """)


@app.cell
def _(FactorAnalyzer, df, visualizer):
    factor_analyzer = FactorAnalyzer()

    # Example: ROIC vs Valuation (e.g., P/E or similar if available)
    # Assuming 'PER' or similar exists, or use 'WACC' as proxy for risk/cost
    factor1 = "ROIC"
    factor2 = "WACC"  # Just as an example

    if factor1 in df.columns and factor2 in df.columns:
        print(f"Performing Double Sort: {factor1} vs {factor2}")
        portfolio_returns = factor_analyzer.perform_double_sort(
            df, factor1, factor2, return_col="Return_1M", n_quantiles=5
        )

        visualizer.plot_factor_heatmap(
            portfolio_returns,
            title=f"Double Sort: {factor1} (Rows) vs {factor2} (Cols)",
        )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Macro Analysis
    """)


@app.cell
def _(MacroAnalyzer, df, display, root_dir, visualizer):
    FRED_DB_PATH = root_dir / "data/FRED/FRED.db"
    macro_analyzer = MacroAnalyzer(fred_db_path=FRED_DB_PATH)

    try:
        # Load 10Y Treasury Yield
        macro_df = macro_analyzer.load_macro_data(["DGS10"])
        if not macro_df.empty:
            # Define Regime
            macro_df = macro_analyzer.define_regimes(macro_df, "DGS10", method="trend")

            # Analyze Strategy Performance (e.g., High ROIC Portfolio)
            high_roic_df = (
                df[df["ROIC_Rank"] == "rank1"]
                .groupby("date")["Return_1M"]
                .mean()
                .reset_index()
            )
            high_roic_df = high_roic_df.rename(columns={"Return_1M": "Return"})

            regime_perf = macro_analyzer.analyze_conditional_performance(
                high_roic_df, macro_df, regime_col="DGS10_Regime"
            )
            display(regime_perf)

            visualizer.plot_bar_chart(
                regime_perf["Annualized Return"],
                title="High ROIC Performance by 10Y Yield Regime",
                ylabel="Annualized Return",
            )
    except Exception as e:
        print(f"Macro analysis skipped or failed: {e}")


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
