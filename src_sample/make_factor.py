"""
make_factor.py
"""

import sqlite3
from pathlib import Path

# from fred_database_utils import load_data_from_database
import fred_database_utils
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.decomposition import PCA
from tqdm import tqdm
from us_treasury import (
    align_pca_components,
    load_yield_data_from_database,
)


# =======================================================================
def orthogonalize(series_to_clean, regressors):
    """
    series_to_cleanをregressorsで回帰させ、その残差（直交化された系列）を返す。

    Parameters
    ----------
    series_to_clean : pd.Series
        直交化したい元の系列
    regressors : pd.Series or pd.DataFrame
        回帰に使う説明変数

    Returns
    -------
    pd.Series
        直交化された系列（残差）
    """
    # NaNを落とし、インデックスを揃える
    data = pd.concat([series_to_clean, regressors], axis=1).dropna()

    Y = data.iloc[:, 0]
    X = data.iloc[:, 1:]
    X = sm.add_constant(X, has_constant="add")

    model = sm.OLS(Y, X).fit()

    # 元のseries_to_cleanと同じインデックスで残差を返す
    residuals = pd.Series(model.resid, index=Y.index)
    return residuals


# =======================================================================
def orthogonalize_all_descriptors(df_descriptor: pd.DataFrame) -> pd.DataFrame:
    """
    記述子（Descriptor）データフレーム内の各ファクターを直交化する。

    Parameters
    ----------
    df_descriptor : pd.DataFrame
        直交化前のファクターデータを含むデータフレーム。

    Returns
    -------
    pd.DataFrame
        直交化されたファクターデータを含むデータフレーム。
    """
    # 金利ファクター直行化
    for factor in ["Factor_Level", "Factor_Slope", "Factor_Curvature"]:
        df_descriptor[factor] = orthogonalize(
            df_descriptor[f"{factor.replace('Factor_', '')}_Shock"],
            df_descriptor["Factor_Market"],
        )

    # FtoQファクター直行化: マーケットと金利ファクターに対して直行化
    regressors_ftoq = df_descriptor[
        ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature"]
    ]
    df_descriptor["Factor_FtoQ"] = orthogonalize(
        df_descriptor["FtoQ_Shock"], regressors=regressors_ftoq
    )

    # インフレファクター直行化: マーケット、金利ファクター、FtoQファクターに対して直行化
    regressors_inflation = df_descriptor[
        [
            "Factor_Market",
            "Factor_Level",
            "Factor_Slope",
            "Factor_Curvature",
            "Factor_FtoQ",
        ]
    ]
    df_descriptor["Factor_Inflation"] = orthogonalize(
        df_descriptor["Inflation_Shock"], regressors=regressors_inflation
    )

    df_factor = df_descriptor[
        [
            "Factor_Market",
            "Factor_Level",
            "Factor_Slope",
            "Factor_Curvature",
            "Factor_FtoQ",
            "Factor_Inflation",
        ]
    ].dropna(how="any")

    del df_descriptor

    return df_factor


# =======================================================================
def make_descriptor_dataframe(
    fred_db_path: Path, benchmark_db_path: Path
) -> pd.DataFrame:
    """
    FREDおよびベンチマークデータベースからデータを取得し、記述子（Descriptor）データフレームを作成する。

    Parameters
    ----------
    fred_db_path : Path
        FREDデータベースのパス。
    benchmark_db_path : Path
        ベンチマークデータベースのパス。

    Returns
    -------
    pd.DataFrame
        作成された記述子データフレーム。
    """

    # download MSCI Kokusai Index data
    conn = sqlite3.connect(benchmark_db_path)
    return_index = (
        pd.read_sql(
            "SELECT * FROM FG_PRICE_Daily WHERE P_SYMBOL='MSCI Kokusai Index (World ex Japan)' ORDER BY date",
            con=conn,
            parse_dates=["date"],
        )
        .assign(log_value=lambda row: np.log(row["value"]))
        .assign(Return=lambda row: row["log_value"].diff())
        .dropna(ignore_index=True)
    )[["date", "P_SYMBOL", "Return"]]
    conn.close()

    # download DTB3 data(Risk Free Rate)
    conn = sqlite3.connect(fred_db_path)
    risk_free_rate = pd.read_sql(
        "SELECT * FROM DTB3", con=conn, parse_dates=["date"]
    ).assign(DTB3=lambda row: row["DTB3"].div(365 * 100))  # convert to daily data
    conn.close()

    excess_return_index = (
        pd.merge(return_index, risk_free_rate, on=["date"], how="left")
        .dropna(how="any", ignore_index=True)
        .assign(Factor_Market=lambda row: row["Return"].sub(row["DTB3"]))
    )

    # ------ Integrate Factor Data -----
    # yield data
    df_yield = load_yield_data_from_database(db_path=fred_db_path)

    # Flight to Quality Factor
    fred = fred_database_utils.FredDataProcessor()
    df_FtoQ = fred.load_data_from_database(
        db_path=fred_db_path, series_id_list=["BAMLH0A0HYM2", "BAMLC0A0CM"]
    )
    df_FtoQ = (
        pd.pivot(df_FtoQ, index="date", columns="variable", values="value")
        .sort_index()
        .assign(FtoQ=lambda row: row["BAMLH0A0HYM2"].sub(row["BAMLC0A0CM"]))
        .assign(FtoQ_Shock=lambda row: row["FtoQ"].diff())
    ).dropna(how="any")[["FtoQ_Shock"]]

    # Inflation Factor
    df_Inflation = (
        fred.load_data_from_database(db_path=fred_db_path, series_id_list=["T10YIE"])
        .set_index("date")
        .assign(Inflation_Shock=lambda row: row["value"].diff())
        .dropna()
    )[["Inflation_Shock"]]

    # Factor_Market dataにマージする
    df_descriptor = pd.merge(
        excess_return_index.set_index("date")[["Factor_Market"]],
        df_yield,
        left_index=True,
        right_index=True,
    )
    df_descriptor = pd.merge(df_descriptor, df_FtoQ, left_index=True, right_index=True)
    df_descriptor = pd.merge(
        df_descriptor, df_Inflation, left_index=True, right_index=True
    )

    return df_descriptor


