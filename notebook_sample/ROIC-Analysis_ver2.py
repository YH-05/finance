import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # `ROIC-Analysis_ver1.ipynb`

    -   ROIC 含めたファクターのパフォーマンス分析用 notebook
    -   ROIC-Preprocessing でデータの前処理を行ったうえでこの notebook で分析
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import os
    import sqlite3
    import sys
    import warnings
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    from dotenv import load_dotenv
    from scipy.stats import spearmanr

    warnings.simplefilter("ignore")
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

    financials_db_path = INDEX_DIR / "Financials_and_Price.db"
    factset_index_db_path = FACTSET_INDEX_CONSTITUENTS_DIR / "Index_Constituents.db"
    bloomberg_index_db_path = BLOOMBERG_ROOT_DIR / "Index_Price_and_Returns.db"
    bloomberg_valuation_db_path = BLOOMBERG_ROOT_DIR / "Valuation.db"
    bpm_db_path = BPM_ROOT_DIR / "Index_Constituents.db"
    return (
        UNIVERSE_CODE,
        db_utils,
        factset_index_db_path,
        financials_db_path,
        go,
        np,
        pd,
        roic_utils,
        spearmanr,
        sqlite3,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 0. データ用意

    GICS セクター、ウェイトなどのデータフレームとファクターのデータフレームをそれぞれの DB から引っ張る -> MERGE
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    financials_db_path,
    pd,
    sqlite3,
):
    with sqlite3.connect(factset_index_db_path) as _conn:
        _df_weight = pd.read_sql(
            f"SELECT `date`, `P_SYMBOL`, `SEDOL`, `FG_COMPANY_NAME`, `GICS Sector`, `GICS Industry Group`, `Weight (%)` FROM {UNIVERSE_CODE}",
            con=_conn,
            parse_dates=["date"],
        )
    factor_list = [
        "FF_ROIC",
        "FF_ROIC_PctRank",
        "FF_ROIC_Rank",
        "FF_ROE",
        "FF_ROE_PctRank",
        "FF_ROE_Rank",
        "Active_Return_1M_annlzd",
        "Active_Return_3M_annlzd",
        "Active_Return_6M_annlzd",
        "Active_Return_12M_annlzd",
        "Active_Return_3Y_annlzd",
        "Active_Return_5Y_annlzd",
    ]
    _query = "\n    SELECT * FROM {}\n".format(
        "\n    UNION ALL\n    SELECT * FROM ".join(factor_list)
    )
    with sqlite3.connect(financials_db_path) as _conn:
        df_factor = pd.read_sql(_query, parse_dates=["date"], con=_conn).assign(
            date=lambda x: pd.to_datetime(x["date"]) + pd.offsets.MonthEnd(0)
        )
        df_factor = pd.pivot(
            df_factor, index=["date", "P_SYMBOL"], columns="variable", values="value"
        )
    df = pd.merge(_df_weight, df_factor, on=["date", "P_SYMBOL"], how="outer").dropna(
        subset=["Weight (%)"], ignore_index=True
    )
    # 方法1: join()を使用
    display(df)
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. セクター分析
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1-1. ROIC Dispersion

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
        _fig = go.Figure()
        for col in ["Dispersion_Q1_Q2", "Dispersion_Q1_Q3", "Dispersion_Q1_Q4"]:
            _fig.add_trace(
                go.Scatter(
                    x=median_factor.index,
                    y=median_factor[col],
                    mode="lines",
                    name=col,
                    line=dict(width=0.5),
                )
            )
        _fig.update_layout(
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
        _fig.show()

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


@app.cell
def _(df, factor, go, np, pd):
    g_median = (
        pd.DataFrame(df.groupby(["date", "GICS Sector"])[factor].agg("median"))
        .reset_index()
        .pivot(index="date", columns="GICS Sector", values=factor)
        .dropna(how="all")
    )
    g_std = (
        pd.DataFrame(df.groupby(["date", "GICS Sector"])[factor].agg(np.std))
        .reset_index()
        .pivot(index="date", columns="GICS Sector", values=factor)
        .dropna(how="all")
    )
    _fig = go.Figure()
    for col in g_median.columns:
        _fig.add_trace(
            go.Scatter(
                x=g_median.index,
                y=g_median[col],
                mode="lines",
                name=col,
                line=dict(width=0.5),
            )
        )
    _fig.update_layout(
        title=f"GICS Sector Median {factor}",
        xaxis_title="date",
        yaxis_title=factor,
        hovermode="x",
        width=1000,
        height=500,
        template="plotly_dark",
        legend=dict(yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"),
        margin=dict(l=30, r=30, t=50, b=40),
    )
    _fig.show()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Performance
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1-1. IC
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1-1-1. Growth Factor
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    financials_db_path,
    np,
    pd,
    spearmanr,
    sqlite3,
):
    # 各日付でICを計算
    def calc_ic(group, factor_name: str, return_name: str):
        valid = group[[_factor_name, return_name]].dropna()
        if len(valid) < 5:  # 最小サンプル数
            return pd.Series(
                {"IC": np.nan, "Number_of_Securities": len(valid), "p_value": np.nan}
            )
        ic, p_value = spearmanr(valid[_factor_name], valid[return_name])
        return pd.Series(
            {"IC": ic, "Number_of_Securities": len(valid), "p_value": p_value}
        )

    def calculate_IC(
        factor_name: str, return_name: str, calculate_by_sector: bool = True
    ) -> pd.DataFrame:
        """
        セクター中立パーセンタイルランクファクターからICを計算

        Parameters:
        -----------
        factor_name : str
            例: "FF_SALES_CAGR_3Y_PctRank"
            前提: DBにはセクター内パーセンタイルランク(0-1)が格納されている
        return_name : str
            例: "Forward_Return_12M"
        calculate_by_sector : bool, default=True
            True: セクター別にICを計算（セクターごとの時系列IC）
            False: ユニバース全体でICを計算（全銘柄の時系列IC）
        min_samples : int, default=5
            IC計算の最小サンプル数

        Returns:
        --------
        ic_df : DataFrame
            columns: date, IC, Number_of_Securities, p_value, GICS Sector,
                     factor_name, return_name, aggregation_level
        """
        with sqlite3.connect(financials_db_path) as _conn:
            df_pct_rank = (
                pd.read_sql(
                    f"SELECT * FROM {_factor_name}", con=_conn, parse_dates=["date"]
                )
                .assign(
                    date=lambda x: pd.to_datetime(x["date"]) + pd.offsets.MonthEnd(0)
                )
                .rename(columns={"value": _factor_name})
                .drop(columns=["variable"])
            )
            df_return = (
                pd.read_sql(
                    f"SELECT * FROM {return_name}", con=_conn, parse_dates=["date"]
                )
                .assign(
                    date=lambda x: pd.to_datetime(x["date"]) + pd.offsets.MonthEnd(0)
                )
                .rename(columns={"value": return_name})
                .drop(columns=["variable"])
            )
        df = pd.merge(df_pct_rank, df_return, on=["date", "P_SYMBOL"], how="outer")
        df = pd.merge(df_members, df, on=["date", "P_SYMBOL"], how="left").dropna(
            subset=["Weight (%)", _factor_name, return_name],
            how="any",
            ignore_index=True,
        )
        if calculate_by_sector:
            ic_dfs = []
            for _sector in df["GICS Sector"].unique():
                _df_slice = df.loc[df["GICS Sector"] == _sector].copy()
                ic_df = (
                    _df_slice.groupby(["date"])
                    .apply(calc_ic, _factor_name, return_name)
                    .reset_index()
                    .dropna(subset=["IC"], ignore_index=True)
                )
                ic_df["GICS Sector"] = _sector
                ic_dfs.append(ic_df)
            ic_df = pd.concat(ic_dfs, ignore_index=True)
            aggregation = "sector"
        else:
            ic_df = (
                df.groupby("date")
                .apply(calc_ic, _factor_name, return_name)
                .reset_index()
                .dropna(subset=["IC"], ignore_index=True)
            )
            ic_df["GICS Sector"] = "Universe"
            aggregation = "universe"
        ic_df = ic_df.assign(
            factor_name=_factor_name,
            return_name=return_name,
            aggregation_level=aggregation,
        )
        return ic_df

    with sqlite3.connect(factset_index_db_path) as _conn:
        _query = f"\n        SELECT\n            `date`, `P_SYMBOL`, `GICS Sector`, `GICS Industry Group`, `Weight (%)`\n        FROM\n            {UNIVERSE_CODE}\n        ORDER BY\n            date\n    "
        df_members = pd.read_sql(_query, parse_dates=["date"], con=_conn)
    return_name = "Forward_Return_12M"
    base_data = "FF_SALES"
    factor_name_list = [
        f"{base_data}_QoQ_PctRank",
        f"{base_data}_YoY_PctRank",
        f"{base_data}_CAGR_3Y_PctRank",
    ]
    ic_dfs = [
        calculate_IC(_factor_name, return_name, calculate_by_sector=False)
        for _factor_name in factor_name_list
    ]
    ic_df = pd.concat(ic_dfs, ignore_index=True)
    display(ic_df.tail())
    ic_dfs_by_sector = [
        calculate_IC(_factor_name, return_name, calculate_by_sector=True)
        for _factor_name in factor_name_list
    ]
    ic_df_by_sector = pd.concat(ic_dfs_by_sector, ignore_index=True)
    display(
        ic_df_by_sector.loc[
            ic_df_by_sector["GICS Sector"] == "Information Technology"
        ].tail(36)
    )  # f"{base_data}_CAGR_5Y_PctRank",
    return base_data, ic_df, ic_df_by_sector


@app.cell
def _(display, ic_df_by_sector):
    display(
        ic_df_by_sector.loc[
            (ic_df_by_sector["GICS Sector"] == "Information Technology")
            & (ic_df_by_sector["date"] >= "2024-01-01")
            & (ic_df_by_sector["factor_name"].str.contains("YoY"))
        ].tail(36)
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### IC の統計計算
    """)


@app.cell
def _(display, ic_df_by_sector, pd):
    ic_df_by_sector_copy = ic_df_by_sector.copy()
    ic_df_by_sector_copy["year"] = pd.to_datetime(ic_df_by_sector_copy["date"]).dt.year
    pivot_ic = ic_df_by_sector_copy.pivot_table(
        index=["year", "GICS Sector"],
        columns="factor_name",
        values="IC",
        aggfunc="mean",
    ).reset_index()

    display(pivot_ic.loc[pivot_ic["GICS Sector"] == "Information Technology"].round(3))


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Plot
    """)


@app.cell
def _(UNIVERSE_CODE, base_data, go, ic_df):
    _fig = go.Figure()
    for _factor_name in ic_df["factor_name"].unique():
        _df_slice = ic_df.loc[ic_df["factor_name"] == _factor_name].sort_values(
            "date", ignore_index=True
        )
        _fig.add_trace(
            go.Scatter(
                x=_df_slice["date"],
                y=_df_slice["IC"],
                mode="lines",
                line=dict(width=0.8),
                name=_factor_name,
            )
        )
    _fig.update_yaxes(dtick=0.1)
    _fig.update_layout(
        title=f"{UNIVERSE_CODE} IC | {base_data}",
        width=1000,
        height=350,
        template="plotly_dark",
        hovermode="x",
        legend=dict(yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"),
        margin=dict(l=30, r=30, t=50, b=30),
    )
    _fig.show()  # fig.add_trace(  #     go.Scatter(  #         x=df_slice["date"],  #         y=df_slice["p_value"],  #         mode="lines",  #         line=dict(width=0.8, dash="dash"),  #         name=f"p value ({factor_name})",  #     )  # )


@app.cell
def _(base_data, go, ic_df_by_sector):
    # for sector in ic_df_by_sector["GICS Sector"].unique():
    for _sector in ["Information Technology"]:
        ic_df_sector = ic_df_by_sector.query("`GICS Sector`==@sector")
        _fig = go.Figure()
        for _factor_name in ic_df_sector["factor_name"].unique():
            _df_slice = ic_df_sector.loc[
                ic_df_sector["factor_name"] == _factor_name
            ].sort_values("date", ignore_index=True)
            _fig.add_trace(
                go.Scatter(
                    x=_df_slice["date"],
                    y=_df_slice["IC"],
                    mode="lines",
                    line=dict(width=0.8),
                    name=_factor_name,
                )
            )
        _fig.update_yaxes(dtick=0.1)
        _fig.update_layout(
            title=f"{_sector} IC | {base_data}",
            width=1000,
            height=350,
            template="plotly_dark",
            hovermode="x",
            legend=dict(
                yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"
            ),
            margin=dict(l=30, r=30, t=50, b=30),
        )
        _fig.show()  # fig.add_trace(  #     go.Scatter(  #         x=df_slice["date"],  #         y=df_slice["p_value"],  #         mode="lines",  #         line=dict(width=0.8, dash="dash"),  #         name=f"p value ({factor_name})",  #     )  # )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1-2. ROIC label 期間別リターン
    """)


@app.cell
def _(db_utils, display, financials_db_path):
    # テーブル確認

    table_names = db_utils.get_table_names(db_path=financials_db_path)
    display(sorted([s for s in table_names if "annlzd" in s]))


@app.cell
def _(
    UNIVERSE_CODE,
    db_utils,
    display,
    factset_index_db_path,
    financials_db_path,
    np,
    pd,
    sqlite3,
):
    _query = f"\n    SELECT\n        `date`, `Universe`, `Universe_code_BPM`, `P_SYMBOL`, `Name`, `FG_COMPANY_NAME`, `Asset ID`, `Asset ID Type`, `Country`,\n        `GICS Sector`, `GICS Industry`, `GICS Industry Group`, `GICS Sub-Industry`, `Holdings`, `Weight (%)`, `Mkt Value`\n    FROM\n        {UNIVERSE_CODE}\n"
    with sqlite3.connect(factset_index_db_path) as _conn:
        _df_weight = pd.read_sql(_query, con=_conn, parse_dates=["date"])
    union_queries = ["SELECT * FROM ROIC_label_Past5Y"]
    union_queries.extend(
        [
            f"SELECT * FROM '{table}'"
            for table in db_utils.get_table_names(db_path=financials_db_path)
            if "annlzd" in table
        ]
    )
    _query = " UNION ALL ".join(union_queries)
    with sqlite3.connect(financials_db_path) as _conn:
        data = pd.pivot(
            pd.read_sql(_query, con=_conn, parse_dates=["date"]),
            index=["date", "P_SYMBOL"],
            columns="variable",
            values="value",
        ).reset_index()
    df_1 = (
        pd.merge(_df_weight, data, on=["date", "P_SYMBOL"], how="outer")
        .dropna(subset=["Weight (%)"])
        .fillna(np.nan)
    )
    display(df_1)
    return (df_1,)


@app.cell
def _(df_1, display, pd, roic_utils):
    pd.options.display.precision = 2
    for _sector in df_1["GICS Sector"].unique():
        _df_slice = df_1.loc[
            (df_1["date"] >= "2015-01-01") & (df_1["GICS Sector"] == _sector)
        ]
        return_cols = [
            "Return_1M_annlzd",
            "Return_3M_annlzd",
            "Return_6M_annlzd",
            "Return_12M_annlzd",
            "Return_3Y_annlzd",
            "Return_5Y_annlzd",
            "Forward_Return_1M_annlzd",
            "Forward_Return_3M_annlzd",
            "Forward_Return_6M_annlzd",
            "Forward_Return_12M_annlzd",
            "Forward_Return_3Y_annlzd",
            "Forward_Return_5Y_annlzd",
        ]
        g = (
            _df_slice.groupby(["ROIC_label_Past5Y"])[return_cols]
            .apply(roic_utils.clipped_mean, 5.0)
            .mul(100)
        )
        print(_sector)
        display(g)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
