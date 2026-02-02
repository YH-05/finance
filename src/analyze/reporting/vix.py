"""
vix.py

"""

import pandas as pd
import plotly.graph_objects as go

from market.errors import FREDCacheNotFoundError
from market.fred import HistoricalCache
from utils_core.logging import get_logger

logger = get_logger(__name__)


def _load_multiple_series(series_ids: list[str]) -> pd.DataFrame:
    """複数のFREDシリーズをロードして結合する。

    Parameters
    ----------
    series_ids : list[str]
        FREDシリーズIDのリスト

    Returns
    -------
    pd.DataFrame
        date, variable, value 列を持つデータフレーム

    Raises
    ------
    FREDCacheNotFoundError
        全シリーズの取得に失敗した場合
    """
    # 空リストの場合は空のDataFrameを返す
    if not series_ids:
        return pd.DataFrame({"date": [], "variable": [], "value": []})

    logger.debug("Loading FRED series", series_ids=series_ids)

    cache = HistoricalCache()
    dfs = []
    missing = []

    for series_id in series_ids:
        df = cache.get_series_df(series_id)
        if df is None or df.empty:
            logger.warning("Series not found in cache", series_id=series_id)
            missing.append(series_id)
            continue

        df = df.reset_index()
        df.columns = ["date", "value"]  # カラム名を明示的に設定
        df["variable"] = series_id
        # 列順序を [date, variable, value] に並べ替え
        df = df[["date", "variable", "value"]]
        dfs.append(df)
        logger.debug("Series loaded", series_id=series_id, rows=len(df))

    if not dfs:
        logger.error("All series failed to load", missing=missing)
        raise FREDCacheNotFoundError(missing)

    if missing:
        logger.warning(
            "Some series missing",
            loaded=[s for s in series_ids if s not in missing],
            missing=missing,
        )

    result = pd.concat(dfs, ignore_index=True)
    logger.info("Series loading complete", total_rows=len(result))
    return result


def plot_vix_and_high_yield_spread():
    """
    VIXと米国ハイイールドスプレッドの推移をプロットする関数。
    """

    # データdownload
    fred_series_list = ["VIXCLS", "BAMLH0A0HYM2"]
    df = pd.pivot_table(
        _load_multiple_series(fred_series_list),
        index="date",
        columns="variable",
        values="value",
        aggfunc="first",  # 重複がある場合は最初の値を使用
    ).assign(
        VIX_mean=lambda x: x["VIXCLS"].mean(),
        Spread_mean=lambda x: x["BAMLH0A0HYM2"].mean(),
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["VIXCLS"],
            name="VIX",
            line=dict(width=0.8, color="orange"),
            connectgaps=True,
        )
    )
    # ★ データの平均線を追加
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["VIX_mean"],
            name=f"VIX mean: {df['VIX_mean'].iloc[-1]:.2f}",
            line=dict(width=0.8, dash="dot", color="orange"),
            connectgaps=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BAMLH0A0HYM2"],
            name="US High Yield Index Option-Adjusted Spread",
            line=dict(width=0.8, color="#00ffee"),
            connectgaps=True,
            yaxis="y2",
        )
    )
    # ★ データの平均線を追加
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Spread_mean"],
            name=f"Spread_mean: {df['Spread_mean'].iloc[-1]:.2f}",
            line=dict(width=0.8, dash="dash", color="#00ffee"),
            connectgaps=True,
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="VIX and US High Yield Index Option-Adjusted Spread",
        width=1000,
        height=450,
        template="plotly_dark",
        yaxis=dict(
            title="VIX",
            rangemode="tozero",
            showgrid=True,
        ),
        yaxis2=dict(
            title="US High Yield Index<br>Option-Adjusted Spread (bps)",
            overlaying="y",
            side="right",
            rangemode="tozero",
            showgrid=False,
        ),
        hovermode="x",
        legend=dict(yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"),
        margin=dict(l=30, r=30, t=50, b=30),
    )
    fig.show()


# =========================================================================================
def plot_vix_and_uncertainty_index(ema_span: int = 30):
    """
    VIXと米国不確実性指数の推移をプロットする関数。

    Parameters
    ----------
    ema_span : int, default 30
        米国不確実性指数の指数移動平均のスパン（日数）。
    """

    # データdownload
    fred_series_list = ["VIXCLS", "USEPUINDXD"]
    df = pd.pivot_table(
        _load_multiple_series(fred_series_list),
        index="date",
        columns="variable",
        values="value",
        aggfunc="first",  # 重複がある場合は最初の値を使用
    ).assign(
        VIX_mean=lambda x: x["VIXCLS"].mean(),
        UCN_Index_EMA=lambda x: x["USEPUINDXD"].ewm(span=ema_span, adjust=False).mean(),
        UCN_Index_mean=lambda x: x["USEPUINDXD"].mean(),
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["VIXCLS"],
            name="VIX",
            line=dict(width=0.8, color="orange"),
            connectgaps=True,
        )
    )
    # ★ データの平均線を追加
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["VIX_mean"],
            name=f"VIX mean: {df['VIX_mean'].iloc[-1]:.2f}",
            line=dict(width=0.8, dash="dot", color="orange"),
            connectgaps=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["USEPUINDXD"],
            name="Economic Policy Uncertainty Index for US",
            line=dict(width=0.8, color="rgba(0, 128, 0, 0.3)"),
            connectgaps=True,
            yaxis="y2",
        )
    )
    # 指数移動平均
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["UCN_Index_EMA"],
            name="UCN_Index_EMA",
            line=dict(width=1.0, color="#90ee90"),
            connectgaps=True,
            yaxis="y2",
        )
    )
    # ★ データの平均線を追加
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["UCN_Index_mean"],
            name=f"UCN_Index_mean: {df['UCN_Index_mean'].iloc[-1]:.2f}",
            line=dict(width=0.8, dash="dash", color="#90ee90"),
            connectgaps=True,
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="VIX and Economic Policy Uncertainty Index for US",
        width=1000,
        height=450,
        template="plotly_dark",
        yaxis=dict(
            title="VIX",
            rangemode="tozero",
            showgrid=True,
        ),
        yaxis2=dict(
            title="Economic Policy<br>Uncertainty Index for US",
            overlaying="y",
            side="right",
            rangemode="tozero",
            showgrid=False,
        ),
        hovermode="x",
        legend=dict(yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"),
        margin=dict(l=30, r=30, t=50, b=30),
    )
    fig.show()
