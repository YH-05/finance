import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # `ROIC-Analysis_ver3.ipynb`
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo
    import logging
    import os
    import sqlite3
    import sys
    import warnings
    from pathlib import Path

    import pandas as pd
    import plotly.graph_objects as go
    from dotenv import load_dotenv

    # ルートロガーのレベルをWARNINGに設定
    # これにより、INFOレベルのメッセージはすべて抑制されます
    logging.basicConfig(level=logging.WARNING)
    # warnings.simplefilter("ignore", category=UserWarning)
    warnings.filterwarnings("ignore")
    load_dotenv()

    UNIVERSE_CODE = "MSXJPN_AD"

    QUANTS_DIR = Path(os.environ.get("QUANTS_DIR"))  # type: ignore
    FACTSET_ROOT_DIR = Path(os.environ.get("FACTSET_ROOT_DIR"))  # type: ignore
    FACTSET_FINANCIALS_DIR = Path(os.environ.get("FACTSET_FINANCIALS_DIR"))  # type: ignore
    FACTSET_INDEX_CONSTITUENTS_DIR = Path(
        os.environ.get("FACTSET_INDEX_CONSTITUENTS_DIR")
    )  # type: ignore
    INDEX_DIR = FACTSET_FINANCIALS_DIR / UNIVERSE_CODE
    BPM_ROOT_DIR = Path(os.environ.get("BPM_ROOT_DIR"))  # type: ignore
    BLOOMBERG_ROOT_DIR = Path(os.environ.get("BLOOMBERG_ROOT_DIR"))  # type: ignore
    BLOOMBERG_DATA_DIR = Path(os.environ.get("BLOOMBERG_DATA_DIR"))  # type: ignore

    sys.path.insert(0, str(QUANTS_DIR))
    import src.database_utils as db_utils
    import src.ROIC_make_data_files_ver2 as roic_utils
    from src.roic_analysis import PerformanceAnalyzer

    financials_db_path = INDEX_DIR / "Financials_and_Price.db"
    factset_index_db_path = FACTSET_INDEX_CONSTITUENTS_DIR / "Index_Constituents.db"
    bloomberg_index_db_path = BLOOMBERG_ROOT_DIR / "Index_Price_and_Returns.db"
    bloomberg_valuation_db_path = BLOOMBERG_ROOT_DIR / "Valuation.db"
    bpm_db_path = BPM_ROOT_DIR / "Index_Constituents.db"

    # Alpha Sector / Non-alpha Sector
    alpha_sectors = [
        "Information Technology",
        "Communication Services",
        "Health Care",
        "Industrials",
        "Materials",
        "Consumer Staples",
        "Consumer Discretionary",
        "Financials",
    ]
    non_alpha_sectors = ["Energy", "Utilities", "Real Estate"]
    return (
        PerformanceAnalyzer,
        UNIVERSE_CODE,
        alpha_sectors,
        db_utils,
        factset_index_db_path,
        financials_db_path,
        go,
        non_alpha_sectors,
        pd,
        roic_utils,
        sqlite3,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Analysis plan

    ### 1. 2025 年（直近）の loser 特定

    -   ROIC が低下した銘柄群

        -   ROIC 分位を移動した銘柄でラベリング（3 年前 ROIC 分位 -> 現在 ROIC 分位 でラベリング）

            -   ラベルごとの銘柄数をカウントする必要あり

    ### 2. ROIC dispersion の計測

    -   計測済み

    ### 3. ヒストリカルのグロース性が高かった銘柄

    -   長期期間と直近のパフォーマンス比較

        -   期待リターンと効率性計測

        -   active return 計測

        -   IC 計測
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. 2025 年（直近）の loser 特定

    -   ROIC が低下した銘柄群

        -   ROIC 分位を移動した銘柄でラベリング（3 年前 ROIC 分位 -> 現在 ROIC 分位 でラベリング）

            -   ラベルごとの銘柄数をカウントする必要あり
    """)


@app.cell
def _(
    PerformanceAnalyzer,
    UNIVERSE_CODE,
    factset_index_db_path,
    financials_db_path,
):
    analyzer = PerformanceAnalyzer(
        factset_index_db_path=factset_index_db_path,
        financials_db_path=financials_db_path,
        UNIVERSE_CODE=UNIVERSE_CODE,
    )
    df = analyzer.data_loader()
    return analyzer, df


@app.cell
def _(analyzer, df):
    # ROIC_label_Past3Y のperformance
    roic_factor_name = "ROIC_label_Past3Y"
    return_col = "Return_3Y_annlzd"
    _df_to_plot = analyzer.calculate_mean_returns_for_roic_label(
        df=df, factor_col=roic_factor_name, return_col=return_col
    )
    analyzer.plot_roic_label_performance(
        df_to_plot=_df_to_plot, roic_factor_name=roic_factor_name, return_col=return_col
    )


@app.cell
def _(analyzer, df):
    roic_factor_name_1 = "ROIC_label_Past3Y"
    return_col_1 = "Active_Return_3Y_annlzd"
    _df_to_plot = analyzer.calculate_mean_returns_for_roic_label(
        df=df, factor_col=roic_factor_name_1, return_col=return_col_1
    )
    analyzer.plot_roic_label_performance(
        df_to_plot=_df_to_plot,
        roic_factor_name=roic_factor_name_1,
        return_col=return_col_1,
    )


@app.cell
def _(alpha_sectors, analyzer, df, non_alpha_sectors):
    roic_factor_name_2 = "ROIC_label_Past3Y"
    return_col_2 = "Active_Return_3Y_annlzd"
    print("Alpha Sectors")
    df_alpha_sectors = df.loc[df["GICS Sector"].isin(alpha_sectors)].reset_index(
        drop=True
    )
    _df_performance = analyzer.calculate_mean_returns_for_roic_label(
        df_alpha_sectors, factor_col=roic_factor_name_2, return_col=return_col_2
    )
    analyzer.plot_roic_label_performance(
        df_to_plot=_df_performance,
        roic_factor_name=roic_factor_name_2,
        return_col=return_col_2,
    )
    print("Non-Alpha Sectors")
    df_non_alpha_sectors = df.loc[
        df["GICS Sector"].isin(non_alpha_sectors)
    ].reset_index(drop=True)
    _df_performance = analyzer.calculate_mean_returns_for_roic_label(
        df_non_alpha_sectors, factor_col=roic_factor_name_2, return_col=return_col_2
    )
    analyzer.plot_roic_label_performance(
        df_to_plot=_df_performance,
        roic_factor_name=roic_factor_name_2,
        return_col=return_col_2,
    )
    return df_alpha_sectors, return_col_2


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### α セクターのうち、remian high と drop to low のパフォーマンス（2025）
    """)


