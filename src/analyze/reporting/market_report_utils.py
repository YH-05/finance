"""
market_report_utils.py
"""

import datetime
import re
from typing import Literal

import curl_cffi
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

from utils_core.logging import get_logger

logger = get_logger(__name__)


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
    def get_eps_historical_data(self, tickers_to_download: list[str]) -> pd.DataFrame:
        """
        指定された複数の銘柄の実績EPS（Reported EPS）のヒストリカルデータを取得する。
        年次（annual）と四半期（quarterly）のデータが含まれます。

        Parameters
        ----------
        tickers_to_download : list[str]
            ティッカーシンボルのリスト（例: ["AAPL", "MSFT"]）

        Returns
        -------
        pd.DataFrame
            全銘柄の実績EPSデータを結合したDataFrame。
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

            except Exception:
                logger.error(
                    "Failed to fetch EPS data",
                    ticker=ticker,
                    exc_info=True,
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
                logger.warning(
                    "Previous year data not found, returning all data",
                    year=previous_year,
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
                ]

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
    ) -> pd.DataFrame:
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
            df_log_returns = np.log(df_price / df_price.shift(1)).dropna()
            result = (
                np.exp(
                    df_log_returns.sum()
                )  # 期間全体の累積対数リターンを計算し、expで通常リターンへ
                .sub(1)  # リターン率（例: 1.10 -> 0.10）
                .mul(100)  # %に変換（例: 0.10 -> 10.0）
                .rename(period_name)  # Tickerごとの結果に期間名を付ける
                .to_frame()  # DataFrameに変換
            )
            result = result.rename(index=self.SECTOR_MAP_EN)

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
            self.price_data.index.date >= last_tuesday_date
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

        return cum_return  # type: ignore[return-value]

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

    def _plot_lines(self, tickers_or_sectors: list[str], title: str):
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
    ).format(dict.fromkeys(bar_columns, "{:.2f}"))


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

        def update(self, params, **kwargs):  # type: ignore[override]
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

        slope_init, _intercept_init, _, _, _ = linregress(warmup_X.flatten(), warmup_y)

        # モデルの構築（外生変数を使わず、観測値を調整する方法）
        # y_adjusted = y - intercept (アルファを除去)
        # 観測方程式: y_adjusted_t = β_t * X_t + ε_t

        # design行列をX_tに設定するため、時変にする必要がある
        # statsmodelsのカルマンフィルタは時変design行列をサポート

        # より簡単な実装: カルマンフィルタを手動実装
        # または、pykalmanを使用

        try:
            from pykalman import KalmanFilter  # type: ignore[import-not-found]

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
            logger.warning(
                "pykalman not installed, skipping Kalman beta",
                ticker=ticker,
            )
            continue

    # 結果をDataFrameに変換
    if not beta_results:
        # 空の場合は、rolling_betaと同じ形式の空DataFrameを返す
        return pd.DataFrame(columns=["Date", "Ticker", "value", "variable"])  # type: ignore[arg-type]

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

        if market_variance == 0 or pd.isna(market_variance):  # type: ignore[comparison-overlap]
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
    tickers_to_plot: list[str],
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