# =======================================================================


# date_list = [d.strftime("%Y-%m-%d") for d in df_factor.index.tolist()]

# # PCA and PCA Shock
# df_pca, pca = analyze_yield_curve_pca(
#     df_yield=df_factor[[s for s in df_factor.columns if s.startswith("DGS")]]
# )
# df_pca = df_pca.assign(
#     Level_Shock=lambda row: row["Level"].diff(),
#     Slope_Shock=lambda row: row["Slope"].diff(),
#     Curvature_Shock=lambda row: row["Curvature"].diff(),
# ).dropna()
# # display(df_pca)

# # merge PCA data
# df_factor = pd.merge(df_factor, df_pca, left_index=True, right_index=True)
# df_factor = df_factor[
#     [col for col in df_factor.columns if ("Factor" in col) | ("Shock" in col)]
# ]

# return df_factor, df_pca, pca


# =======================================================================
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

    Parameters
    ----------
    stock_price_series : pd.Series
        個別銘柄の株価時系列
    df_raw_macro : pd.DataFrame
        必要な全てのマクロ指標の元データ
    window_size : int
        ローリングウィンドウのサイズ（営業日数）
    yield_cols : list, optional
        PCAに使用する金利カラム名

    Returns
    -------
    pd.DataFrame
        時間変動ベータ、アルファ、R2の時系列データ
    """
    # 株価リターンと超過リターンを計算
    stock_return = stock_price_series.pct_change()
    daily_rf = df_raw_macro["DTB3"] / 365
    stock_excess_return = (stock_return - daily_rf).rename("Excess_Return")

    # 分析に必要なデータを全て結合
    data = pd.concat([stock_excess_return, df_raw_macro], axis=1)

    # 結果を格納するリスト
    results = []

    # ローリング処理
    for t in tqdm(
        range(window_size, len(data)),
        desc=f"Rolling Betas for {stock_price_series.name}",
    ):
        df = data.iloc[t - window_size : t].copy()
        df.fillna(method="ffill", inplace=True)
        df.dropna(inplace=True)

        # --- ループ内でのファクター生成 ---
        # 1. マーケットファクター
        mkt_return = df["MSCI_KOKUSAI"].pct_change()
        factor_market = (mkt_return - df["daily_rf"]).rename("Factor_Market")

        # 2. 金利ファクター
        pca = PCA(n_components=3)
        pc_scores_raw = pca.fit_transform(df[yield_cols])
        pc_scores_aligned = align_pca_components(pca.components_, pc_scores_raw)
        df_pc = pd.DataFrame(
            pc_scores_aligned,
            index=df[yield_cols].index,
            columns=["Level", "Slope", "Curvature"],
        )

        level_shock = df_pc["Level"].diff()
        slope_shock = df_pc["Slope"].diff()
        curvature_shock = df_pc["Curvature"].diff()

        factor_level = orthogonalize(level_shock, factor_market)
        factor_slope = orthogonalize(slope_shock, factor_market)
        factor_curvature = orthogonalize(curvature_shock, factor_market)

        # 3. FtoQファクター
        ftoq = df["BAMLH0A0HYM2"] - df["BAMLC0A0CM"]
        ftoq_shock = ftoq.diff()
        factor_ftoq = orthogonalize(
            ftoq_shock,
            pd.concat(
                [factor_market, factor_level, factor_slope, factor_curvature], axis=1
            ),
        )

        # 4. インフレファクター
        inflation_shock = df["T10YIE"].diff()
        all_other_factors = pd.concat(
            [factor_market, factor_level, factor_slope, factor_curvature, factor_ftoq],
            axis=1,
        )
        factor_inflation = orthogonalize(inflation_shock, all_other_factors)

        # --- 回帰分析の実行 ---
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
        X.columns = [
            "Market",
            "Level",
            "Slope",
            "Curvature",
            "FtoQ",
            "Inflation",
        ]  # カラム名を簡潔に

        analysis_data = pd.concat([df["Excess_Return"], X], axis=1).dropna()

        if len(analysis_data) < 50:
            continue  # データ不足の場合はスキップ

        Y_reg = analysis_data["Excess_Return"]
        X_reg = sm.add_constant(analysis_data.iloc[:, 1:])

        model = sm.OLS(Y_reg, X_reg).fit()

        # 結果を辞書として保存
        res = model.params.to_dict()
        res["r_squared_adj"] = model.rsquared_adj
        res["date"] = df.index[-1]
        results.append(res)

    # 結果をDataFrameに変換
    beta_history = pd.DataFrame(results).set_index("date")
    beta_history = beta_history.rename(columns={"const": "alpha"})

    return beta_history
