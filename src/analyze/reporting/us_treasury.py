"""
us_treasury.py
"""

import os
from pathlib import Path
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import seaborn as sns
from matplotlib import gridspec
from matplotlib.ticker import MultipleLocator, PercentFormatter
from plotly.subplots import make_subplots
from sklearn.decomposition import PCA

from market.fred.historical_cache import HistoricalCache
from utils_core.logging import get_logger
from utils_core.settings import get_fred_api_key, load_project_env

logger = get_logger(__name__)

# 環境変数を読み込み
load_project_env()
FRED_API = os.getenv("FRED_API_KEY")


def load_fred_api_key() -> str:
    """環境変数からFRED APIキーを読み込む"""
    return get_fred_api_key()


def load_fred_series_id_json() -> dict:
    """FREDのシリーズIDが定義されたJSONファイルを読み込む(Githubから)"""
    json_url = os.environ.get("FRED_SERIES_ID_JSON")
    if json_url is None:
        logger.warning("FRED_SERIES_ID_JSON environment variable not set")
        return {}
    try:
        response = requests.get(json_url, timeout=30)
        response.raise_for_status()
        series_data = response.json()
    except Exception:
        logger.error(
            "Failed to load FRED series ID JSON",
            url=json_url,
            exc_info=True,
        )
        series_data = {}
    return series_data


def plot_us_interest_rates_and_spread(
    start_date: str = "2000-01-01",
    end_date: Optional[str] = None,
    template: str = "plotly_dark",
):
    """米国金利とイールドスプレッドの時系列データをPlotlyでプロットする。

    HistoricalCacheからFREDの時系列データを読み込み、
    複数のサブプロットに分けて視覚化する。プロットには主要な米国債利回り、
    FF金利、および長短金利差（T10Y3M, T10Y2Y）が含まれる。

    Parameters
    ----------
    start_date : str, optional
        プロットを描画する期間の開始日。'YYYY-MM-DD'形式。
        デフォルトは "2000-01-01"。
    end_date : str, optional
        プロットを描画する期間の終了日。'YYYY-MM-DD'形式。
        デフォルトは None で、データセットの最終日までを描画する。
    template : str, optional
        Plotlyテンプレート名。デフォルトは "plotly_dark"。

    Returns
    -------
    None
        この関数は戻り値を返さず、Plotlyのプロットを直接表示する。

    """

    series_id_spread = ["T10Y3M", "T10Y2Y"]
    series_id_interest_rates = [
        "DFF",
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
    ]

    # 1. データの読み込みと整形
    cache = HistoricalCache()
    dfs = []
    for series_id in series_id_interest_rates + series_id_spread:
        df_temp = cache.get_series_df(series_id)
        if df_temp is not None:
            df_temp = df_temp.reset_index().rename(columns={"index": "date"})
            df_temp["variable"] = series_id
            dfs.append(df_temp)
        else:
            logger.warning("Series not found in cache", series_id=series_id)

    if not dfs:
        logger.error("No data loaded from cache for interest rates plot")
        return

    df = pd.concat(dfs, ignore_index=True)
    df = pd.pivot(
        df,
        index="date",
        columns="variable",
        values="value",
    ).sort_index()
    df.index = pd.to_datetime(df.index)

    # 期間のフィルタリング
    if end_date:
        df = df.loc[pd.to_datetime(start_date) : pd.to_datetime(end_date)]
    else:
        df = df.loc[pd.to_datetime(start_date) :]

    # 2. Plotlyサブプロットの作成
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            "US Interest Rates",
            "10-Year vs 3-Month Spread (T10Y3M)",
            "10-Year vs 2-Year Spread (T10Y2Y)",
        ),
    )

    # 3. プロットするカラムの定義とカラーマップの準備
    cols_to_plot_rates = [
        "DFF",
        "DGS1",
        "DGS2",
        "DGS3",
        "DGS5",
        "DGS7",
        "DGS10",
        "DGS20",
        "DGS30",
    ]

    cols_to_plot_rates = [col for col in cols_to_plot_rates if col in df.columns]
    series_id_spread = [col for col in series_id_spread if col in df.columns]

    cols_all_for_cmap = cols_to_plot_rates + series_id_spread
    total_cols = len(cols_all_for_cmap)
    color_map = {}

    for i, series_id in enumerate(cols_all_for_cmap):
        if series_id != "DFF" and series_id not in series_id_spread:
            scale_index = i / (total_cols - 1) if total_cols > 1 else 0
            color_index = int(scale_index * (len(px.colors.sequential.Tealgrn) - 1))
            color_map[series_id] = px.colors.sequential.Tealgrn[color_index]

    # 4. サブプロット1: 金利
    if "DFF" in cols_to_plot_rates:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["DFF"].div(100),
                name="DFF (FF Rate)",
                line=dict(color="silver", width=2),
                connectgaps=True,
                # legendgroup="1",
                # legendgrouptitle_text="Rates",
                # legendrank=1,
            ),
            row=1,
            col=1,
        )

    rank_counter = 2
    for series_id in cols_to_plot_rates:
        if series_id != "DFF" and series_id in color_map:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[series_id].div(100),
                    name=series_id,
                    line=dict(color=color_map[series_id], width=1.0),
                    opacity=0.7,
                    connectgaps=True,
                    # legendgroup="1",
                    # legendrank=rank_counter,
                ),
                row=1,
                col=1,
            )
            rank_counter += 1

    # 5. サブプロット2: 10Y-3M スプレッド
    if "T10Y3M" in series_id_spread:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["T10Y3M"],
                name="T10Y3M Spread",
                showlegend=False,
                fill="tozeroy",
                fillcolor="rgba(106, 90, 205, 0.4)",
                line=dict(color="rgba(106, 90, 205, 0.8)"),
                connectgaps=True,
                # legendgroup="2",
                # legendgrouptitle_text="Spreads",
            ),
            row=2,
            col=1,
        )
        fig.add_hline(y=0, line=dict(color="black", width=1, dash="dash"), row=2, col=1)  # type: ignore[arg-type]

    # 6. サブプロット3: 10Y-2Y スプレッド
    if "T10Y2Y" in series_id_spread:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["T10Y2Y"],
                name="T10Y2Y Spread",
                showlegend=False,
                fill="tozeroy",
                fillcolor="rgba(30, 144, 255, 0.4)",
                line=dict(color="rgba(30, 144, 255, 0.8)"),
                # legendgroup="2",
                connectgaps=True,
            ),
            row=3,
            col=1,
        )
        fig.add_hline(y=0, line=dict(color="black", width=1, dash="dash"), row=3, col=1)  # type: ignore[arg-type]

    # 7. レイアウトの更新
    fig.update_layout(
        title_text="US Interest Rates and Yield Spreads",
        # 2. グラフサイズを指定
        width=1000,
        height=700,
        template=template,
        showlegend=True,
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,  # X軸ラベルとの距離を調整
            xanchor="center",
            x=0.5,
            # tracegroupgap=40,
            # title_font=dict(size=14),
        ),
        yaxis1=dict(title="Interest Rates (%)", tickformat=".2%"),
        yaxis2=dict(title="Spread (%)"),
        yaxis3=dict(title="Spread (%)"),
        xaxis1_showticklabels=False,
        xaxis2_showticklabels=False,
        xaxis3_title="Date",
        hovermode="x",
    )

    fig.update_annotations(font_size=12)
    fig.update_xaxes(rangeslider_visible=False)

    fig.show()


