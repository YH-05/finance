"""
metal.py

金属コモディティ分析モジュール
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from pandas import DataFrame

from analyze.reporting.market_report_utils import MarketPerformanceAnalyzer
from market.fred import HistoricalCache
from utils_core.settings import load_project_env


class DollarsIndexAndMetalsAnalyzer:
    """
    ドル指数と金属価格の分析を行うクラス。
    """

    def __init__(self):
        """
        DollarsIndexAndMetalsAnalyzerクラスを初期化する。
        必要なデータプロセッサを初期化し、データをロードしてリターンを計算する。
        """
        load_project_env()
        fred_dir = os.environ.get("FRED_DIR")
        if fred_dir is None:
            raise ValueError("FRED_DIR environment variable not set")
        self.db_path = Path(fred_dir) / "FRED.db"
        self.fred_cache = HistoricalCache()
        self.analyzer = MarketPerformanceAnalyzer()
        self.price_metal = self._load_metal_price()
        self.price = self.load_price()
        self.cum_return = self.calc_return()

    # -------------------------------------------------------------------------------------
    def _load_metal_price(self):
        """
        金属価格データをダウンロードし、整形して返す内部メソッド。

        Returns
        -------
        pd.DataFrame
            金属価格データ（Adj Close）を含むデータフレーム。
        """
        df_metals = (
            self.analyzer.yf_download_with_curl(
                tickers_to_download=self.analyzer.TICKERS_METAL, period="max"
            )
            .query('variable == "Adj Close"')
            .pivot(index="Date", columns="Ticker", values="value")
        )
        return df_metals

    # -------------------------------------------------------------------------------------
    def load_price(self):
        """
        ドル指数と金属価格データを結合したデータフレームを返す。

        Returns
        -------
        pd.DataFrame
            ドル指数と金属価格を含むデータフレーム（ロング形式）。
        """
        conn = sqlite3.connect(self.db_path)
        df_dollars = (
            pd.read_sql("SELECT * from DTWEXAFEGS", con=conn, parse_dates="date")
            .rename(columns={"date": "Date"})
            .set_index("Date")
        )

        df_price = pd.melt(
            pd.merge(
                df_dollars,
                self.price_metal,
                left_index=True,
                right_index=True,
                how="left",
            )
            .ffill()
            .reset_index(),
            id_vars="Date",
            var_name="Ticker",
            value_name="value",
        ).assign(variable="Price")

        return df_price

    # -------------------------------------------------------------------------------------
    def calc_return(self, start_date: str = "2020-01-01"):
        """
        指定された開始日からの累積リターンを計算する。

        Parameters
        ----------
        start_date : str, default "2020-01-01"
            リターン計算の開始日。

        Returns
        -------
        pd.DataFrame
            累積リターンを含むデータフレーム。
        """
        conn = sqlite3.connect(self.db_path)
        df_dollars = (
            pd.read_sql("SELECT * from DTWEXAFEGS", con=conn, parse_dates="date")
            .rename(columns={"date": "Date"})
            .set_index("Date")
        )

        df_metals_return = self.price_metal.loc[start_date:, :]
        df_metals_return = df_metals_return.div(df_metals_return.iloc[0])
        df_metals_return = pd.merge(
            df_metals_return, df_dollars, left_index=True, right_index=True, how="outer"
        ).ffill()

        return df_metals_return

    # -------------------------------------------------------------------------------------
    def plot_us_dollar_index_and_metal_price(
        self, df_cum_return: DataFrame | None = None
    ):
        """
        ドル指数と金属価格の累積リターンをプロットする。

        Parameters
        ----------
        df_cum_return : pd.DataFrame, optional
            プロットする累積リターンデータ。指定しない場合はインスタンスのデータを使用。

        Returns
        -------
        plotly.graph_objects.Figure
            作成されたPlotlyのFigureオブジェクト。
        """

        if df_cum_return is None:
            df_cum_return = self.cum_return

        fig = go.Figure()
        for col in [s for s in df_cum_return.columns.tolist() if s != "DTWEXAFEGS"]:
            fig.add_trace(
                go.Scatter(
                    x=df_cum_return.index,
                    y=df_cum_return[col],
                    mode="lines",
                    line=dict(width=0.8),
                    name=col,
                    yaxis="y1",
                    connectgaps=True,
                )
            )
        fig.add_trace(
            go.Scatter(
                x=df_cum_return.index,
                y=df_cum_return["DTWEXAFEGS"],
                mode="lines",
                line=dict(color="white", width=0.8),
                name="Nominal Advanced Foreign Economies US Dollar Index",
                connectgaps=True,
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Metal Commodities and US Dollar Index",
            width=1000,
            height=450,
            template="plotly_dark",
            yaxis=dict(title="Cumulative Return", showgrid=True),
            yaxis2=dict(
                title="US Dollar Index", side="right", showgrid=False, overlaying="y"
            ),
            hovermode="x",
            legend=dict(
                yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"
            ),
            margin=dict(l=30, r=30, t=50, b=30),
        )

        return fig
