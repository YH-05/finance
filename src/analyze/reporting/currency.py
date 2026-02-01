"""currency.py

円クロス為替レートを分析する CurrencyAnalyzer クラス。

yfinance を使用して為替データを取得し、複数期間の騰落率を計算する。

対象通貨ペア:
- USDJPY=X: 米ドル/円
- EURJPY=X: ユーロ/円
- GBPJPY=X: 英ポンド/円
- AUDJPY=X: 豪ドル/円
- CADJPY=X: カナダドル/円
- CHFJPY=X: スイスフラン/円
"""

from datetime import datetime, timedelta

import pandas as pd
from market.yfinance import FetchOptions, YFinanceFetcher
from pandas import DataFrame
from utils_core.logging import get_logger

from analyze.config import get_symbols


class CurrencyAnalyzer:
    """円クロス為替レートを分析するクラス.

    symbols.yaml の currencies.jpy_crosses で定義された通貨ペアに対して、
    yfinance を使用して為替データを取得し、複数期間の騰落率を計算する。

    Attributes
    ----------
    target_pairs : list[str]
        分析対象の通貨ペア一覧

    Examples
    --------
    >>> analyzer = CurrencyAnalyzer()
    >>> data = analyzer.fetch_data()
    >>> returns = analyzer.calculate_returns(data, periods=["1D", "1W", "1M"])
    >>> summary = analyzer.get_summary()
    """

    # デフォルトの対象通貨ペア（symbols.yaml からも取得可能）
    DEFAULT_PAIRS: list[str] = [
        "USDJPY=X",
        "EURJPY=X",
        "GBPJPY=X",
        "AUDJPY=X",
        "CADJPY=X",
        "CHFJPY=X",
    ]

    # 期間の定義（営業日数）
    PERIOD_DAYS: dict[str, int] = {
        "1D": 1,
        "1W": 5,  # 1週間 = 5営業日
        "1M": 21,  # 1ヶ月 = 約21営業日
    }

    def __init__(self) -> None:
        """CurrencyAnalyzer を初期化する."""
        self.logger = get_logger(__name__, component="CurrencyAnalyzer")
        self._fetcher: YFinanceFetcher | None = None
        self.logger.debug("CurrencyAnalyzer initialized")

    @property
    def target_pairs(self) -> list[str]:
        """分析対象の通貨ペアを返す.

        Returns
        -------
        list[str]
            通貨ペアのシンボルリスト
        """
        return self.DEFAULT_PAIRS.copy()

    def get_currency_pairs(self) -> list[str]:
        """symbols.yaml から通貨ペアを取得する.

        Returns
        -------
        list[str]
            通貨ペアのシンボルリスト
        """
        pairs = get_symbols("currencies", "jpy_crosses")
        if not pairs:
            self.logger.warning(
                "No currency pairs found in symbols.yaml, using defaults"
            )
            return self.DEFAULT_PAIRS.copy()
        return pairs

    def _get_fetcher(self) -> YFinanceFetcher:
        """YFinanceFetcher インスタンスを取得する.

        Returns
        -------
        YFinanceFetcher
            yfinance データ取得クライアント
        """
        if self._fetcher is None:
            self._fetcher = YFinanceFetcher()
            self.logger.debug("YFinanceFetcher created")
        return self._fetcher

    def fetch_data(
        self,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> dict[str, DataFrame]:
        """対象通貨ペアのデータを yfinance から取得する.

        Parameters
        ----------
        start_date : datetime | str | None, optional
            データ取得開始日（デフォルト: 1年前）
        end_date : datetime | str | None, optional
            データ取得終了日（デフォルト: 今日）

        Returns
        -------
        dict[str, DataFrame]
            通貨ペアシンボルをキー、DataFrame を値とする辞書
            各 DataFrame は OHLCV 列を持ち、インデックスは日付

        Examples
        --------
        >>> analyzer = CurrencyAnalyzer()
        >>> data = analyzer.fetch_data()
        >>> data["USDJPY=X"].head()
                        open    high     low   close  volume
        2026-01-27  155.50  156.00  155.00  155.75       0
        ...
        """
        # デフォルト日付を設定
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        pairs = self.get_currency_pairs()

        self.logger.info(
            "Fetching currency data",
            pairs=pairs,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        fetcher = self._get_fetcher()
        options = FetchOptions(
            symbols=pairs,
            start_date=start_date,
            end_date=end_date,
        )

        results = fetcher.fetch(options)

        data: dict[str, DataFrame] = {}
        for result in results:
            if not result.is_empty:
                data[result.symbol] = result.data
                self.logger.debug(
                    "Currency pair fetched",
                    symbol=result.symbol,
                    rows=len(result.data),
                )
            else:
                self.logger.warning(
                    "Empty data for currency pair",
                    symbol=result.symbol,
                )

        self.logger.info(
            "Data fetch completed",
            total_pairs=len(pairs),
            fetched_pairs=len(data),
        )

        return data

    def calculate_returns(
        self,
        data: dict[str, DataFrame],
        periods: list[str] | None = None,
    ) -> dict[str, dict[str, float | None]]:
        """期間別の騰落率（パーセント）を計算する.

        Parameters
        ----------
        data : dict[str, DataFrame]
            fetch_data() で取得したデータ
        periods : list[str] | None, optional
            計算する期間のリスト（デフォルト: ["1D", "1W", "1M"]）

        Returns
        -------
        dict[str, dict[str, float | None]]
            通貨ペアシンボルをキー、期間別騰落率を値とする辞書
            データ不足の場合は None

        Examples
        --------
        >>> analyzer = CurrencyAnalyzer()
        >>> data = analyzer.fetch_data()
        >>> returns = analyzer.calculate_returns(data, periods=["1D", "1W"])
        >>> returns["USDJPY=X"]["1D"]
        0.16  # 前日比+0.16%
        """
        if periods is None:
            periods = ["1D", "1W", "1M"]

        self.logger.info(
            "Calculating returns",
            pairs_count=len(data),
            periods=periods,
        )

        result: dict[str, dict[str, float | None]] = {}

        for symbol, df in data.items():
            result[symbol] = {}

            if df.empty or "close" not in df.columns:
                for period in periods:
                    result[symbol][period] = None
                continue

            # NaN を除去してソート
            clean_df = df.dropna(subset=["close"]).sort_index()

            if clean_df.empty:
                for period in periods:
                    result[symbol][period] = None
                continue

            latest_value = float(clean_df["close"].iloc[-1])

            for period in periods:
                days = self.PERIOD_DAYS.get(period)
                if days is None:
                    self.logger.warning(
                        "Unknown period",
                        period=period,
                    )
                    result[symbol][period] = None
                    continue

                if len(clean_df) <= days:
                    self.logger.debug(
                        "Insufficient data for period",
                        symbol=symbol,
                        period=period,
                        required_days=days,
                        available_days=len(clean_df),
                    )
                    result[symbol][period] = None
                    continue

                # 指定日数前の値を取得
                past_value = float(clean_df["close"].iloc[-(days + 1)])
                if past_value == 0:
                    result[symbol][period] = None
                    continue

                # 騰落率を計算（パーセント）
                return_pct = ((latest_value - past_value) / past_value) * 100
                result[symbol][period] = round(return_pct, 3)

                self.logger.debug(
                    "Return calculated",
                    symbol=symbol,
                    period=period,
                    latest=latest_value,
                    past=past_value,
                    return_pct=result[symbol][period],
                )

        return result

    def get_summary(
        self,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> dict[str, object]:
        """為替データのサマリーを取得する.

        データ取得と騰落率計算を一括で実行し、結果をまとめたサマリーを返す。

        Parameters
        ----------
        start_date : datetime | str | None, optional
            データ取得開始日
        end_date : datetime | str | None, optional
            データ取得終了日

        Returns
        -------
        dict[str, object]
            サマリー情報
            - generated_at: 生成日時
            - latest_rates: 各通貨ペアの最新レート
            - returns: 期間別騰落率

        Examples
        --------
        >>> analyzer = CurrencyAnalyzer()
        >>> summary = analyzer.get_summary()
        >>> summary["latest_rates"]["USDJPY=X"]
        155.75
        >>> summary["returns"]["USDJPY=X"]["1D"]
        0.16
        """
        self.logger.info("Generating currency summary")

        # データ取得
        data = self.fetch_data(start_date=start_date, end_date=end_date)

        # 最新レートを抽出
        latest_rates: dict[str, float | None] = {}
        for symbol in self.target_pairs:
            if symbol in data and not data[symbol].empty:
                df = data[symbol].dropna(subset=["close"])
                if not df.empty:
                    latest_rates[symbol] = float(df["close"].iloc[-1])
                else:
                    latest_rates[symbol] = None
            else:
                latest_rates[symbol] = None

        # 騰落率計算
        returns = self.calculate_returns(data, periods=["1D", "1W", "1M"])

        summary = {
            "generated_at": datetime.now().isoformat(),
            "latest_rates": latest_rates,
            "returns": returns,
        }

        self.logger.info(
            "Summary generated",
            pairs_count=len(latest_rates),
        )

        return summary


__all__ = ["CurrencyAnalyzer"]
