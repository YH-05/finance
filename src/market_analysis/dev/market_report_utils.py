"""
market_report_utils.py
"""

import datetime
import os
import re
import sqlite3
from pathlib import Path
from typing import List, Literal, Optional

import curl_cffi
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import seaborn as sns
import yfinance as yf
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pandas import DataFrame


# =========================================================================================
class MarketPerformanceAnalyzer:
    """
    株価データの取得、リターン計算、および累積リターンプロットを一元的に管理するクラス。
    主要なインデックス、セクター、個別株のパフォーマンスを分析・可視化する機能を提供する。
    データソースはyfinanceを使用し、curl_cffiでHTTPリクエストを行う。
    """

    def __init__(self):
        """
        MarketPerformanceAnalyzerクラスを初期化する。
        データの取得と基本リターンの計算を行う。
        """
        self.today = datetime.date.today()

        # --- 1. 定数（クラス属性）の定義 ---

        self.TICKERS_US_AND_SP500 = [
            "^SPX",
            "^SPXEW",
            "VUG",
            "VTV",
            "SPHQ",
            "^DJI",
            "^IXIC",
            # "^GSPC"
        ]
        # self.TICKERS_WORLD = [
        #     "^GDAXI",
        #     "^FTSE",
        #     "^FCHI",
        #     "^STOXX50E",
        #     "^AEX",
        #     "^N225",
        #     "^HSI",
        #     "000001.SS",
        #     "399001.SZ",
        # ]
        self.TICKERS_MAG7_AND_SOX = [
            "^SOX",
            "AAPL",
            "MSFT",
            "NVDA",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
        ]
        self.SECTOR_MAP_EN = {
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLE": "Energy",
            "XLF": "Financials",
            "XLV": "Health Care",
            "XLI": "Industrials",
            "XLK": "Information Technology",
            "XLB": "Materials",
            "XLU": "Utilities",
            "XLC": "Communication Services",
            "XLRE": "Real Estate",
        }
        # 金属
        self.TICKERS_METAL = ["GLD", "SLV", "PPLT", "CPER", "PALL", "DBB"]
        # WTI原油（先物）
        self.TICKERS_OIL = ["CL=F"]
        # 市場センチメント
        self.TICKERS_MARKET = [
            "^VIX",  # VIX
            "DX-Y.NYB",  # ドル指数（DXY Futures）
        ]

        # 全てのティッカーを結合
        self.ALL_TICKERS = list(
            self.TICKERS_US_AND_SP500
            # + self.TICKERS_WORLD
            + self.TICKERS_MAG7_AND_SOX
            + list(self.SECTOR_MAP_EN.keys())
            + self.TICKERS_METAL
            + self.TICKERS_OIL
            + self.TICKERS_MARKET
        )

        # データ取得と前処理
        raw_df = self.yf_download_with_curl(self.ALL_TICKERS)
        self.price_data = (
            raw_df.loc[raw_df["variable"] == "Adj Close"]
            .pivot(index="Date", columns="Ticker", values="value")
            .astype(float)
        ).dropna(subset=list(self.SECTOR_MAP_EN.keys()))

        # 対数リターンの計算とセクター名へのリネーム
        self.log_return = np.log(self.price_data / self.price_data.shift(1))
        self.log_return.rename(columns=self.SECTOR_MAP_EN, inplace=True)

        # 累積リターンの推移を計算（プロット用）
        self.cum_return_plot = np.exp(self.log_return.cumsum()).fillna(1)

        # パフォーマンステーブルの事前計算
        self.performance_table = self._calculate_period_returns()

    # -------------------------------------------------------------------------------------
    def get_eps_historical_data(
        self, tickers_to_download: list[str]
    ) -> dict[str, dict[str, pd.DataFrame]]:
        """
        指定された複数の銘柄の実績EPS（Reported EPS）のヒストリカルデータを取得する。
        年次（annual）と四半期（quarterly）のデータが含まれます。

        Parameters
        ----------
        tickers_to_download : list[str]
            ティッカーシンボルのリスト（例: ["AAPL", "MSFT"]）

        Returns
        -------
        dict[str, dict[str, pd.DataFrame]]
            キー: 銘柄名 (str)
            値: 年次と四半期の実績EPSデータを含む辞書。キーは 'annual_eps' と 'quarterly_eps'。
            データ取得に失敗した銘柄は結果に含まれません。
        """
        all_eps_data = []

        for ticker in tickers_to_download:
            try:
                # yf.Tickerオブジェクトをセッション付きで取得
                session = curl_cffi.Session(impersonate="safari15_5")
                t = yf.Ticker(ticker, session=session)

                # --- 決算情報（earnings）を取得 ---
                # .earnings属性は、実績EPS（Reported EPS）と収益（Revenue）のデータフレームを保持
                earnings_data = t.earnings_history.assign(Ticker=ticker)
                earnings_data.index = pd.to_datetime(earnings_data.index)
                all_eps_data.append(earnings_data)

            except Exception as e:
                print(
                    f"エラー: 銘柄 {ticker} のEPSデータ取得中に例外が発生しました: {e}"
                )

        all_eps_data = pd.concat(all_eps_data)

        return all_eps_data

    # -------------------------------------------------------------------------------------
    def yf_download_with_curl(
        self,
        tickers_to_download: list[str],
        period: str = "2y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        yfinanceのダウンロードをcurl_cffiで代替する関数。

        Parameters
        ----------
        tickers_to_download : list[str]
            ダウンロードするティッカーのリスト。
        period : str, default "2y"
            データ取得期間。
        interval : str, default "1d"
            データの間隔。

        Returns
        -------
        pd.DataFrame
            取得したデータフレーム。
        """
        session = curl_cffi.Session(impersonate="safari15_5")
        intra_day_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]
        datetime_col_name = None
        if not tickers_to_download:
            tickers_to_download = self.ALL_TICKERS
        if interval in intra_day_intervals:
            datetime_col_name = "Datetime"
            df = yf.download(
                tickers=tickers_to_download,
                period=period,
                interval=interval,
                prepost=False,
                group_by="ticker",
            )
            return df  # type: ignore
        else:
            datetime_col_name = "Date"
            df = (
                yf.download(
                    tickers=tickers_to_download,
                    period=period,
                    interval=interval,
                    session=session,
                    auto_adjust=False,
                )
                .stack(future_stack=True)  # type: ignore
                .reset_index()
            )
            df = pd.melt(
                df,
                id_vars=[datetime_col_name, "Ticker"],
                value_vars=df.columns.tolist()[2:],
                value_name="value",
                var_name="variable",
            )
            return df

    # -------------------------------------------------------------------------------------
    ## 期間リターン計算
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    def get_data_since_period_start(
        self, df: pd.DataFrame, date_column: str, period_type: str = "yearly"
    ) -> pd.DataFrame:
        """
        データフレームから、前年の最終日（YTD基準）または前月の最終日（MTD基準）以降のデータを取得する。

        Parameters
        ----------
        df : pd.DataFrame
            日付カラムを持つデータフレーム。
        date_column : str
            日付データが格納されているカラム名（datetime型を想定）。
        period_type : str, default "yearly"
            基準とする期間タイプ。'yearly' (YTD) または 'monthly' (MTD)。

        Returns
        -------
        pd.DataFrame
            基準日以降のデータ。
        """

        # 1. 日付カラムをインデックスに設定し、datetime型に変換
        if date_column not in df.index.names:
            df = df.set_index(date_column)

        # インデックスがdatetime型であることを確認
        df.index = pd.to_datetime(df.index)
        # 2. 基準日を決定するロジック
        start_date = None

        if period_type == "yearly":
            # --- YTD基準日（前年の最終日）の特定 ---

            previous_year = self.today.year - 1

            try:
                # 前年のデータに絞り込み、その中の最大の日付（最終営業日）を特定
                start_date = df.loc[str(previous_year)].index.max()
            except KeyError:
                print(
                    f"警告: {previous_year}年のデータが見つかりませんでした。全データを返します。"
                )
                return df

        elif period_type == "monthly":
            # --- MTD基準日（前月の最終日）の特定 ---

            # 現在の月から1日を引き、前月の任意の日付を取得
            # 例: 9/30 -> 9/29 (前月ではない)
            # 確実に前月の日付を取得するため、現在の月の初日 (self.today.replace(day=1)) から1日を引く
            last_day_of_previous_month = self.today.replace(day=1) - datetime.timedelta(
                days=1
            )

            # 前月の最終日データを探すために、前月のデータを取得
            previous_month_year = last_day_of_previous_month.year
            previous_month = last_day_of_previous_month.month

            try:
                # locで前月・前年のデータを抽出
                # 例: 2025年9月に実行した場合、2025-08のデータに絞り込み
                start_date = df.loc[
                    str(previous_month_year) + "-" + str(previous_month).zfill(2)
                ].index.max()
            except KeyError:
                # データが存在しない場合、直近のデータセットを返却（MTDの場合、現在月全体）
                return df.loc[
                    str(self.today.year) + "-" + str(self.today.month).zfill(2)
                ]  # pyright: ignore[reportReturnType]

        else:
            raise ValueError(
                "period_type は 'yearly' または 'monthly' のいずれかを指定してください。"
            )

        # 3. 基準日以降のデータを抽出
        if start_date is not None:
            # 抽出範囲は、「基準日」の行から「データフレームの終端」まで
            data_since_period_start = df.loc[start_date:]
            return data_since_period_start

        return df  # 念のため、何か問題があった場合は元のDFを返す

    # -------------------------------------------------------------------------------------
    def _get_last_tuesday_date(self) -> datetime.date:
        """
        先週火曜日の日付を datetime.date 型で取得する。

        Returns
        -------
        datetime.date
            先週火曜日の日付。
        """
        current_weekday = self.today.weekday()
        days_to_subtract = (current_weekday + 7) - 1  # (火曜日の曜日番号)
        return self.today - datetime.timedelta(days=days_to_subtract)

    # -------------------------------------------------------------------------------------
    def get_final_period_return(
        self, df_price: pd.DataFrame, return_type: str, period_name: str
    ) -> DataFrame:
        """
        プライスのDataFrameを受け取り、最終的な累積リターン（%）を計算し整形する。

        Parameters
        ----------
        df_price : pd.DataFrame
            価格データフレーム。
        return_type : str
            リターンの種類 ("simple" または "log")。
        period_name : str
            期間の名前（カラム名に使用）。

        Returns
        -------
        pd.DataFrame
            計算されたリターンを含むデータフレーム。
        """
        result = None
        if return_type == "simple":
            result = df_price.div(df_price.iloc[0]).sub(1).mul(100).iloc[-1].to_frame()
            result.columns = [period_name]
            result = result.rename(index=self.SECTOR_MAP_EN)
        elif return_type == "log":
            df_log_returns = np.log(df_price / df_price.shift(1)).dropna()  # pyright: ignore[reportAttributeAccessIssue]
            result: DataFrame = (
                np.exp(
                    df_log_returns.sum()
                )  # 期間全体の累積対数リターンを計算し、expで通常リターンへ
                .sub(1)  # リターン率（例: 1.10 -> 0.10）
                .mul(100)  # %に変換（例: 0.10 -> 10.0）
                .rename(period_name)  # Tickerごとの結果に期間名を付ける
                .to_frame()  # DataFrameに変換
            )
            result: DataFrame = result.rename(index=self.SECTOR_MAP_EN)

        return result  # pyright: ignore[reportReturnType]

    # -------------------------------------------------------------------------------------
    def _calculate_period_returns(self, return_type: str = "simple") -> pd.DataFrame:
        """
        YTD, MTD, Last Tuesday以降, 前日比のリターンを計算し、統合する。

        Parameters
        ----------
        return_type : str, default "simple"
            リターンの種類 ("simple" または "log")。

        Returns
        -------
        pd.DataFrame
            各期間のリターンを含むデータフレーム。
        """
        # Previous Day (前日比)
        # 最後の2日間の価格データをスライス
        price_prev_day = self.price_data.iloc[-2:]
        # 既存の計算メソッドを再利用してリターンを算出
        cum_return_prev_day = self.get_final_period_return(
            df_price=price_prev_day, return_type=return_type, period_name="prev_day"
        )

        # MTD
        price_mtd = self.get_data_since_period_start(
            self.price_data, date_column="Date", period_type="monthly"
        )
        cum_return_mtd = self.get_final_period_return(
            df_price=price_mtd, return_type=return_type, period_name="mtd"
        )

        # YTD
        price_ytd = self.get_data_since_period_start(
            self.price_data, date_column="Date", period_type="yearly"
        )
        cum_return_ytd = self.get_final_period_return(
            df_price=price_ytd, return_type=return_type, period_name="ytd"
        )

        # Last Tuesday
        last_tuesday_date = self._get_last_tuesday_date()
        price_last_tuesday = self.price_data.loc[
            self.price_data.index.date >= last_tuesday_date  # pyright: ignore[reportAttributeAccessIssue]
        ]
        cum_return_last_Tuesday = self.get_final_period_return(
            df_price=price_last_tuesday,
            return_type=return_type,
            period_name="last_Tuesday",
        )

        # 統合、整形、ソート
        cum_return = (
            cum_return_ytd.join(cum_return_mtd)
            .join(cum_return_last_Tuesday)
            .join(cum_return_prev_day)  # <- 追加
            .round(2)
        )

        # カラムの順序を直感的な順（短期 -> 長期）に入れ替え
        cum_return = cum_return[["prev_day", "last_Tuesday", "mtd", "ytd"]]

        # ソートキーを週次リターン（last_Tuesday）に設定
        cum_return.sort_values("last_Tuesday", ascending=False, inplace=True)

        return cum_return

    # -------------------------------------------------------------------------------------
    def get_performance_groups(self) -> dict:
        """
        セクターやグループごとのパフォーマンスを辞書形式で返す。

        Returns
        -------
        dict
            各グループのパフォーマンスデータフレームを含む辞書。
        """
        cum_return = self.performance_table

        # 辞書値はセクター名（英語）のリストに変換
        sector_names = list(self.SECTOR_MAP_EN.values())

        return {
            "Mag7_SOX": cum_return.loc[
                cum_return.index.isin(self.TICKERS_MAG7_AND_SOX)
            ],
            # "World": cum_return.loc[cum_return.index.isin(self.TICKERS_WORLD)],
            "US_and_SP500_Indices": cum_return.loc[
                cum_return.index.isin(self.TICKERS_US_AND_SP500)
            ],
            "Sector": cum_return.loc[cum_return.index.isin(sector_names)],
            "Metals": cum_return.loc[cum_return.index.isin(self.TICKERS_METAL)],
            "Oil": cum_return.loc[cum_return.index.isin(self.TICKERS_OIL)],
            "Market_Sentiment": cum_return.loc[
                cum_return.index.isin(self.TICKERS_MARKET)
            ],
        }

    # -------------------------------------------------------------------------------------
    ## プロット関数
    # -------------------------------------------------------------------------------------

    def _plot_lines(self, tickers_or_sectors: List[str], title: str):
        """
        汎用の累積リターン折れ線グラフ描画メソッド。

        Parameters
        ----------
        tickers_or_sectors : List[str]
            プロットするティッカーまたはセクターのリスト。
        title : str
            グラフのタイトル。
        """

        # cum_return_plot の列名が、引数のリストに含まれているものに絞り込まれる
        plot_df = self.price_data[tickers_or_sectors]
        plot_df = plot_df.loc[f"{datetime.date.today().year}-01-01" :]
        # 累積リターン
        plot_df = plot_df.div(plot_df.iloc[0]).dropna(how="all")

        fig = go.Figure()
        for ticker in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df[ticker],
                    mode="lines",
                    name=(
                        self.SECTOR_MAP_EN[ticker]
                        if ticker.startswith("XL")
                        else ticker
                    ),
                    line=dict(width=0.8),
                ),
            )
        fig.update_layout(
            width=850,
            height=450,
            template="plotly_dark",
            title=title,
            hovermode="x",
            legend=dict(
                yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"
            ),
            margin=dict(l=30, r=30, t=50, b=30),
        )
        fig.show()

    # -------------------------------------------------------------------------------------
    def plot_sp500_indices(self):
        """
        S&P 500 インデックスのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_US_AND_SP500, "S&P 500 Indices Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_world_indices(self):
        """
        全世界インデックスのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_WORLD, "World Indices Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_mag7_sox(self):
        """
        Mag7とSOX指数のYTDパフォーマンスをプロットする。
        """
        self._plot_lines(
            self.TICKERS_MAG7_AND_SOX, "Mag7 and SOX Index Performance YTD"
        )

    # -------------------------------------------------------------------------------------
    def plot_sector_performance(self):
        """
        S&P 500 セクターのYTDパフォーマンスをプロットする。
        """
        # セクター名（英語名）をリストとして渡す
        sector_names = list(self.SECTOR_MAP_EN)
        self._plot_lines(sector_names, "S&P 500 Sector Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_metal(self):
        """
        金属のYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_METAL, "Metals Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_oil(self):
        """
        WTIのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_OIL, "Oil Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_market_sentiment(self):
        """
        市場センチメントのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_MARKET, "Market Sentiment Performance YTD")

    # -------------------------------------------------------------------------------------


