import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    [Gemini](https://gemini.google.com/app/a0cd28b75b80675e?utm_source=app_launcher&utm_medium=owned&utm_campaign=base_all)
    """)
    return


@app.cell
def _():
    import pandas as pd
    import numpy as np
    import statsmodels.api as sm
    from sklearn.decomposition import PCA

    # ================================================================================
    # 0. 準備: ダミーデータの作成とヘルパー関数の定義
    # ================================================================================

    # --- ダミーデータの作成（実際にはこの部分をご自身のデータ読み込みに置き換えてください）---
    # 分析期間を設定
    dates = pd.to_datetime(
        pd.date_range(start="2010-01-01", end="2023-12-31", freq="B")
    )  # 営業日ベース

    # 各種マクロ経済指標の時系列データをランダムに生成
    data = {
        "MSCI_KOKUSAI": np.random.randn(len(dates)).cumsum() + 100,
        "DTB3": np.random.rand(len(dates)) * 2 + 0.5,
        # 金利PCA用のイールドデータ
        "DGS2": np.random.rand(len(dates)) * 2 + 1.0,
        "DGS5": np.random.rand(len(dates)) * 2 + 1.2,
        "DGS10": np.random.rand(len(dates)) * 2 + 1.5,
        "DGS30": np.random.rand(len(dates)) * 2 + 2.0,
        # スプレッド、VIX、インフレ期待
        "BAMLH0A0HYM2": np.random.rand(len(dates)) + 3.0,
        "BAMLC0A0CM": np.random.rand(len(dates)) * 0.5 + 1.0,
        "VIXCLS": np.random.rand(len(dates)) * 15 + 10,
        "T10YIE": np.random.rand(len(dates)) + 2.0,
    }
    df_raw = pd.DataFrame(data, index=dates)
    # ---------------------------------------------------------------------------------


    def orthogonalize(series_to_clean, regressors):
        """
        ある系列(series_to_clean)を、他の変数(regressors)で回帰させ、
        その残差（他の変数と相関しない部分）を返すヘルパー関数。

        :param series_to_clean: pd.Series - 直交化したい元の系列
        :param regressors: pd.Series or pd.DataFrame - 回帰に使う説明変数
        :return: pd.Series - 直交化された系列（残差）
        """
        # NaNを落とし、インデックスを揃える
        combined_data = pd.concat([series_to_clean, regressors], axis=1).dropna()

        # 被説明変数Yと説明変数Xを定義
        Y = combined_data.iloc[:, 0]
        X = combined_data.iloc[:, 1:]

        # Xに定数項（切片）を追加
        X = sm.add_constant(X, has_constant="add")

        # OLSモデルで回帰分析を実行
        model = sm.OLS(Y, X).fit()

        # 元のseries_to_cleanと同じインデックスで残差を返す
        residuals = pd.Series(model.resid, index=Y.index)
        return residuals


    # ================================================================================
    # 1. データの前処理とマーケットファクターの作成
    # ================================================================================
    print("Step 1: データの前処理とマーケットファクターの作成")
    df = df_raw.copy()
    df.index = pd.to_datetime(df.index)

    # 欠損値を前日の値で埋める (forward fill)
    df.fillna(method="ffill", inplace=True)

    # リスクフリーレートを年率から日率に変換
    df["daily_rf"] = df["DTB3"] / 365

    # マーケットリターン（MSCI Kokusaiの日次リターン）を計算
    df["mkt_return"] = df["MSCI_KOKUSAI"].pct_change()

    # 【完成】マーケットファクター（超過リターン）
    df["Factor_Market"] = df["mkt_return"] - df["daily_rf"]
    print(" -> マーケットファクター (Factor_Market) を作成しました。\n")


    # ================================================================================
    # 2. 金利ファクターの作成と直交化
    # ================================================================================
    print("Step 2: 金利ファクターの作成と直交化")
    # 2-1. イールドカーブデータで主成分分析(PCA)を実行
    yield_cols = ["DGS2", "DGS5", "DGS10", "DGS30"]
    pca = PCA(n_components=3)
    principal_components = pca.fit_transform(df[yield_cols])

    # 2-2. PCAの結果をDataFrameに追加
    df_pc = pd.DataFrame(
        principal_components, index=df.index, columns=["Level", "Slope", "Curvature"]
    )
    df = pd.concat([df, df_pc], axis=1)

    # 2-3. Level, Slope, Curvatureのショック（日次差分）を計算
    df["Level_Shock"] = df["Level"].diff()
    df["Slope_Shock"] = df["Slope"].diff()
    df["Curvature_Shock"] = df["Curvature"].diff()

    # 2-4. 各金利ファクターをマーケットファクターに対して直交化
    df["Factor_Level"] = orthogonalize(df["Level_Shock"], df["Factor_Market"])
    df["Factor_Slope"] = orthogonalize(df["Slope_Shock"], df["Factor_Market"])
    df["Factor_Curvature"] = orthogonalize(df["Curvature_Shock"], df["Factor_Market"])
    print(" -> 金利ファクター (Level, Slope, Curvature) を作成し、直交化しました。\n")


    # ================================================================================
    # 3. FtoQファクターの作成と直交化
    # ================================================================================
    print("Step 3: Flight-to-Qualityファクターの作成と直交化")
    # 3-1. FtoQファクターの元系列を計算
    df["FtoQ"] = df["BAMLH0A0HYM2"] - df["BAMLC0A0CM"]

    # 3-2. FtoQのショック（日次差分）を計算
    df["FtoQ_Shock"] = df["FtoQ"].diff()

    # 3-3. FtoQをマーケットと金利ファクター群に対して直交化
    regressors_ftoq = df[
        ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature"]
    ]
    df["Factor_FtoQ"] = orthogonalize(df["FtoQ_Shock"], regressors_ftoq)
    print(" -> FtoQファクター (Factor_FtoQ) を作成し、直交化しました。\n")


    # ================================================================================
    # 4. インフレファクターの作成と直交化
    # ================================================================================
    print("Step 4: インフレファクターの作成と直交化")
    # 4-1. インフレのショック（日次差分）を計算
    df["Inflation_Shock"] = df["T10YIE"].diff()

    # 4-2. インフレをこれまでに作成した全てのファクターに対して直交化
    regressors_inflation = df[
        ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature", "Factor_FtoQ"]
    ]
    df["Factor_Inflation"] = orthogonalize(df["Inflation_Shock"], regressors_inflation)
    print(" -> インフレファクター (Factor_Inflation) を作成し、直交化しました。\n")


    # ================================================================================
    # 5. 最終的なファクターセットの完成
    # ================================================================================
    print("Step 5: 最終的なファクターセットの完成")
    # 最終的なファクターカラムのリスト
    final_factor_columns = [
        "Factor_Market",
        "Factor_Level",
        "Factor_Slope",
        "Factor_Curvature",
        "Factor_FtoQ",
        "Factor_Inflation",
    ]

    # ファクターだけを抜き出し、計算過程で生じたNaNを削除
    df_factors = df[final_factor_columns].dropna()

    print("\n--- 完成した直交化済みファクター（最初の5行） ---")
    print(df_factors.head())

    print("\n--- ファクター間の相関行列（対角成分以外はほぼ0になるはず） ---")
    # 相関行列を計算し、小数点以下4桁で表示
    correlation_matrix = df_factors.corr()
    print(correlation_matrix.round(4))
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