@app.cell
def _(df_alpha_sectors, display, pd, return_col_2, roic_utils):
    def display_performance_table(df_target: pd.DataFrame):
        count_by_sector = pd.DataFrame(
            df_target.groupby(["GICS Sector"])["P_SYMBOL"].count().sort_values()
        )
        display(count_by_sector)
        return_mean_col = f"{return_col_2}_mean"
        return_std_col = f"{return_col_2}_std"
        efficiency_col = "Efficiency"
        eff_by_sector = (
            df_target.groupby(["GICS Sector"])
            .agg(
                {
                    return_col_2: [
                        (return_mean_col, roic_utils.clipped_mean),
                        (return_std_col, roic_utils.clipped_std),
                    ]
                }
            )
            .droplevel(0, axis=1)
            .assign(
                **{efficiency_col: lambda x: x[return_mean_col].div(x[return_std_col])}
            )
            .sort_values(by=efficiency_col, ascending=True)
        )
        display(eff_by_sector)

    alpha_sector_and_remain_high = df_alpha_sectors.loc[
        (df_alpha_sectors["ROIC_label_Past3Y"] == "remain high")
        & (df_alpha_sectors["year"] == 2025)
    ]
    alpha_sector_and_drop_to_low = df_alpha_sectors.loc[
        (df_alpha_sectors["ROIC_label_Past3Y"] == "drop to low")
        & (df_alpha_sectors["year"] == 2025)
    ]
    pd.options.display.precision = 3
    print("===== remain high =====")
    display_performance_table(
        alpha_sector_and_remain_high
    )  # 1. GICS Sectorでグループ化
    print("===== drop to low =====")  # type: ignore
    display_performance_table(
        alpha_sector_and_drop_to_low
    )  # 2. aggを使用して、平均(mean)と標準偏差(std)を同時に計算  # type:ignore  # 3. リターンを標準偏差で割ってEfficiencyを計算し、カラムを追加  # 4. Efficiencyでソート


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    -   remain high はベンチマーク負けが目立つ
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. ROIC Dispersion の計測

    -   第一分位の ROIC 中央値が他の分位の ROIC の中央値の何倍かを見る

    -   Financials は ROE、それ以外のアルファファクターは ROIC
    """)


@app.cell
def _(go, pd):
    def calculate_factor_dispersion(
        df: pd.DataFrame, factor_name: str, sector_name: str
    ) -> pd.DataFrame:
        median_factor = (
            df.loc[df["GICS Sector"] == sector_name]
            .groupby(["date", f"{_factor_name}_Rank"])[_factor_name]
            .agg("median")
            .to_frame()
            .reset_index()
            .pivot(index="date", columns=f"{_factor_name}_Rank", values=_factor_name)
            .rename(columns={_factor_name: f"{_factor_name}_Rank_median"})
            .assign(
                Dispersion_Q1_Q2=lambda x: x["rank1"].div(x["rank2"]),
                Dispersion_Q1_Q3=lambda x: x["rank1"].div(x["rank3"]),
                Dispersion_Q1_Q4=lambda x: x["rank1"].div(x["rank4"]),
            )
        )
        return median_factor

    def plot_dispersion(
        median_factor: pd.DataFrame, factor_name: str, sector_name: str
    ):
        fig = go.Figure()
        for col in ["Dispersion_Q1_Q2", "Dispersion_Q1_Q3", "Dispersion_Q1_Q4"]:
            fig.add_trace(
                go.Scatter(
                    x=median_factor.index,
                    y=median_factor[col],
                    mode="lines",
                    name=col,
                    line=dict(width=0.5),
                )
            )
        fig.update_layout(
            title=f"{_factor_name} Dispersion ({sector_name})",
            yaxis_title="dispersion",
            hovermode="x",
            width=1000,
            height=300,
            template="plotly_dark",
            legend=dict(
                yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"
            ),
            margin=dict(l=30, r=30, t=50, b=40),
        )
        fig.show()

    return calculate_factor_dispersion, plot_dispersion


@app.cell
def _(calculate_factor_dispersion, df, pd, plot_dispersion):
    pd.options.display.precision = 2
    # ROIC dispersion

    for sector_name in [
        "Information Technology",
        "Communication Services",
        "Health Care",
        "Industrials",
        "Materials",
        "Consumer Staples",
        "Consumer Discretionary",
    ]:
        median_roic = calculate_factor_dispersion(
            df=df, factor_name="FF_ROIC", sector_name=sector_name
        )
        plot_dispersion(
            median_factor=median_roic, factor_name="FF_ROIC", sector_name=sector_name
        )

    # Financials
    median_roe = calculate_factor_dispersion(
        df=df, factor_name="FF_ROE", sector_name="Financials"
    )
    plot_dispersion(
        median_factor=median_roe, factor_name="FF_ROE", sector_name="Financials"
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. ヒストリカルのグロース性が高かった銘柄
    """)


