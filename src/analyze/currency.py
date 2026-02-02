"""currency.py

ドル指数と金属価格の統合分析モジュール。

FREDからドル指数データを、yfinanceから金属ETF価格を取得し、
統合分析と累積リターン計算を行う。

対象データ:
- DTWEXAFEGS: Nominal Advanced Foreign Economies U.S. Dollar Index (FRED)
- GLD: SPDR Gold Shares (金)
- SLV: iShares Silver Trust (銀)
- PPLT: abrdn Physical Platinum Shares ETF (プラチナ)
- CPER: United States Copper Index Fund (銅)
- PALL: abrdn Physical Palladium Shares ETF (パラジウム)
- DBB: Invesco DB Base Metals Fund (ベースメタル)
"""

from datetime import datetime
from typing import Any

import pandas as pd
from pandas import DataFrame

from market.fred import HistoricalCache
from market.yfinance import FetchOptions, YFinanceFetcher
from utils_core.logging import get_logger


class DollarsIndexAndMetalsAnalyzer:
    """ドル指数と金属価格の分析を行うクラス.

    FREDからドル指数（DTWEXAFEGS）を、yfinanceから金属ETF価格を取得し、
    統合分析と累積リターン計算を行う。

    Attributes
    ----------
    metal_tickers : list[str]
        分析対象の金属ETFティッカーリスト
    dollar_index_series : str
        ドル指数のFREDシリーズID

    Examples
    --------
    >>> analyzer = DollarsIndexAndMetalsAnalyzer()
    >>> price_df = analyzer.load_price()
    >>> cum_return = analyzer.calc_return(start_date="2020-01-01")
    >>> summary = analyzer.get_summary()
    """

    # デフォルトの金属ETFティッカー
    DEFAULT_METAL_TICKERS: list[str] = ["GLD", "SLV", "PPLT", "CPER", "PALL", "DBB"]

    # ドル指数のFREDシリーズID
    DOLLAR_INDEX_SERIES: str = "DTWEXAFEGS"

    def __init__(self) -> None:
        """DollarsIndexAndMetalsAnalyzer を初期化する.

        FREDキャッシュとyfinanceフェッチャーを初期化し、
        ドル指数データの存在を確認する。

        Raises
        ------
        ValueError
            FREDからドル指数データが取得できない場合
        """
        self.logger = get_logger(__name__, component="DollarsIndexAndMetalsAnalyzer")
        self._fred_cache: HistoricalCache | None = None
        self._yf_fetcher: YFinanceFetcher | None = None

        # ドル指数データの存在確認
        dollar_df = self.load_dollar_index()
        if dollar_df is None or dollar_df.empty:
            msg = (
                f"Failed to load {self.DOLLAR_INDEX_SERIES} from FRED cache. "
                "Please ensure the data is synced using HistoricalCache.sync_series()."
            )
            self.logger.error(msg, series_id=self.DOLLAR_INDEX_SERIES)
            raise ValueError(msg)

        self.logger.debug(
            "DollarsIndexAndMetalsAnalyzer initialized",
            metal_tickers=self.metal_tickers,
            dollar_index_series=self.DOLLAR_INDEX_SERIES,
        )

    @property
    def metal_tickers(self) -> list[str]:
        """分析対象の金属ETFティッカーを返す.

        Returns
        -------
        list[str]
            金属ETFティッカーのリスト
        """
        return self.DEFAULT_METAL_TICKERS.copy()

    @property
    def dollar_index_series(self) -> str:
        """ドル指数のFREDシリーズIDを返す.

        Returns
        -------
        str
            FREDシリーズID
        """
        return self.DOLLAR_INDEX_SERIES

    def _get_fred_cache(self) -> HistoricalCache:
        """FRED HistoricalCache インスタンスを取得する.

        Returns
        -------
        HistoricalCache
            FREDデータキャッシュマネージャー
        """
        if self._fred_cache is None:
            self._fred_cache = HistoricalCache()
            self.logger.debug("HistoricalCache created")
        return self._fred_cache

    def _get_yf_fetcher(self) -> YFinanceFetcher:
        """YFinanceFetcher インスタンスを取得する.

        Returns
        -------
        YFinanceFetcher
            yfinanceデータ取得クライアント
        """
        if self._yf_fetcher is None:
            self._yf_fetcher = YFinanceFetcher()
            self.logger.debug("YFinanceFetcher created")
        return self._yf_fetcher

    def load_dollar_index(self) -> DataFrame | None:
        """FREDからドル指数データを取得する.

        HistoricalCacheを使用してDTWEXAFEGS（Nominal Advanced Foreign
        Economies U.S. Dollar Index）を取得する。

        Returns
        -------
        DataFrame | None
            ドル指数データ（DatetimeIndex、'value'列）
            キャッシュにデータがない場合はNone

        Examples
        --------
        >>> analyzer = DollarsIndexAndMetalsAnalyzer()
        >>> dollar_df = analyzer.load_dollar_index()
        >>> dollar_df.head()
                       value
        2024-01-01    110.5
        ...
        """
        self.logger.info(
            "Loading dollar index from FRED cache",
            series_id=self.DOLLAR_INDEX_SERIES,
        )

        cache = self._get_fred_cache()
        df = cache.get_series_df(self.DOLLAR_INDEX_SERIES)

        if df is not None:
            self.logger.debug(
                "Dollar index loaded",
                rows=len(df),
                date_range=(
                    str(df.index.min()) if not df.empty else None,
                    str(df.index.max()) if not df.empty else None,
                ),
            )
        else:
            self.logger.warning(
                "Dollar index not found in cache",
                series_id=self.DOLLAR_INDEX_SERIES,
            )

        return df

    def load_metal_prices(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> DataFrame:
        """yfinanceから金属ETF価格データを取得する.

        Parameters
        ----------
        start_date : str | None, optional
            データ取得開始日（デフォルト: None = 最も古いデータから）
            ISO 8601形式（YYYY-MM-DD）
        end_date : str | None, optional
            データ取得終了日（デフォルト: None = 今日まで）
            ISO 8601形式（YYYY-MM-DD）

        Returns
        -------
        DataFrame
            金属ETFの調整済み終値（ワイド形式）
            カラム: ティッカーシンボル
            インデックス: 日付

        Examples
        --------
        >>> analyzer = DollarsIndexAndMetalsAnalyzer()
        >>> metal_df = analyzer.load_metal_prices()
        >>> metal_df.head()
                        GLD    SLV   PPLT   CPER   PALL    DBB
        2024-01-01   180.5  22.3   95.2   25.1  140.5   20.3
        ...
        """
        self.logger.info(
            "Loading metal prices from yfinance",
            tickers=self.metal_tickers,
            start_date=start_date,
            end_date=end_date,
        )

        fetcher = self._get_yf_fetcher()
        options = FetchOptions(
            symbols=self.metal_tickers,
            start_date=start_date,
            end_date=end_date,
        )

        results = fetcher.fetch(options)

        # 結果をワイド形式に変換
        price_data: dict[str, pd.Series] = {}

        for result in results:
            if not result.is_empty and "adj_close" in result.data.columns:
                adj_close_data = result.data["adj_close"]
                # DataFrameの場合はSeriesに変換
                if isinstance(adj_close_data, pd.DataFrame):
                    adj_close_data = adj_close_data.iloc[:, 0]
                price_data[result.symbol] = adj_close_data
                self.logger.debug(
                    "Metal price loaded",
                    symbol=result.symbol,
                    rows=len(result.data),
                )
            elif not result.is_empty and "close" in result.data.columns:
                # adj_closeがない場合はcloseを使用
                close_data = result.data["close"]
                # DataFrameの場合はSeriesに変換
                if isinstance(close_data, pd.DataFrame):
                    close_data = close_data.iloc[:, 0]
                price_data[result.symbol] = close_data
                self.logger.debug(
                    "Metal price loaded (using close)",
                    symbol=result.symbol,
                    rows=len(result.data),
                )
            else:
                self.logger.warning(
                    "Empty data for metal ticker",
                    symbol=result.symbol,
                )

        if not price_data:
            self.logger.warning("No metal price data fetched")
            return pd.DataFrame()

        df = pd.DataFrame(price_data)

        self.logger.info(
            "Metal prices loaded",
            total_tickers=len(price_data),
            rows=len(df),
        )

        return df

    def load_price(self) -> DataFrame:
        """ドル指数と金属価格データを結合したDataFrameを返す.

        ドル指数（FRED）と金属ETF価格（yfinance）を結合し、
        ロング形式のDataFrameとして返す。

        Returns
        -------
        DataFrame
            結合されたデータ（ロング形式）
            カラム: Date, Ticker, value, variable

        Examples
        --------
        >>> analyzer = DollarsIndexAndMetalsAnalyzer()
        >>> price_df = analyzer.load_price()
        >>> price_df.head()
                 Date    Ticker    value variable
        0  2024-01-01       GLD   180.50    Price
        1  2024-01-01       SLV    22.30    Price
        ...
        """
        self.logger.info("Loading combined price data")

        # ドル指数を取得
        dollar_df = self.load_dollar_index()
        if dollar_df is None:
            self.logger.error("Dollar index not available")
            raise ValueError("Dollar index data not available")

        dollar_df = dollar_df.rename(columns={"value": self.DOLLAR_INDEX_SERIES})

        # 金属価格を取得
        metal_df = self.load_metal_prices()

        # マージ（左外部結合：ドル指数の日付を基準）
        merged_df = pd.merge(
            dollar_df,
            metal_df,
            left_index=True,
            right_index=True,
            how="left",
        )

        # 前方向補間
        merged_df = merged_df.ffill()

        # ロング形式に変換
        merged_df = merged_df.reset_index()
        merged_df = merged_df.rename(columns={"index": "Date"})

        price_df = pd.melt(
            merged_df,
            id_vars=["Date"],
            var_name="Ticker",
            value_name="value",
        ).assign(variable="Price")

        self.logger.info(
            "Combined price data loaded",
            rows=len(price_df),
            tickers=price_df["Ticker"].nunique(),
        )

        return price_df

    def calc_return(self, start_date: str = "2020-01-01") -> DataFrame:
        """指定された開始日からの累積リターンを計算する.

        Parameters
        ----------
        start_date : str, optional
            リターン計算の開始日（デフォルト: "2020-01-01"）
            ISO 8601形式（YYYY-MM-DD）

        Returns
        -------
        DataFrame
            累積リターン（ワイド形式）
            カラム: ティッカーシンボル + DTWEXAFEGS
            インデックス: 日付
            初日の値は1.0に正規化

        Examples
        --------
        >>> analyzer = DollarsIndexAndMetalsAnalyzer()
        >>> cum_return = analyzer.calc_return(start_date="2024-01-01")
        >>> cum_return.head()
                        GLD    SLV  DTWEXAFEGS
        2024-01-01    1.000  1.000       110.5
        2024-01-02    1.012  1.005       111.0
        ...
        """
        self.logger.info(
            "Calculating cumulative returns",
            start_date=start_date,
        )

        # ドル指数を取得
        dollar_df = self.load_dollar_index()
        if dollar_df is None:
            self.logger.error("Dollar index not available")
            raise ValueError("Dollar index data not available")

        # 金属価格を取得
        metal_df = self.load_metal_prices()

        # 開始日以降のデータに絞り込み
        metal_return = metal_df.loc[start_date:, :]

        if metal_return.empty:
            self.logger.warning(
                "No metal data after start_date",
                start_date=start_date,
            )
            return pd.DataFrame()

        # 初日で正規化（累積リターン）
        metal_return = metal_return.div(metal_return.iloc[0])

        # ドル指数と結合
        merged_df = pd.merge(
            metal_return,
            dollar_df,
            left_index=True,
            right_index=True,
            how="outer",
        )

        # 前方向補間
        merged_df = merged_df.ffill()

        # valueカラムをDTWEXAFEGSにリネーム
        merged_df = merged_df.rename(columns={"value": self.DOLLAR_INDEX_SERIES})

        self.logger.info(
            "Cumulative returns calculated",
            rows=len(merged_df),
            start_date=start_date,
        )

        return merged_df

    def get_summary(
        self,
        start_date: str = "2020-01-01",
    ) -> dict[str, Any]:
        """分析サマリーを取得する.

        ドル指数と金属価格の最新値、および累積リターンを
        まとめたサマリー情報を返す。

        Parameters
        ----------
        start_date : str, optional
            累積リターン計算の開始日（デフォルト: "2020-01-01"）

        Returns
        -------
        dict[str, Any]
            サマリー情報
            - generated_at: 生成日時（ISO 8601形式）
            - dollar_index_latest: ドル指数の最新値
            - metal_prices_latest: 金属ETFの最新価格（辞書形式）
            - cumulative_returns: 累積リターンDataFrame

        Examples
        --------
        >>> analyzer = DollarsIndexAndMetalsAnalyzer()
        >>> summary = analyzer.get_summary()
        >>> summary["dollar_index_latest"]
        112.5
        >>> summary["metal_prices_latest"]["GLD"]
        185.3
        """
        self.logger.info("Generating summary", start_date=start_date)

        # ドル指数の最新値
        dollar_df = self.load_dollar_index()
        dollar_latest: float | None = None
        if dollar_df is not None and not dollar_df.empty:
            dollar_latest = float(dollar_df["value"].iloc[-1])

        # 金属価格の最新値
        metal_df = self.load_metal_prices()
        metal_latest: dict[str, float | None] = {}
        for ticker in self.metal_tickers:
            if ticker in metal_df.columns and not metal_df[ticker].empty:
                metal_latest[ticker] = float(metal_df[ticker].dropna().iloc[-1])
            else:
                metal_latest[ticker] = None

        # 累積リターン
        cum_return = self.calc_return(start_date=start_date)

        summary: dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "dollar_index_latest": dollar_latest,
            "metal_prices_latest": metal_latest,
            "cumulative_returns": cum_return,
        }

        self.logger.info(
            "Summary generated",
            dollar_index_latest=dollar_latest,
            metal_count=len([v for v in metal_latest.values() if v is not None]),
        )

        return summary


__all__ = ["DollarsIndexAndMetalsAnalyzer"]