# ================================================================================
def load_yield_data_from_cache() -> pd.DataFrame:
    """キャッシュからイールドデータを読み込む。

    HistoricalCacheを使用して米国債イールドデータを取得する。

    Returns
    -------
    pd.DataFrame
        イールドデータを含むデータフレーム。
        インデックスは日付、カラムは各テナー（DGS1MO, DGS3MO, ...）。
    """
    table_list = [
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
    ]

    cache = HistoricalCache()
    dfs_yield = []
    for series_id in table_list:
        df = cache.get_series_df(series_id)
        if df is not None:
            df = df.reset_index().rename(columns={"index": "date"})
            df["tenor"] = series_id
            dfs_yield.append(df)

    df_yield = (
        pd.pivot(
            pd.concat(dfs_yield, ignore_index=True),
            index="date",
            columns="tenor",
            values="value",
        )
        .sort_index()
        .reindex(columns=table_list)
    )

    return df_yield


# ================================================================================
def align_pca_components(pca_components, pc_scores):
    """
    PCAの主成分の符号を経済学的な解釈に基づき、一貫性を持つように調整する。
    PC1=Level, PC2=Slope, PC3=Curvatureと仮定する。

    Parameters
    ----------
    pca_components : np.ndarray
        pca.components_ - 主成分の負荷量 (loadings)
    pc_scores : np.ndarray
        主成分スコア (時系列データ)

    Returns
    -------
    np.ndarray
        aligned_scores (符号調整後の主成分スコア)
    """
    aligned_components = pca_components.copy()
    aligned_scores = pc_scores.copy()

    # --- PC1 (Level) の符号調整 ---
    # 負荷量が全て正になるように調整（金利上昇を正とする）
    if np.sum(aligned_components[0]) < 0:
        aligned_components[0] = -aligned_components[0]
        aligned_scores[:, 0] = -aligned_scores[:, 0]

    # --- PC2 (Slope) の符号調整 ---
    # 長期の負荷量が正、短期が負になるように調整（スティープ化を正とする）
    if aligned_components[1, -1] < 0:  # 最後の要素（最長期）が負の場合
        aligned_components[1] = -aligned_components[1]
        aligned_scores[:, 1] = -aligned_scores[:, 1]

    # --- PC3 (Curvature) の符号調整 ---
    # 中期の負荷量が正になるように調整（バタフライが立つ方向を正とする）
    mid_index = len(aligned_components[2]) // 2
    if aligned_components[2, mid_index] < 0:
        aligned_components[2] = -aligned_components[2]
        aligned_scores[:, 2] = -aligned_scores[:, 2]

    return aligned_scores


