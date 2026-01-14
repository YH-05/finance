import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Reference

    -   [FRED](https://fred.stlouisfed.org/searchresults/?st=ICE%20BofA)
    -   [Gemini](https://gemini.google.com/app/a0cd28b75b80675e?utm_source=app_launcher&utm_medium=owned&utm_campaign=base_all)
    -   [Gemini](https://gemini.google.com/app/0da10f614b7e7434?utm_source=app_launcher&utm_medium=owned&utm_campaign=base_all)
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # MSCI Kokusai Constituents Macro Factor Model Ver3

    ## 回帰モデル

    $$
    R_i - R_f = \alpha
    + \beta_{\mathrm{mkt}}F_{\mathrm{mkt}}
    + \left[\beta_{\mathrm{level}}F_{\mathrm{level}}
    + \beta_{\mathrm{slope}}F_{\mathrm{slope}}
    + \beta_{\mathrm{curvature}}F_{\mathrm{curvature}}\right]
    + \beta_{X}F_{X}
    + \beta_{\mathrm{Inflation}}F_{\mathrm{Inflation}}
    + \epsilon_{i}
    $$

    -   $R_i$: 個別銘柄リターン
    -   $R_f$: リスクフリーレート（米国 3 ヶ月物財務省短期証券 TBill）、日次リターン計測用。FRED シリーズは`DTB3`。長期の場合は 10 年物財務省長期証券を使用。
        -   年率ベースであるため、日次に変換。
    -   $\beta_{\mathrm{mkt}}$: マーケット(MSCI Kokusai)ベータ。リスクフリーレートからの指数の超過収益を使う($R_{\mathrm{mkt}} - R_f$)。

    ### 金利ベータ

    -   $\beta_{\mathrm{level}}$: US 金利データを主成分分析したのちの第 1 主成分(level)によるベータ
    -   $\beta_{\mathrm{slope}}$: 第 2 主成分(slope)によるベータ
    -   $\beta_{\mathrm{curvature}}$: 第 3 主成分(curvature)によるベータ

    ### クレジット orVIX ベータ: $\beta_{X}$

    次の 1 または 2 を使用。

    1.  $\beta_{\mathrm{FtoQ}}$: Flight to Quality ファクターによるベータ。

        定義は米国ハイイールド債スプレッド（FRED シリーズ:`BAMLH0A0HYM2` ）と米国投資適格級スプレッド（FRED シリーズ`BAMLC0A0CM`）の差分。"質への逃避"をモデル化したもの。このファクターが拡大する時、安全な投資適格債に比べて、リスクの高いハイイールド債を極端に避けている（+より高いリスクプレミアムを要求している）ことを意味する。これは市場の恐怖感を抽出したファクターとなりうる。

        企業の倒産リスクをどれだけ深刻に捉えているかを直接反映する。実際の売買の**行動の結果**が FtoQ ファクターに現れる。また、リスクの識別・選別という情報を含み、単にリスクオフになっているだけでなく、**質の低い社債が質の高い社債に比べてどれだけ余計に売られているか**を定量化している。

    2.  $\beta_{\mathrm{VIX}}$: VIX 指数によるベータ。FRED シリーズは`VIXCLS`。

        S&P 500 の株価が将来どれだけ大きく変動するかという市場予想を反映する。これは企業の信用リスクだけでなく、地政学リスクや政治不安といった不確実性にも反応する。VIX は将来の変動を予想してプットオプションなどを買う行動の結果である。よって VIX が FtoQ に先行して急騰することもある。

    ### インフレベータ

    -   $\beta_{\mathrm{Inflation}}$: インフレファクターベータ。5 年または 10 年ブレークイーブン・インフレ率を使う。
        -   FRED シリーズは`T5YIE`（5 年） or `T10YIE`（10 年）。

    ### 直行化

    [Google Document を参照](https://docs.google.com/document/d/1OJ1hipUb0jYnwNXVZmq4FhBTmOqx0nSz0VpI-uF8PRQ/edit?tab=t.0)
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo
    import os
    import sqlite3
    import warnings
    from pathlib import Path

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns
    import statsmodels.api as sm
    from fred_database_utils import (
        get_fred_ids_from_file,
        load_data_from_database,
        store_fred_database,
    )
    from make_factor import (
        make_descriptor_dataframe,
        orthogonalize,
        orthogonalize_all_descriptors,
    )
    from sklearn.decomposition import PCA
    from tqdm import tqdm
    from us_treasury import (
        analyze_yield_curve_pca,
        load_yield_data_from_database,
        plot_loadings_and_explained_variance,
    )

    warnings.simplefilter("ignore")
    Q_DIR = Path().cwd().parent
    DATA_DIR = Q_DIR / "data" / "MSCI_KOKUSAI"
    PRJ_DIR = Q_DIR / "A_001"
    BM_DIR = Q_DIR / "data/Factset/Benchmark"
    FRED_DIR = Q_DIR / "data/FRED"
    print(f"FRED directory: {FRED_DIR}")
    FRED_API = os.getenv("FRED_API_KEY")
    series_id_list = get_fred_ids_from_file(FRED_DIR / "fred_series.json")
    _db_path = FRED_DIR / "FRED.db"
    # Factset Benchmark directory
    # Prepare FRED Data
    store_fred_database(
        db_path=_db_path, series_id_list=series_id_list, FRED_API=FRED_API
    )
    return (
        BM_DIR,
        DATA_DIR,
        FRED_DIR,
        PCA,
        analyze_yield_curve_pca,
        load_data_from_database,
        load_yield_data_from_database,
        make_descriptor_dataframe,
        np,
        orthogonalize,
        orthogonalize_all_descriptors,
        pd,
        plot_loadings_and_explained_variance,
        plt,
        sm,
        sns,
        sqlite3,
        tqdm,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prepare Data
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Return data
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### MSCI Kokusai Constituents
    """)


@app.cell
def _(DATA_DIR, display, np, pd, sqlite3):
    _db_path = DATA_DIR / "MSCI_KOKUSAI_Price_Daily.db"
    _conn = sqlite3.connect(_db_path)
    return_secs = pd.read_sql(
        "SELECT * FROM FG_PRICE_Daily ORDER BY date", con=_conn, parse_dates=["date"]
    ).assign(log_value=lambda row: np.log(row["value"]))
    return_secs["Return"] = return_secs.groupby("P_SYMBOL")["log_value"].diff()
    return_secs = return_secs[["date", "P_SYMBOL", "Return"]].dropna(
        how="any", ignore_index=True
    )
    display(return_secs)
    return (return_secs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Calculate Excess Return
    """)


@app.cell
def _(FRED_DIR, display, pd, return_secs, sqlite3):
    _db_path = FRED_DIR / "FRED.db"
    _conn = sqlite3.connect(_db_path)
    risk_free_rate = pd.read_sql(
        "SELECT * FROM DTB3", con=_conn, parse_dates=["date"]
    ).assign(DTB3=lambda row: row["DTB3"].div(365 * 100))
    _conn.close()
    print("Risk free rate(DTB3)")
    display(risk_free_rate)
    excess_return_secs = (
        pd.merge(return_secs, risk_free_rate, on=["date"], how="left")
        .dropna(how="any", ignore_index=True)
        .assign(Excess_Return=lambda row: row["Return"].sub(row["DTB3"]))
    )  # convert to daily data
    print("Excess return of securities")
    display(excess_return_secs)
    return (excess_return_secs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Integrate factor data

    #### Market Factor, Yield, FtoQ, Inflation

    <!--
    #### 金利変動幅に対して PCA(Leve, Slope, Curvature) -->
    """)


@app.cell
def _(
    FRED_DIR,
    analyze_yield_curve_pca,
    display,
    excess_return_index,
    load_data_from_database,
    load_yield_data_from_database,
    pd,
    plot_loadings_and_explained_variance,
):
    # yield data
    _db_path = FRED_DIR / "FRED.db"
    df_yield = load_yield_data_from_database(db_path=_db_path)
    df_FtoQ = load_data_from_database(
        db_path=_db_path, series_id_list=["BAMLH0A0HYM2", "BAMLC0A0CM"]
    )
    # Flight to Quality Factor
    df_FtoQ = (
        pd.pivot(df_FtoQ, index="date", columns="variable", values="value")
        .sort_index()
        .assign(FtoQ=lambda row: row["BAMLH0A0HYM2"].sub(row["BAMLC0A0CM"]))
        .assign(FtoQ_Shock=lambda row: row["FtoQ"].diff())
        .dropna(how="any")[["FtoQ_Shock"]]
    )
    df_Inflation = (
        load_data_from_database(db_path=_db_path, series_id_list=["T10YIE"])
        .set_index("date")
        .assign(Inflation_Shock=lambda row: row["value"].diff())
        .dropna()[["Inflation_Shock"]]
    )
    df_factor = pd.merge(
        excess_return_index.set_index("date")[["Factor_Market"]],
        df_yield,
        left_index=True,
        right_index=True,
    )
    df_factor = pd.merge(df_factor, df_FtoQ, left_index=True, right_index=True)
    df_factor = pd.merge(df_factor, df_Inflation, left_index=True, right_index=True)
    _date_list = [d.strftime("%Y-%m-%d") for d in df_factor.index.tolist()]
    _start_date = _date_list[0]
    _end_date = _date_list[500]
    df_factor = df_factor.loc[_start_date:_end_date]
    display(df_factor.head())
    # Inflation Factor
    display(df_factor.tail())
    plot_loadings_and_explained_variance(
        df_yield=df_factor[[s for s in df_factor.columns if s.startswith("DGS")]]
    )
    _df_pca, _pca = analyze_yield_curve_pca(
        df_yield=df_factor[[s for s in df_factor.columns if s.startswith("DGS")]]
    )
    _df_pca = _df_pca.assign(
        Level_Shock=lambda row: row["Level"].diff(),
        Slope_Shock=lambda row: row["Slope"].diff(),
        Curvature_Shock=lambda row: row["Curvature"].diff(),
    ).dropna()
    df_factor = pd.merge(df_factor, _df_pca, left_index=True, right_index=True)
    df_factor = df_factor[
        [col for col in df_factor.columns if ("Factor" in col) | ("Shock" in col)]
    ]
    # Factor_Market dataにマージする
    # ====== 分析期間を指定 =======
    # Check: loading and contribution
    # PCA and PCA Shock
    # display(df_pca)
    # merge PCA data
    # plot_us_interest_rates_and_spread(
    #     db_path=db_path, start_date=start_date, end_date=end_date
    # )
    display(df_factor)
    return (df_factor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 直行化
    """)


@app.cell
def _(df_factor, display, orthogonalize):
    # 金利ファクター直行化
    df_factor["Factor_Level"] = orthogonalize(
        df_factor["Level_Shock"], df_factor["Factor_Market"]
    )
    df_factor["Factor_Slope"] = orthogonalize(
        df_factor["Slope_Shock"], df_factor["Factor_Market"]
    )
    df_factor["Factor_Curvature"] = orthogonalize(
        df_factor["Curvature_Shock"], df_factor["Factor_Market"]
    )
    regressors_ftoq = df_factor[
        ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature"]
    ]
    df_factor["Factor_FtoQ"] = orthogonalize(
        df_factor["FtoQ_Shock"], regressors=regressors_ftoq
    )
    regressors_inflation = df_factor[
        [
            "Factor_Market",
            "Factor_Level",
            "Factor_Slope",
            "Factor_Curvature",
            "Factor_FtoQ",
        ]
    ]
    df_factor["Factor_Inflation"] = orthogonalize(
        df_factor["Inflation_Shock"], regressors=regressors_inflation
    )
    df_factor_1 = df_factor[
        [
            "Factor_Market",
            "Factor_Level",
            "Factor_Slope",
            "Factor_Curvature",
            "Factor_FtoQ",
            "Factor_Inflation",
        ]
    ].dropna(how="any")
    display(df_factor_1)
    print("=== Correlation Matrix ===")
    # FtoQファクター直行化: マーケットと金利ファクターに対して直行化
    # インフレファクター直行化: マーケット、金利ファクター、FtoQファクターに対して直行化
    # ファクター間の相関行列
    display(df_factor_1.corr().round(4))
    return (df_factor_1,)


@app.cell
def _(df_factor_1, display, excess_return_secs, pd):
    security = "BKNG-US"
    excess_return_security = excess_return_secs.loc[
        excess_return_secs["P_SYMBOL"] == security, ["date", "Excess_Return"]
    ].set_index("date")
    display(excess_return_security)
    df_data = pd.merge(
        excess_return_security, df_factor_1, left_index=True, right_index=True
    )
    display(df_data)


@app.cell
def _(PCA, orthogonalize, pd, sm, tqdm):
    from us_treasury import align_pca_components

    def calculate_rolling_betas(
        stock_price_series,
        df_raw_macro,
        window_size,
        yield_cols=[
            "DGS1MO",
            "DGS3MO",
            "DGS6MO",
            "DGS1",
            "DGS2",
            "DGS3",
            "DGS5",
            "DGS7",
            "DGS10",
            "DGS20",
            "DGS30",
        ],
    ):
        """
        ローリングウィンドウ内でファクター生成（PCA, 直交化）と回帰分析を全て実行し、
        時系列ベータを算出する統合関数。

        :param stock_price_series: pd.Series - 個別銘柄の株価時系列
        :param df_raw_macro: pd.DataFrame - 必要な全てのマクロ指標の元データ
        :param window_size: int - ローリングウィンドウのサイズ（営業日数）
        :param yield_cols: list - PCAに使用する金利カラム名
        :return: pd.DataFrame - 時間変動ベータ、アルファ、R2の時系列データ
        """
        stock_return = stock_price_series.pct_change()
        daily_rf = df_raw_macro["DTB3"] / 365
        stock_excess_return = (stock_return - daily_rf).rename("Excess_Return")
        data = pd.concat([stock_excess_return, df_raw_macro], axis=1)
        results = []
        for t in tqdm(
            range(window_size, len(data)),
            desc=f"Rolling Betas for {stock_price_series.name}",
        ):
            df = data.iloc[t - window_size : t].copy()
            df.fillna(method="ffill", inplace=True)
            df.dropna(inplace=True)
            mkt_return = df["MSCI_KOKUSAI"].pct_change()
            factor_market = (mkt_return - df["daily_rf"]).rename("Factor_Market")
            _pca = PCA(n_components=3)
            pc_scores_raw = _pca.fit_transform(df[yield_cols])
            pc_scores_aligned = align_pca_components(_pca.components_, pc_scores_raw)
            df_pc = pd.DataFrame(
                pc_scores_aligned,
                index=df[yield_cols].index,
                columns=["Level", "Slope", "Curvature"],
            )
            level_shock = df_pc["Level"].diff()
            slope_shock = df_pc["Slope"].diff()
            curvature_shock = df_pc["Curvature"].diff()
            factor_level = orthogonalize(
                level_shock, factor_market
            )  # 株価リターンと超過リターンを計算
            factor_slope = orthogonalize(slope_shock, factor_market)
            factor_curvature = orthogonalize(curvature_shock, factor_market)
            ftoq = df["BAMLH0A0HYM2"] - df["BAMLC0A0CM"]
            ftoq_shock = ftoq.diff()
            factor_ftoq = orthogonalize(
                ftoq_shock,
                pd.concat(
                    [factor_market, factor_level, factor_slope, factor_curvature],
                    axis=1,
                ),
            )  # 分析に必要なデータを全て結合
            inflation_shock = df["T10YIE"].diff()
            all_other_factors = pd.concat(
                [
                    factor_market,
                    factor_level,
                    factor_slope,
                    factor_curvature,
                    factor_ftoq,
                ],
                axis=1,
            )
            factor_inflation = orthogonalize(
                inflation_shock, all_other_factors
            )  # 結果を格納するリスト
            X = pd.concat(
                [
                    factor_market,
                    factor_level,
                    factor_slope,
                    factor_curvature,
                    factor_ftoq,
                    factor_inflation,
                ],
                axis=1,
            )
            X.columns = ["Market", "Level", "Slope", "Curvature", "FtoQ", "Inflation"]
            analysis_data = pd.concat(
                [df["Excess_Return"], X], axis=1
            ).dropna()  # ローリング処理
            if len(analysis_data) < 50:
                continue
            Y_reg = analysis_data["Excess_Return"]
            X_reg = sm.add_constant(analysis_data.iloc[:, 1:])
            model = sm.OLS(Y_reg, X_reg).fit()
            res = model.params.to_dict()
            res["r_squared_adj"] = model.rsquared_adj
            res["date"] = df.index[-1]
            results.append(res)  # --- ループ内でのファクター生成 ---
        beta_history = pd.DataFrame(results).set_index(
            "date"
        )  # 1. マーケットファクター
        beta_history = beta_history.rename(columns={"const": "alpha"})
        return beta_history  # 2. 金利ファクター  # 3. FtoQファクター  # 4. インフレファクター  # --- 回帰分析の実行 ---  # カラム名を簡潔に  # データ不足の場合はスキップ  # 結果を辞書として保存  # 結果をDataFrameに変換


@app.cell
def _(
    BM_DIR,
    FRED_DIR,
    analyze_yield_curve_pca,
    display,
    make_descriptor_dataframe,
    orthogonalize_all_descriptors,
    pd,
    plot_loadings_and_explained_variance,
):
    fred_db_path = FRED_DIR / "FRED.db"
    benchmark_db_path = BM_DIR / "BM_Price_Daily.db"
    df_descriptor = make_descriptor_dataframe(
        fred_db_path=fred_db_path, benchmark_db_path=benchmark_db_path
    )
    _date_list = [d.strftime("%Y-%m-%d") for d in df_descriptor.index.tolist()]
    start_index = 100
    _start_date = _date_list[start_index]
    _end_date = _date_list[start_index + 252 * 2]
    df_descriptor = df_descriptor.loc[_start_date:_end_date]
    display(df_descriptor.head())
    display(df_descriptor.tail())
    plot_loadings_and_explained_variance(
        df_yield=df_descriptor[
            [s for s in df_descriptor.columns if s.startswith("DGS")]
        ]
    )
    _df_pca, _pca = analyze_yield_curve_pca(
        df_yield=df_descriptor[
            [s for s in df_descriptor.columns if s.startswith("DGS")]
        ]
    )
    _df_pca = _df_pca.assign(
        Level_Shock=lambda row: row["Level"].diff(),
        Slope_Shock=lambda row: row["Slope"].diff(),
        Curvature_Shock=lambda row: row["Curvature"].diff(),
    ).dropna()
    df_descriptor = pd.merge(df_descriptor, _df_pca, left_index=True, right_index=True)
    df_descriptor = df_descriptor[
        [col for col in df_descriptor.columns if ("Factor" in col) | ("Shock" in col)]
    ]
    display(df_descriptor)
    df_factor_2 = orthogonalize_all_descriptors(df_descriptor=df_descriptor)
    display(df_factor_2)
    return (df_factor_2,)


@app.cell
def _(df_factor_2, display, plt, sns):
    display(df_factor_2.corr().round(4))
    fig, axes = plt.subplots(6, 1, figsize=(10, 8), tight_layout=True, sharex=True)
    for i, col in enumerate(df_factor_2.columns.tolist()):
        ax = axes[i]
        sns.lineplot(
            df_factor_2, x=df_factor_2.index, y=df_factor_2[col], alpha=0.7, ax=ax
        )
        ax.set_ylabel(col)
    plt.show()


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