@app.cell
def _(PerformanceAnalyzer):
    analyzer_1 = PerformanceAnalyzer()
    df_1 = analyzer_1.data_loader()
    return analyzer_1, df_1


@app.cell
def _(alpha_sectors, analyzer_1, df_1):
    df_alpha_sectors_1 = df_1.loc[df_1["GICS Sector"].isin(alpha_sectors)]
    roic_factor_name_3 = "ROIC_label_Past3Y"
    _factor_name = "Factor_Composite_Growth_Score_Rank"
    return_col_3 = "Active_Return_3Y_annlzd"
    _df_performance = analyzer_1.calculate_mean_returns_double_factors(
        df=df_alpha_sectors_1,
        factor1=roic_factor_name_3,
        factor2=_factor_name,
        return_col=return_col_3,
        factor1_rank="remain high",
    )
    analyzer_1.plot_factor_performance(
        df_to_plot=_df_performance, factor_name=_factor_name, return_col=return_col_3
    )


@app.cell
def _(alpha_sectors, analyzer_1, df_1):
    df_alpha_sectors_2 = df_1.loc[df_1["GICS Sector"].isin(alpha_sectors)]
    roic_factor_name_4 = "ROIC_label_Past3Y"
    _factor_name = "Factor_Composite_Growth_Score_Rank"
    return_col_4 = "Active_Return_3Y_annlzd"
    _df_performance = analyzer_1.calculate_mean_returns_double_factors(
        df=df_alpha_sectors_2,
        factor1=roic_factor_name_4,
        factor2=_factor_name,
        return_col=return_col_4,
        factor1_rank="drop to low",
    )
    analyzer_1.plot_factor_performance(
        df_to_plot=_df_performance, factor_name=_factor_name, return_col=return_col_4
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### drop to low の財務スコア
    """)


@app.cell
def _(db_utils, display, financials_db_path, pd, sqlite3):
    tables = db_utils.get_table_names(financials_db_path)
    roic_factor_name_5 = "ROIC_label_Past3Y"
    factor_list = [
        s for s in tables if s.startswith("FF_") and s.endswith("PctRank")
    ] + [roic_factor_name_5]
    TARGET_YEAR = "2025"
    SELECT_PART = f"SELECT `date`, `P_SYMBOL`, `variable`, `value` FROM {{}} WHERE strftime('%Y', date) = '{TARGET_YEAR}'"
    union_all_clauses = [SELECT_PART.format(table) for table in factor_list]
    # 抽出したい年 (2025年と2023年が混ざっていたが、エラーログに合わせて2023年に統一)
    query = " \n    UNION ALL \n    ".join(union_all_clauses)
    # 繰り返し使用する SELECT * WHERE ... 部分
    with sqlite3.connect(financials_db_path) as conn:
        # UNION ALLで結合するための文字列を生成
        df_2 = pd.read_sql(query, con=conn, parse_dates=["date"])
    # クエリ全体を結合
    df_factors = (
        df_2.loc[df_2["variable"] != roic_factor_name_5]
        .reset_index(drop=True)
        .pivot(index=["date", "P_SYMBOL"], columns="variable", values="value")
    )
    df_roic = (
        df_2.loc[df_2["variable"] == roic_factor_name_5]
        .reset_index(drop=True)
        .pivot(index=["date", "P_SYMBOL"], columns="variable", values="value")
    )
    df_final = pd.merge(
        df_factors, df_roic, left_index=True, right_index=True
    ).reset_index()
    display(df_final)
    return df_final, roic_factor_name_5, tables


@app.cell
def _(df_final, display, roic_factor_name_5, tables):
    factors = [s for s in tables if s.startswith("FF_") and s.endswith("PctRank")]
    g = df_final.groupby([roic_factor_name_5])[factors].agg(["mean", "median"])
    display(g)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