# ================================================================================
def analyze_yield_curve_pca(df_yield: pd.DataFrame, n_components: int = 3):
    """
    イールドカーブのPCA分析を行う。

    Parameters
    ----------
    df_yield : pd.DataFrame
        イールドデータを含むデータフレーム。
    n_components : int, default 3
        主成分の数。

    Returns
    -------
    tuple
        (pd.DataFrame: PCAスコアのデータフレーム, sklearn.decomposition.PCA: 学習済みPCAオブジェクト)
    """
    # 金利の変動幅を計算
    df_yield_diff = df_yield.diff().dropna(how="any")

    # apply PCA
    pca = PCA(n_components=n_components)
    principal_components_raw = pca.fit_transform(df_yield_diff)

    # 符号を揃える
    principal_components_aligned = align_pca_components(
        pca.components_, principal_components_raw
    )

    # 符号調整後のスコアでDataFrameを作成
    cols = (
        ["Level", "Slope", "Curvature"]
        if n_components == 3
        else [f"PC_{i + 1}" for i in range(principal_components_aligned.shape[1])]
    )
    df_pca = pd.DataFrame(
        principal_components_aligned,
        index=df_yield_diff.index,
        columns=cols,  # type: ignore[arg-type]
    )

    return df_pca, pca


# ================================================================================
def plot_loadings_and_explained_variance(df_yield: pd.DataFrame):
    """
    学習済みのPCAオブジェクトを受け取り、主成分負荷と寄与率をプロットする関数。

    Parameters
    ----------
    df_yield : pd.DataFrame
        イールドデータを含むデータフレーム。
    """

    # PCA計算
    n_features = df_yield.shape[1]
    _, pca = analyze_yield_curve_pca(df_yield=df_yield, n_components=n_features)

    # loadings(top3)
    df_loadings = pd.DataFrame(
        pca.components_[:3, :],  # 上位3成分のみ抽出
        columns=df_yield.columns,  # type: ignore[arg-type]
        index=[  # type: ignore[arg-type]
            "PC1 (Level)",
            "PC2 (Slope)",
            "PC3 (Curvature)",
        ],
    )

    # 主成分スコア（time series, top3 components）
    df_yield_diff = df_yield.diff().dropna(how="any")
    pc_scores = pca.transform(df_yield_diff)[:, :3]
    df_pca = pd.DataFrame(
        pc_scores,
        columns=[f"PC{i + 1}" for i in range(3)],  # type: ignore[arg-type]
        index=df_yield_diff.index,
    )

    # 寄与率と累積寄与率（all components）
    explained_variance = pca.explained_variance_ratio_
    cumulative_explained_variance = np.cumsum(explained_variance)
    n_components = len(explained_variance)

    # -------------------------------------
    # Plot GridSpecを使用して柔軟なレイアウトを定義
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(10, 10), tight_layout=True)
    gs_master = gridspec.GridSpec(4, 2, figure=fig, height_ratios=[5, 1, 1, 1])

    # --- 上段: 負荷量と寄与率 ---
    gs_loadings = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=gs_master[0, 0])
    ax_loadings = fig.add_subplot(gs_loadings[0, 0])
    gs_explained_variance = gridspec.GridSpecFromSubplotSpec(
        1, 1, subplot_spec=gs_master[0, 1]
    )
    ax_explained_variance = fig.add_subplot(gs_explained_variance[0, 0])
    # --- 下段: 主成分スコアの時系列 ---
    gs_pca = gridspec.GridSpecFromSubplotSpec(
        3, 1, subplot_spec=gs_master[1:, :], hspace=0.1
    )
    ax_pc1 = fig.add_subplot(gs_pca[0, 0])
    ax_pc2 = fig.add_subplot(gs_pca[1, 0], sharex=ax_pc1)
    ax_pc3 = fig.add_subplot(gs_pca[2, 0], sharex=ax_pc1)

    start_date = df_yield_diff.index.min().strftime("%Y-%m-%d")
    end_date = df_yield_diff.index.max().strftime("%Y-%m-%d")

    fig.suptitle(
        f"PCA of US Treasury Yield Curve [ from {start_date} to {end_date} ({len(df_yield_diff)} Days) ]"
    )

    # (ax1) 負荷量ヒートマップ
    sns.heatmap(df_loadings, cmap="vlag", annot=True, fmt=".2f", ax=ax_loadings)
    ax_loadings.set_xlabel("Maturity")
    ax_loadings.set_title("PCA Loadings")

    # (ax2) 寄与率と累積寄与率
    component_numbers = np.arange(1, n_components + 1)
    bars = ax_explained_variance.bar(
        component_numbers,
        explained_variance,
        alpha=0.7,
        label="Individual explained variance",
        color="royalblue",
    )
    ax_explained_variance.plot(
        component_numbers,
        cumulative_explained_variance,
        marker="o",
        linestyle="--",
        color="darkorange",
        label="Cumulative explained variance",
    )
    ax_explained_variance.set_title("Explained Variance")
    ax_explained_variance.set_xlabel("Principal Component")
    ax_explained_variance.set_xticks(component_numbers)
    ax_explained_variance.set_ylabel("Explained Variance Ratio")
    ax_explained_variance.set_ylim(0, 1.05)
    ax_explained_variance.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax_explained_variance.yaxis.set_major_locator(MultipleLocator(0.1))
    ax_explained_variance.grid(which="minor", axis="y", linestyle=":", alpha=0.8)
    for bar in bars:
        yval = bar.get_height()
        ax_explained_variance.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 0.02,
            f"{yval:.1%}",
            ha="center",
            va="bottom",
        )
    ax_explained_variance.legend(loc="center right")

    # (ax3, ax4, ax5) 主成分スコアの時系列プロット
    axes_pc = [ax_pc1, ax_pc2, ax_pc3]
    colors = ["green", "blue", "red"]
    pc_labels = ["PC1 (Level)", "PC2 (Slope)", "PC3 (Curvature)"]

    for i, ax in enumerate(axes_pc):
        sns.lineplot(
            data=df_pca,
            x=df_pca.index,
            y=f"PC{i + 1}",
            ax=ax,
            alpha=0.8,
            color=colors[i],
        )
        ax.set_ylabel(pc_labels[i])
        ax.axhline(0, color="grey", linestyle="--", linewidth=0.8)
        ax.set_xlabel("")  # X軸ラベルは一番下のみ表示

    # 一番下のグラフ以外、X軸の目盛りラベルを非表示に
    plt.setp(ax_pc1.get_xticklabels(), visible=False)
    plt.setp(ax_pc2.get_xticklabels(), visible=False)

    axes_pc[-1].set_xlabel("Year")

    # 全体のレイアウトを調整
    fig.tight_layout(rect=[0, 0, 1, 0.97])  # type: ignore # suptitleとの重なりを回避
    plt.show()