# =========================================================================================
def apply_df_style(df: pd.DataFrame):
    """
    データフレームにスタイルを適用する。

    Parameters
    ----------
    df : pd.DataFrame
        スタイルを適用するデータフレーム。

    Returns
    -------
    pandas.io.formats.style.Styler
        スタイルが適用されたオブジェクト。
    """
    bar_columns = ["prev_day", "last_Tuesday", "mtd", "ytd"]

    # 小数点以下2桁にフォーマットする辞書を作成
    # 注: format()は数値の列全てに適用されるように設定しています。

    # スタイルを適用し、表示桁数を設定
    return df.style.bar(
        subset=bar_columns,
        align="zero",
        color=["red", "green"],
    ).format({col: "{:.2f}" for col in bar_columns})


# =========================================================================================
def plot_vix_and_high_yield_spread():
    """
    VIXと米国ハイイールドスプレッドの推移をプロットする関数。
    """

    # データdownload
    fred_series_list = ["VIXCLS", "BAMLH0A0HYM2"]
    db_path = Path().cwd().parent / "data/FRED/FRED.db"
    fred = FredDataProcessor()
    df = pd.pivot(
        fred.load_data_from_database(db_path=db_path, series_id_list=fred_series_list),
        index="date",
        columns="variable",
        values="value",
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
    db_path = Path().cwd().parent / "data/FRED/FRED.db"
    fred = FredDataProcessor()
    df = pd.pivot(
        fred.load_data_from_database(db_path=db_path, series_id_list=fred_series_list),
        index="date",
        columns="variable",
        values="value",
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


# =========================================================================================
class TSAPassengerDataCollector:
    """
    ウェブスクレイピングを用いて、TSA Passengerデータを収集するクラス。
    """

    def __init__(self):
        self.url = "https://www.tsa.gov/travel/passenger-volumes"

    def scrape_tsa_passenger_data(
        self,
        year=None,
    ):
        """
        TSAの旅客数データをスクレイピングしてDataFrameを返す関数

        Parameters
        ----------
        year : int, optional
            取得したい特定の年（2019から）。指定しない場合は最新のデータを取得。

        Returns
        -------
        pd.DataFrame or None
            旅客数データを含むデータフレーム。取得に失敗した場合はNone。
        """

        url = self.url
        if year:
            url = f"{self.url}/{year}"

        try:
            # ウェブページを取得
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table")

            if not table:
                print("テーブルが見つかりませんでした")
                return None

            # データを格納するリスト
            dates = []
            numbers = []

            # テーブルの行を処理
            rows = table.find("tbody").find_all("tr")  # pyright: ignore[reportOptionalMemberAccess]

            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    # 日付を取得（テキストをクリーンアップ）
                    date_text = cells[0].get_text(strip=True)

                    # 数値を取得（カンマを除去して整数に変換）
                    number_text = cells[1].get_text(strip=True)
                    number_clean = re.sub(r"[,]", "", number_text)

                    try:
                        # 日付を標準形式に変換
                        date_obj = datetime.datetime.strptime(date_text, "%m/%d/%Y")

                        dates.append(date_obj)
                        numbers.append(int(number_clean))

                    except (ValueError, TypeError) as e:
                        print(f"データ変換エラー: {date_text}, {number_text} - {e}")
                        continue

            # DataFrameを作成
            df = (
                pd.DataFrame({"Date": dates, "Numbers": numbers})
                .assign(Date=lambda x: pd.to_datetime(x["Date"]))
                .sort_values("Date", ascending=False)
                .reset_index(drop=True)
            )

            return df

        except requests.exceptions.RequestException as e:
            print(f"ウェブページの取得に失敗しました: {e}")
            return None
        except Exception as e:
            print(f"予期しないエラーが発生しました: {e}")
            return None

    def display_data_info(self, df: pd.DataFrame):
        """
        データフレームの基本情報を表示する。

        Parameters
        ----------
        df : pd.DataFrame
            情報を表示するデータフレーム。
        """
        if df is not None:
            print("=== TSA旅客数データ ===")
            print(
                f"データ期間: {df['Date'].min().strftime('%Y/%m/%d')} - {df['Date'].max().strftime('%Y/%m/%d')}"
            )
            print(f"データ件数: {len(df)}件")
            print(
                f"最大旅客数: {df['Numbers'].max():,}人 ({df.loc[df['Numbers'].idxmax(), 'Date'].strftime('%Y/%m/%d')})"
            )

            print(
                f"最小旅客数: {df['Numbers'].min():,}人 ({df.loc[df['Numbers'].idxmin(), 'Date'].strftime('%Y/%m/%d')})"
            )
            print(f"平均旅客数: {df['Numbers'].mean():.0f}人")
            print("\n=== 最新10件のデータ ===")
            print(df.head(10).to_string(index=False))

    def save_to_csv(self, df: pd.DataFrame, filename: str = "tsa_passenger_data.csv"):
        """
        DataFrameをCSVファイルに保存する関数

        Parameters
        ----------
        df : pd.DataFrame
            保存するデータフレーム。
        filename : str, default "tsa_passenger_data.csv"
            保存するファイル名。
        """
        try:
            df.to_csv(filename, index=False)
            print(f"\nデータを '{filename}' に保存しました")
        except Exception as e:
            print(f"CSVファイルの保存に失敗しました: {e}")

    def store_to_tsa_database(
        self, df: pd.DataFrame, db_path: str | Path, table_name: str = "tsa_passenger"
    ):
        """
        DataFrameをSQLiteデータベースに保存する関数。
        既存のデータがある場合は、新しい日付のデータのみを追加する。

        Parameters
        ----------
        df : pd.DataFrame
            保存するデータフレーム。
        db_path : str | Path
            データベースファイルのパス。
        table_name : str, default "tsa_passenger"
            保存先のテーブル名。
        """
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # テーブルが存在するか確認
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                # 既存の全日付をセットとして取得
                existing_dates = set(
                    pd.read_sql(f"SELECT Date FROM {table_name}", conn)["Date"]
                )
                # 新しいデータのうち、DBに存在しない日付の行のみを抽出
                df["Date_str"] = df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
                df_to_add = df[~df["Date_str"].isin(existing_dates)].drop(
                    columns=["Date_str"]
                )
            else:
                # テーブルが存在しない場合は全データを追加対象とする
                df_to_add = df

            print(f"{'-' * 20} + TSA Passenger Data + {'-' * 20}")
            if not df_to_add.empty:
                print(
                    f"{len(df_to_add)}件の新規データをテーブル '{table_name}' に追加します。"
                )
                df_to_add.to_sql(table_name, conn, if_exists="append", index=False)
            else:
                print("追加する新規データはありませんでした。")

        except sqlite3.Error as e:
            print(f"データベースエラーが発生しました: {e}")
        finally:
            if conn:
                conn.close()

    def plot_passenger_trend(self, df_passenger: pd.DataFrame, fig_save_path=None):
        """
        旅客数の推移をプロットする関数
        """
        g_passenger = (
            df_passenger.resample("ME")
            .agg(Numbers=("Numbers", "sum"))
            .assign(Numbers_Change_YOY=lambda df: df["Numbers"].pct_change(12) * 100)
            .dropna()
        )

        # --- plot ---

        fig, ax = plt.subplots(figsize=(10, 5), tight_layout=True)
        ax.set_title(
            f"TSA checkpoint passenger numbers (as of {df_passenger.index.max().strftime('%Y-%m-%d')})"
        )
        ax.bar(
            g_passenger.index,
            g_passenger["Numbers"],
            width=25,
            align="center",
            label="Num. of Passengers",
            alpha=0.5,
            color="blue",
        )
        ax.set_xlabel("Year-Month")
        ax.set_ylabel("Number of Passengers(Millions)")
        ax.yaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, pos: f"{int(x / 1000000)}")
        )

        ax_sub = ax.twinx()
        sns.lineplot(
            data=g_passenger,
            x=g_passenger.index,
            y="Numbers_Change_YOY",
            ax=ax_sub,
            color="green",
            label="YOY (%)",
            marker="o",
            markersize=4,
        )

        # legend
        handler1, label1 = ax.get_legend_handles_labels()
        handler2, label2 = ax_sub.get_legend_handles_labels()
        ax.legend(handler1 + handler2, label1 + label2, loc="lower right")
        # 服軸に自動で作成された判例を削除
        if ax_sub.get_legend() is not None:
            ax_sub.get_legend().remove()

        ax_sub.set_ylim(-100, 100)
        ax_sub.set_ylabel("YOY (%)")
        ax_sub.grid(color="black", linewidth=0.2, linestyle="--")
        ax_sub.yaxis.set_major_formatter(mtick.PercentFormatter())

        # x-axis date format
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate(rotation=90)

        # ax.set_xlim(left=pd.to_datetime("2019-10-31"))

        plt.show()
        if fig_save_path:
            plt.savefig(fig_save_path, dpi=300)
        else:
            return fig


