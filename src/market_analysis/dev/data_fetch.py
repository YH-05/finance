import datetime

import curl_cffi
import pandas as pd
from pandas.core.frame import DataFrame
import yfinance as yf

from src import fred_database_utils as fred_utils
from src import market_report_utils as mru
from src import us_treasury
from src.market_report import news


class YfinanceFethcer:
    """
    yfinanceからデータ取得するクラス
    """

    def __init__(self):
        self.today = datetime.date.today()
        self.session = curl_cffi.Session(impersonate="safari15_5")

    def yf_download(
        self, tickers: list[str], period: str = "2y", interval: str = "1d"
    ) -> pd.DataFrame:
        """
        yfinanceのダウンロードをcurl_cffiで代替する関数。

        Parameters
        ----------
        tickers : list[str]
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
        intra_day_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]
        datetime_col_name = None

        if interval in intra_day_intervals:
            datetime_col_name = "Datetime"
            df: pd.DataFrame = yf.download(
                tickers=tickers,
                period=period,
                interval=interval,
                prepost=False,
                group_by="ticker",
            )
            return df
        else:
            datetime_col_name = "Date"
            df: pd.DataFrame = (
                yf.download(
                    tickers=tickers,
                    period=period,
                    interval=interval,
                    session=self.session,
                    auto_adjust=False,
                )
                .stack(future_stack=True)
                .reset_index()
            )
            df: pd.DataFrame = pd.melt(
                df,
                id_vars=[datetime_col_name, "Ticker"],
                value_vars=df.columns.tolist()[2:],
                value_name="value",
                var_name="variable",
            )
            return df

    def get_performance(self, tickers: list[str]) -> pd.DataFrame:
        """複数Tickerの期間別パフォーマンスを取得する"""
        price: DataFrame = self.yf_download(tickers)
        price: DataFrame = price.loc[price["variable"] == "Adj Close"].pivot(
            index="Date", values="value", columns="Ticker"
        )
        periods = {"1d": 1, "5d": 5, "1m": 21, "3m": 63, "6m": 126, "1y": 252}

        df_performance = pd.DataFrame(
            {name: price.pct_change(periods=p).iloc[-1] for name, p in periods.items()}
        ).sort_values("5d", ascending=False)

        return df_performance

    # def get_sector_top_companies(self, sector: str) -> list[str]:
    #     """特定のセクターのtop companiesのsymbolを取得する"""
    #     yf_fetcher = YfinanceFethcer()