# ================================================================================
def plot_us_corporate_bond_spreads(
    fred_series_id: list[str] | None = None,
    template: str = "plotly_dark",
):
    """
    FREDの社債スプレッドデータをHistoricalCacheから読み込み、Plotlyでプロットする。

    Parameters
    ----------
    fred_series_id : list[str] | None
        FREDシリーズIDのリスト。Noneの場合はデフォルトの社債スプレッド系列を使用。
    template : str
        Plotlyテンプレート名。デフォルトは "plotly_dark"。
    """
    fred_series_id = (
        fred_series_id
        if fred_series_id
        else load_fred_series_id_json()["Corporate Bond Yield Spread"]
    )
    # 1. データの読み込み
    cache = HistoricalCache()

    # { "ID": "Full Name" } の辞書を作成
    spread_dict = {k: v["name_en"] for k, v in fred_series_id.items()}

    # キャッシュからデータを読み込む
    dfs = []
    for series_id in spread_dict:
        df = cache.get_series_df(series_id)
        if df is not None:
            df = df.reset_index().rename(columns={"index": "date"})
            df["variable"] = series_id
            dfs.append(df)

    # 2. データの整形
    df = pd.concat(dfs, ignore_index=True).replace(spread_dict)

    # 'variable' 列の文字列をクリーニング
    df["variable"] = df["variable"].str.replace("ICE BofA ", "")
    df["variable"] = df["variable"].str.replace("Index Option-Adjusted Spread", "")

    # プロット用にピボット (元のコードの 'df' をそのまま使用)
    df = pd.pivot(df, index="date", columns="variable", values="value").sort_index()

    # 3. グラフの作成
    fig = go.Figure()
    for spread in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[spread],
                name=spread,
                line=dict(width=0.8),
                connectgaps=True,
            )
        )

    # 4. レイアウトの更新
    fig.update_layout(
        width=1000,
        height=450,
        template=template,
        title="US Corporate Bond Spread",
        hovermode="x",
        legend=dict(yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"),
        margin=dict(l=20, r=20, t=50, b=30),
    )

    # 5. グラフの表示
    fig.show()


# ================================================================================