# =========================================================================================
class BloombergDataProcessor:
    def __init__(self):
        """
        BloombergDataProcessorクラスを初期化する。
        環境変数からディレクトリパスを読み込み、必要なファイルやデータベースの存在を確認する。
        """
        load_dotenv()
        self.data_dir = Path(os.environ.get("BLOOMBERG_ROOT_DIR"))  # type: ignore
        self.sp_price_excel = self.data_dir / "SP500-Indices.xlsx"
        # sp_price_excelが見つからない場合
        if not self.sp_price_excel.exists():
            print(f"ファイル '{self.sp_price_excel}' が見つかりません。")
        self.sp_price_db = self.data_dir / "SP_Indices_Price.db"
        if not self.sp_price_db.exists():
            print(f"データベースファイル '{self.sp_price_db}' が見つかりません。")
            print("新しくデータベースを作成します。")
            self.store_sp_indices_price_to_database()
        self.sp_members_excel = self.data_dir / "SP500-Constituents.xlsx"
        if not self.sp_members_excel.exists():
            print(f"ファイル '{self.sp_members_excel}' が見つかりません。")
        else:
            self._store_sp500_members()

    # -------------------------------------------------------------------------------------
    def store_sp_indices_price_to_database(self, excel_path=None, db_path=None) -> None:
        """
        BQLでダウンロードしたS&P500のセクターインデックスとインダストリーインデックスの
        priceデータをsqlite3データベースに保存する関数
        """

        TABLE_NAME = "sp_indices_price"
        if excel_path is None:
            excel_path = self.sp_price_excel
        if db_path is None:
            db_path = self.sp_price_db

        try:
            # 1. Excelファイルの読み込みと前処理
            # BQLの出力形式を想定し、1行目をヘッダー、最初の列を日付として読み込む
            print(f"Reading data from '{excel_path.name}'...")
            df = pd.melt(
                pd.read_excel(excel_path, sheet_name="Price")
                .rename(columns={"Unnamed: 0": "Date"})
                .sort_values("Date"),
                id_vars=["Date"],
                var_name="Ticker",
                value_name="value",
            ).assign(variable="Price")
            df["Date"] = pd.to_datetime(df["Date"])
            df["value"] = df["value"].astype(float)

            print(f"Successfully loaded and reshaped {len(df)} rows from Excel.")

            # 2. データベース接続
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 3. 差分更新ロジック
            # テーブルが存在するか確認
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'"
            )
            table_exists = cursor.fetchone()

            df_to_add = pd.DataFrame()

            if table_exists:
                # テーブルが存在する場合、最新の日付を取得
                latest_date_str = pd.read_sql(
                    f"SELECT MAX(Date) FROM {TABLE_NAME}", conn
                ).iloc[0, 0]

                if latest_date_str:
                    latest_date = pd.to_datetime(latest_date_str)  # type: ignore
                    # Excelデータから最新日より後のデータを抽出
                    df_to_add = df[df["Date"] > latest_date].copy()
                    print(
                        f"Database latest date: {latest_date.date()}. Found {len(df_to_add)} new rows to add."
                    )
                else:
                    # テーブルは存在するが空の場合
                    df_to_add = df.copy()
            else:
                # テーブルが存在しない場合、全てのデータを追加対象とする
                df_to_add = df.copy()
                print(
                    f"Table '{TABLE_NAME}' not found. Creating a new table with {len(df_to_add)} rows."
                )

            # 4. 差分データをデータベースに書き込み
            if not df_to_add.empty:
                df_to_add.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
                print(
                    f"Successfully wrote {len(df_to_add)} rows to '{TABLE_NAME}' in '{db_path.name}'."
                )

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if "conn" in locals() and conn:  # type: ignore
                conn.close()

    # -------------------------------------------------------------------------------------
    def load_sp_indices_price_from_database(
        self, db_path: Optional[Path] = None, tickers: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        SQLiteデータベースからS&Pインデックスの価格データを読み込み、DataFrameとして返す。

        Args:
            db_path (Path, optional): データベースファイルのパス。指定しない場合はインスタンスのデフォルトパスを使用。
            tickers (List[str], optional): 読み込むティッカーのリスト。指定しない場合は全ティッカーを読み込む。

        Returns:
            pd.DataFrame: 読み込んだ価格データ。データが存在しない場合は空のDataFrameを返す。
        """
        TABLE_NAME = "sp_indices_price"
        if db_path is None:
            db_path = self.sp_price_db

        if not db_path.exists():
            print(f"データベースファイル '{db_path}' が見つかりません。")
            return pd.DataFrame()

        conn = None
        try:
            conn = sqlite3.connect(db_path)

            query = f"SELECT * FROM {TABLE_NAME}"
            params: Optional[List[str]] = None

            if tickers:
                placeholders = ", ".join("?" for _ in tickers)
                query += f" WHERE Ticker IN ({placeholders})"
                params = tickers

            df = pd.read_sql_query(query, conn, params=params)  # type:ignore
            df["Date"] = pd.to_datetime(df["Date"])
            print(f"Successfully loaded {len(df)} rows from '{db_path.name}'.")
            return df

        except Exception as e:
            print(f"An error occurred while reading from the database: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

    # -------------------------------------------------------------------------------------
    def get_current_sp_members(self) -> list[str]:
        """
        BloombergでダウンロードしたSP500構成銘柄のティッカーをlistで返す関数
        """

        tickers = []
        df = pd.read_excel(self.sp_members_excel, sheet_name="current members")
        tickers = df["ID"].unique().tolist()
        return tickers

    # -------------------------------------------------------------------------------------
    def _store_sp500_members(self):
        """
        ExcelファイルからS&P 500構成銘柄データを読み込み、SQLiteデータベースに保存する内部メソッド。
        """
        TABLE_NAME = "Members"

        df = (
            pd.melt(
                pd.read_excel(self.sp_members_excel, sheet_name="current members")[
                    [
                        "ID",
                        "DATES",
                        "market_cap",
                        "gics_sector_name",
                        "gics_industry_group_name",
                        "gics_industry_name",
                        "gics_sub_industry_name",
                    ]
                ],
                id_vars=["ID"],
                var_name="variable",
                value_name="values",
            )
            .dropna(subset=["values"], ignore_index=True)
            .rename(columns={"ID": "Ticker"})
            .assign(
                Ticker=lambda x: x["Ticker"]
                .str.replace("/", "-")
                .str.split(" ", expand=True)[0],
            )
        ).sort_values("Ticker", ignore_index=True)
        df = (
            pd.pivot(df, index="Ticker", columns="variable", values="values")
            .reset_index()
            .rename(columns={"DATES": "date"})
            .assign(date=lambda x: pd.to_datetime(x["date"]))
        ).reindex(
            columns=[
                "date",
                "Ticker",
                "gics_sector_name",
                "gics_industry_group_name",
                "gics_industry_name",
                "gics_sub_industry_name",
                "market_cap",
            ]
        )

        try:
            # 2. データベース接続
            conn = sqlite3.connect(self.sp_price_db)
            cursor = conn.cursor()

            # 3. 差分更新ロジック
            # テーブルが存在するか確認
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'"
            )
            table_exists = cursor.fetchone()

            df_to_add = pd.DataFrame()

            if table_exists:
                # テーブルが存在する場合、最新の日付を取得
                latest_date_str = pd.read_sql(
                    f"SELECT MAX(Date) FROM {TABLE_NAME}", conn
                ).iloc[0, 0]

                if latest_date_str:
                    latest_date = pd.to_datetime(latest_date_str)  # type: ignore
                    # Excelデータから最新日より後のデータを抽出
                    df_to_add = df[df["Date"] > latest_date].copy()
                    print(
                        f"Database latest date: {latest_date.date()}. Found {len(df_to_add)} new rows to add."
                    )
                else:
                    # テーブルは存在するが空の場合
                    df_to_add = df.copy()
            else:
                # テーブルが存在しない場合、全てのデータを追加対象とする
                df_to_add = df.copy()
                print(
                    f"Table '{TABLE_NAME}' not found. Creating a new table with {len(df_to_add)} rows."
                )

            # 4. 差分データをデータベースに書き込み
            if not df_to_add.empty:
                df_to_add.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
                print(
                    f"Successfully wrote {len(df_to_add)} rows to '{TABLE_NAME}' in '{self.sp_price_db.name}'."
                )

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if "conn" in locals() and conn:  # type: ignore
                conn.close()

    # --------------------------------------------------------------------------------
    def delete_table_from_db(self, db_path: Path, table_name: str):
        """
        指定されたSQLiteデータベースから特定のテーブルを削除する。

        Parameters
        ----------
        db_path : Path
            SQLiteデータベースファイルへのパス (pathlib.Path オブジェクト)。
        table_name : str
            削除するテーブル名。
        """

        # 1. テーブル名の簡易検証 (SQLインジェクション対策)
        # 英数字とアンダースコアのみを許可
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            print(
                f"エラー: '{table_name}' は無効なテーブル名です。処理を中止しました。"
            )
            return

        # 2. SQLコマンドの準備
        # テーブル名のような識別子はパラメータ化(?)できないため、f-stringを使用
        # "IF EXISTS" を付けることで、テーブルが存在しなくてもエラーにならない
        # 識別子をダブルクォートで囲み、安全性を高める
        sql_command = f'DROP TABLE IF EXISTS "{table_name}"'

        try:
            # 3. 'with' ステートメントでデータベースに接続
            # ブロック終了時に自動的にコミット(正常時)またはロールバック(異常時)され、
            # 接続がクローズされます。
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # 4. SQLの実行
                cursor.execute(sql_command)

            print(
                f"テーブル '{table_name}' をデータベース ({db_path.name}) から正常に削除しました。"
            )

        except sqlite3.Error as e:
            print(f"データベースエラーが発生しました: {e}")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")


# =========================================================================================
def rolling_correlation(df_price: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    ターゲットとなるインデックスと特定銘柄のローリング相関係数を計算する関数
    Args:
        df_price: pd.DataFrame, 価格データ. Date, Ticker, valueの列を持つ
        target_col: str, ターゲットとなるインデックスの列名

    """
    df_return = df_price.sort_values("Date", ignore_index=True)
    for period in [1, 20, 20 * 3, 20 * 6, 252]:
        colname = "1d" if period == 1 else f"{int(period // 20)}m"
        df_return[f"return_{colname}"] = df_return.groupby("Ticker")[
            "value"
        ].pct_change(period)
    df_return.drop(columns=["value"], inplace=True)

    # 相関係数
    dfs_corr = []
    for return_col in [col for col in df_return.columns if col.startswith("return")]:
        period = re.split("_", return_col)[-1]
        rtn = pd.pivot(df_return, index="Date", columns="Ticker", values=return_col)
        corr = pd.melt(
            (
                rtn.rolling(window=252, min_periods=30)
                .corr(rtn[target_col])
                .drop(columns=[target_col])
                .dropna(how="all")
                .reset_index()
            ),
            id_vars=["Date"],
            var_name="Ticker",
            value_name="value",
        ).assign(variable=f"corr_{period}_chg_12M_roll")
        dfs_corr.append(corr)

    df_corr = pd.concat(dfs_corr).sort_values(["Date", "Ticker"], ignore_index=True)

    return df_corr


# =========================================================================================
def plot_rolling_correlation(
    df_corr: pd.DataFrame, ticker_to_plot: str, target_index_name: str
):
    """
    ローリング相関係数の推移をプロットする関数。

    Parameters
    ----------
    df_corr : pd.DataFrame
        相関係数データを含むデータフレーム。
    ticker_to_plot : str
        プロット対象のティッカーシンボル。
    target_index_name : str
        ターゲットとなるインデックスの名前（グラフタイトル用）。

    Returns
    -------
    plotly.graph_objects.Figure
        作成されたPlotlyのFigureオブジェクト。
    """

    fig = go.Figure()
    periods_ordered = ["1d", "1m", "3m", "6m", "12m"]
    num_colors = len(periods_ordered)
    sample_points = [i / (num_colors - 1) for i in range(num_colors)]
    colors_plasma = px.colors.sample_colorscale("GnBu", sample_points)
    color_map = dict(zip(periods_ordered, colors_plasma, strict=False))

    df_slice = pd.pivot(
        df_corr.loc[df_corr["Ticker"] == ticker_to_plot],
        index="Date",
        columns="variable",
        values="value",
    )
    df_slice = df_slice.reindex(
        columns=[f"corr_{s}_chg_12M_roll" for s in periods_ordered]
    )
    for col in df_slice.columns:
        period = col.replace("corr_", "").replace("_chg_12M_roll", "")

        color = color_map[period]
        fig.add_trace(
            go.Scatter(
                x=df_slice.index,
                y=df_slice[col],
                mode="lines",
                line=dict(width=0.8, color=color),
                name=period,
            ),
        )

    fig.add_hline(y=0.0, line_dash="dash", line_color="gray")

    fig.update_yaxes(range=[-1, 1])
    fig.update_layout(
        width=1000,
        height=300,
        template="plotly_dark",
        hovermode="x",
        title=f"{ticker_to_plot}: Rolling Correlation with {target_index_name}",
        legend=dict(
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            orientation="h",
            title="Price change period",
        ),
        margin=dict(l=30, r=30, t=50, b=30),
    )

    return fig


# =========================================================================================
def calculate_kalman_beta(
    df_price: pd.DataFrame,
    target_col: str,
    freq: Literal["W", "M"],
    window_years: Literal[3, 5],
    rolling_window: int = 60,
) -> pd.DataFrame:
    """
    カルマンフィルタを使用して時変ベータを推定する関数。

    状態空間モデル:
    - 観測方程式: r_s,t = α + β_t * r_m,t + ε_t
    - 状態方程式: β_t = β_{t-1} + η_t

    Args:
        df_price (pd.DataFrame): 価格データ. Date, Ticker, valueの列を持つ
        target_col (str): ターゲットとなるインデックスの列名（市場リターン）
        freq (str): リターン計算の頻度 ('W' for 週次, 'M' for 月次)
        window_years (int): リターン計算の期間（3年または5年）
        rolling_window (int): 初期値推定用のウォームアップ期間（使用されるが、全期間でカルマンフィルタを適用）

    Returns:
        pd.DataFrame: カルマンフィルタで推定された時変ベータ値
    """
    from statsmodels.tsa.statespace.mlemodel import MLEModel

    # Date列をDatetime型にし、インデックスに設定
    df_price["Date"] = pd.to_datetime(df_price["Date"])

    # 1. 指定頻度でのリターン計算
    df_periodic = (
        df_price.set_index("Date")
        .groupby("Ticker")
        .resample(freq)["value"]
        .last()
        .reset_index()
    )

    df_return = df_periodic.sort_values(["Ticker", "Date"]).copy()

    # 期間に対応するpct_changeのlag（遅延）を設定
    if freq == "M":
        lag = window_years * 12
        freq_label = f"{window_years}y_m"
    elif freq == "W":
        lag = window_years * 52
        freq_label = f"{window_years}y_w"
    else:
        raise ValueError("freqは 'W' (週次) または 'M' (月次) である必要があります。")

    # リターンを計算
    df_return["returns"] = df_return.groupby("Ticker")["value"].pct_change(lag)

    # 不要な列を削除し、ピボット用に整形
    df_return.drop(columns=["value"], inplace=True)
    rtn = pd.pivot_table(
        df_return, index="Date", columns="Ticker", values="returns"
    ).dropna(how="all")

    # 2. カルマンフィルタによるベータ推定
    market_returns = rtn[target_col].dropna()
    tickers = [col for col in rtn.columns if col != target_col]

    # カスタム状態空間モデルクラス
    class TimevaryingBetaModel(MLEModel):
        def __init__(self, endog, exog):
            # endog: 個別銘柄リターン
            # exog: 市場リターン
            super().__init__(
                endog, k_states=1, exog=exog, initialization="approximate_diffuse"
            )

            # 状態空間表現の設定
            # 観測方程式: y_t = d + Z * β_t + ε_t
            self["design"] = np.array([[1.0]])  # Z (1x1)
            self["obs_intercept"] = np.array([0.0])  # d
            self["obs_cov"] = np.array([[1.0]])  # H (観測誤差分散)

            # 状態方程式: β_t = c + T * β_{t-1} + η_t
            self["transition"] = np.array([[1.0]])  # T (ランダムウォーク)
            self["state_intercept"] = np.array([0.0])  # c
            self["state_cov"] = np.array([[0.01]])  # Q (状態誤差分散、初期値)

        @property
        def param_names(self):
            return ["obs_var", "state_var"]

        @property
        def start_params(self):
            return np.array([1.0, 0.01])

        def update(self, params, **kwargs):
            params = super().update(params, **kwargs)
            # パラメータを状態空間モデルに反映
            self["obs_cov", 0, 0] = params[0]  # 観測誤差分散
            self["state_cov", 0, 0] = params[1]  # 状態誤差分散

    # 各銘柄に対してカルマンフィルタを適用
    beta_results = []

    for ticker in tickers:
        # 共通のインデックスでデータを揃える
        stock_returns = rtn[ticker].dropna()
        common_idx = stock_returns.index.intersection(market_returns.index)

        if len(common_idx) < rolling_window:
            # データが不足している場合はスキップ
            continue

        y = stock_returns.loc[common_idx].values
        X = market_returns.loc[common_idx].values.reshape(-1, 1)

        # 初期値の推定（最初のrolling_window期間でOLS）
        warmup_y = y[:rolling_window]
        warmup_X = X[:rolling_window]

        # 説明変数に市場リターンを含める（外生変数として）
        # 観測方程式を y_t = α + β_t * X_t + ε_t の形にするため、
        # 観測値を y_t - α と変換し、design行列をX_tにする

        # OLSで初期アルファとベータを推定
        from scipy.stats import linregress

        slope_init, intercept_init, _, _, _ = linregress(warmup_X.flatten(), warmup_y)

        # モデルの構築（外生変数を使わず、観測値を調整する方法）
        # y_adjusted = y - intercept (アルファを除去)
        # 観測方程式: y_adjusted_t = β_t * X_t + ε_t

        # design行列をX_tに設定するため、時変にする必要がある
        # statsmodelsのカルマンフィルタは時変design行列をサポート

        # より簡単な実装: カルマンフィルタを手動実装
        # または、pykalmanを使用

        try:
            from pykalman import KalmanFilter

            # 観測行列を市場リターンに設定（時変）
            observation_matrices = X.reshape(-1, 1, 1)  # (T, 1, 1)

            # カルマンフィルタの設定
            kf = KalmanFilter(
                transition_matrices=np.array([[1.0]]),  # ランダムウォーク
                observation_matrices=observation_matrices,
                transition_covariance=np.array([[0.001]]),  # 状態ノイズ（小さい値）
                observation_covariance=np.array([[np.var(y)]]),  # 観測ノイズ
                initial_state_mean=np.array([slope_init]),
                initial_state_covariance=np.array([[1.0]]),
                n_dim_state=1,
                n_dim_obs=1,
            )

            # EMアルゴリズムでパラメータを学習
            kf = kf.em(y.reshape(-1, 1), n_iter=10)

            # フィルタリングとスムージング
            state_means, _ = kf.filter(y.reshape(-1, 1))

            # 結果を格納
            for i, date in enumerate(common_idx):
                beta_results.append(
                    {"Date": date, "Ticker": ticker, "value": state_means[i, 0]}
                )

        except ImportError:
            # pykalmanがインストールされていない場合は警告
            print(f"Warning: pykalman is not installed. Skipping ticker {ticker}")
            print("Install with: pip install pykalman")
            continue

    # 結果をDataFrameに変換
    if not beta_results:
        # 空の場合は、rolling_betaと同じ形式の空DataFrameを返す
        return pd.DataFrame(columns=["Date", "Ticker", "value", "variable"])

    df_beta = pd.DataFrame(beta_results)
    df_beta["variable"] = f"beta_{freq_label}_kalman_{window_years}years"
    df_beta = df_beta.sort_values(["Date", "Ticker"], ignore_index=True)

    return df_beta


# =========================================================================================
def rolling_beta(
    df_price: pd.DataFrame,
    target_col: str,
    freq: Literal["W", "M"],
    window_years: Literal[3, 5],
    rolling_window: int = 60,
) -> pd.DataFrame:
    """
    指定された頻度（週次/月次）と期間（3年/5年）のリターンに基づき、
    ローリング・ベータを計算する関数。

    Args:
        df_price (pd.DataFrame): 価格データ. Date, Ticker, valueの列を持つ
        target_col (str): ターゲットとなるインデックスの列名（市場リターン）
        freq (str): リターン計算の頻度 ('W' for 週次, 'M' for 月次)
        window_years (int): リターン計算の期間（3年または5年）
        rolling_window (int): ローリングベータ計算に使用する期間数 (例: 60ヶ月)

    Returns:
        pd.DataFrame: 計算されたローリング・ベータ値
    """
    # Date列をDatetime型にし、インデックスに設定
    df_price["Date"] = pd.to_datetime(df_price["Date"])

    # 1. 指定頻度でのリターン計算
    # Tickerごとにグループ化し、指定頻度の最終日（終値）を取得
    # これにより、日次データを週次/月次データにダウンサンプリングする
    df_periodic = (
        df_price.set_index("Date")
        .groupby("Ticker")
        .resample(freq)["value"]
        .last()
        .reset_index()
    )

    # グループ化されたデータでリターンを計算
    df_return = df_periodic.sort_values(["Ticker", "Date"]).copy()

    # 期間に対応するpct_changeのlag（遅延）を設定
    # 3年 = 36ヶ月 (M) または 156週 (W)
    # 5年 = 60ヶ月 (M) または 260週 (W)
    if freq == "M":
        lag = window_years * 12
        freq_label = f"{window_years}y_m"
    elif freq == "W":
        lag = window_years * 52
        freq_label = f"{window_years}y_w"
    else:
        raise ValueError("freqは 'W' (週次) または 'M' (月次) である必要があります。")

    # 複数期間のリターンを計算 (ベータ計算の直接の基礎となるデータ)
    df_return["returns"] = df_return.groupby("Ticker")["value"].pct_change(lag)

    # 不要な列を削除し、ピボット用に整形
    df_return.drop(columns=["value"], inplace=True)
    rtn = pd.pivot_table(
        df_return, index="Date", columns="Ticker", values="returns"
    ).dropna(how="all")

    # 2. ローリング・ベータの計算ロジック
    market_returns = rtn[target_col]

    def beta_function(window_data):
        # window_dataは個別銘柄のリターンを含むSeries
        rs = window_data
        rm = market_returns[window_data.index]  # 同じ期間の市場リターンを取得

        # ベータ = Cov(Rs, Rm) / Var(Rm)
        covariance = rs.cov(rm)
        market_variance = rm.var()

        if market_variance == 0 or pd.isna(market_variance):
            return np.nan

        return covariance / market_variance

    # 3. ローリング関数を適用
    # min_periodsを rolling_window // 3 などに設定し、データ不足でも計算できるようにするのも一般的
    MIN_PERIODS = 20

    beta_results = (
        # Ticker列（個別銘柄リターン）に対してローリングウィンドウを適用
        rtn.drop(columns=[target_col])
        .rolling(window=rolling_window, min_periods=MIN_PERIODS)
        .apply(beta_function, raw=False)
        .dropna(how="all")
        .reset_index()
    )

    # 4. 結果の整形
    df_beta = pd.melt(
        beta_results,
        id_vars="Date",
        var_name="Ticker",
        value_name="value",
    ).assign(variable=f"beta_{freq_label}_roll_{window_years}years")

    df_beta.sort_values(["Date", "Ticker"], ignore_index=True, inplace=True)

    return df_beta


# =========================================================================================
def plot_rolling_beta(
    df_beta: pd.DataFrame,
    freq: Literal["W", "M"],
    window_years: Literal[3, 5],
    tickers_to_plot: List[str],
    target_index_name: str,
    beta_variable_name: str | None = None,
):
    fig = go.Figure()
    # periods_ordered = ["1d", "1m", "3m", "6m", "12m"]
    # num_colors = len(periods_ordered)
    # sample_points = [i / (num_colors - 1) for i in range(num_colors)]
    # colors_plasma = px.colors.sample_colorscale("GnBu", sample_points)
    # color_map = dict(zip(periods_ordered, colors_plasma))

    if not beta_variable_name:
        beta_variable_name = (
            f"beta_{window_years}y_{freq.lower()}_roll_{window_years}years"
        )
    df_beta = pd.pivot(
        df_beta.loc[df_beta["variable"] == beta_variable_name],
        index="Date",
        columns="Ticker",
        values="value",
    )

    fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig.add_hline(y=0.0, line_dash="dot", line_color="light gray")

    for ticker in tickers_to_plot:
        fig.add_trace(
            go.Scatter(
                x=df_beta.index,
                y=df_beta[ticker],
                mode="lines",
                line=dict(width=0.8),
                name=ticker,
            ),
        )

    # fig.update_yaxes(range=[-4, 4])
    fig.update_layout(
        width=1000,
        height=250,
        template="plotly_dark",
        hovermode="x",
        title=f"Rolling Beta with {target_index_name}",
        legend=dict(yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"),
        margin=dict(l=30, r=30, t=50, b=50),
    )

    return fig


# =========================================================================================
class DollarsIndexAndMetalsAnalyzer:
    """
    ドル指数と金属価格の分析を行うクラス。
    """

    def __init__(self):
        """
        DollarsIndexAndMetalsAnalyzerクラスを初期化する。
        必要なデータプロセッサを初期化し、データをロードしてリターンを計算する。
        """
        self.db_path = Path().cwd().parent / "data/FRED/FRED.db"
        self.fred = FredDataProcessor()
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
    def plot_us_dollar_index_and_metal_price(self, df_cum_return: pd.DataFrame = None):
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


# =========================================================================================
