"""MarketAnalysisProvider implementation.

market パッケージを使用した DataProvider の実装。
YFinanceFetcher を使用して株価データを取得し、TickerInfo を提供する。
"""

from typing import Any

import pandas as pd
import yfinance as yf

from market.yfinance import DataFetchError, FetchOptions, YFinanceFetcher
from strategy.errors import DataProviderError
from strategy.types import TickerInfo
from utils_core.logging import get_logger

logger = get_logger(__name__, module="market_analysis_provider")


class MarketAnalysisProvider:
    """DataProvider implementation using market package.

    市場データの取得に market パッケージの YFinanceFetcher を使用する
    DataProvider の実装。

    Parameters
    ----------
    use_cache : bool, default=True
        キャッシュを使用するかどうか

    Examples
    --------
    >>> provider = MarketAnalysisProvider()
    >>> df = provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")
    >>> df.columns.names
    ['ticker', 'price_type']
    """

    def __init__(self, use_cache: bool = True) -> None:
        """Initialize MarketAnalysisProvider.

        Parameters
        ----------
        use_cache : bool, default=True
            キャッシュを使用するかどうか
        """
        logger.debug(
            "Initializing MarketAnalysisProvider",
            use_cache=use_cache,
        )
        self._use_cache = use_cache
        self._fetcher = YFinanceFetcher()
        logger.info(
            "MarketAnalysisProvider initialized",
            use_cache=use_cache,
        )

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """指定期間の価格データ（OHLCV）を取得.

        Parameters
        ----------
        tickers : list[str]
            取得するティッカーシンボルのリスト（例: ["AAPL", "GOOGL", "MSFT"]）
        start : str
            開始日（YYYY-MM-DD形式、例: "2024-01-01"）
        end : str
            終了日（YYYY-MM-DD形式、例: "2024-12-31"）

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame で以下の構造を持つ:

            - **index**: DatetimeIndex（date）
            - **columns**: MultiIndex with levels:
                - level 0 (ticker): ティッカーシンボル
                - level 1 (price_type): open, high, low, close, volume

        Raises
        ------
        DataProviderError
            データ取得に失敗した場合

        Examples
        --------
        >>> provider = MarketAnalysisProvider()
        >>> df = provider.get_prices(["AAPL", "GOOGL"], "2024-01-01", "2024-12-31")
        >>> df.columns.names
        ['ticker', 'price_type']
        """
        logger.debug(
            "Fetching prices",
            tickers=tickers,
            start=start,
            end=end,
        )

        try:
            options = FetchOptions(
                symbols=tickers,
                start_date=start,
                end_date=end,
                use_cache=self._use_cache,
            )

            results = self._fetcher.fetch(options)

            # Convert results to MultiIndex DataFrame
            df = self._convert_to_multiindex_dataframe(results)

            logger.info(
                "Prices fetched successfully",
                tickers=tickers,
                rows=len(df),
            )

            return df

        except DataFetchError as e:
            logger.error(
                "Failed to fetch prices",
                tickers=tickers,
                error=str(e),
            )
            raise DataProviderError(
                f"Failed to fetch prices for {tickers}: {e}",
                code="PROVIDER_FETCH_ERROR",
                cause=e,
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error fetching prices",
                tickers=tickers,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DataProviderError(
                f"Unexpected error fetching prices for {tickers}: {e}",
                code="PROVIDER_UNEXPECTED_ERROR",
                cause=e,
            ) from e

    def _convert_to_multiindex_dataframe(
        self,
        results: list[Any],
    ) -> pd.DataFrame:
        """Convert MarketDataResult list to MultiIndex DataFrame.

        Parameters
        ----------
        results : list[MarketDataResult]
            YFinanceFetcher.fetch() の結果

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame with (ticker, price_type) columns
        """
        if not results:
            # Return empty DataFrame with correct structure
            columns = pd.MultiIndex.from_tuples(
                [],
                names=["ticker", "price_type"],
            )
            return pd.DataFrame(columns=columns)

        dfs: dict[str, pd.DataFrame] = {}

        for result in results:
            symbol = result.symbol
            data = result.data

            if data.empty:
                continue

            # Ensure column names are lowercase
            data.columns = pd.Index([col.lower() for col in data.columns])

            # Select only OHLCV columns
            ohlcv_cols = ["open", "high", "low", "close", "volume"]
            available_cols = [col for col in ohlcv_cols if col in data.columns]

            if available_cols:
                dfs[symbol] = data[available_cols]

        if not dfs:
            # Return empty DataFrame with correct structure
            columns = pd.MultiIndex.from_tuples(
                [],
                names=["ticker", "price_type"],
            )
            return pd.DataFrame(columns=columns)

        # Concatenate all DataFrames with MultiIndex columns
        combined = pd.concat(
            dfs,
            axis=1,
            keys=dfs.keys(),
            names=["ticker", "price_type"],
        )

        # Ensure index is named 'date'
        combined.index.name = "date"

        return combined

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """ティッカーの情報（セクター、資産クラス等）を取得.

        Parameters
        ----------
        ticker : str
            ティッカーシンボル（例: "AAPL"）

        Returns
        -------
        TickerInfo
            ティッカーの詳細情報を含むデータクラス。

        Raises
        ------
        DataProviderError
            銘柄情報取得に失敗した場合

        Examples
        --------
        >>> provider = MarketAnalysisProvider()
        >>> info = provider.get_ticker_info("AAPL")
        >>> info.ticker
        'AAPL'
        """
        logger.debug("Fetching ticker info", ticker=ticker)

        try:
            yf_ticker = yf.Ticker(ticker)
            info: dict[str, Any] = yf_ticker.info

            name = info.get("shortName") or info.get("longName") or ticker
            sector = info.get("sector")
            industry = info.get("industry")

            ticker_info = TickerInfo(
                ticker=ticker,
                name=str(name),
                sector=str(sector) if sector else None,
                industry=str(industry) if industry else None,
                asset_class="equity",
            )

            logger.debug(
                "Ticker info fetched",
                ticker=ticker,
                name=ticker_info.name,
                sector=ticker_info.sector,
            )

            return ticker_info

        except Exception as e:
            logger.error(
                "Failed to fetch ticker info",
                ticker=ticker,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DataProviderError(
                f"Failed to fetch ticker info for {ticker}: {e}",
                code="PROVIDER_TICKER_INFO_ERROR",
                cause=e,
            ) from e

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """複数ティッカーの情報を一括取得.

        Parameters
        ----------
        tickers : list[str]
            ティッカーシンボルのリスト（例: ["AAPL", "GOOGL", "MSFT"]）

        Returns
        -------
        dict[str, TickerInfo]
            ティッカーシンボルをキー、TickerInfo を値とする辞書。

        Examples
        --------
        >>> provider = MarketAnalysisProvider()
        >>> infos = provider.get_ticker_infos(["AAPL", "GOOGL"])
        >>> infos["AAPL"].name
        'Apple Inc.'
        """
        logger.debug("Fetching ticker infos", tickers=tickers)

        result: dict[str, TickerInfo] = {}

        for ticker in tickers:
            try:
                result[ticker] = self.get_ticker_info(ticker)
            except DataProviderError:
                # Re-raise to preserve the error
                raise
            except Exception as e:
                raise DataProviderError(
                    f"Failed to fetch ticker info for {ticker}: {e}",
                    code="PROVIDER_TICKER_INFO_ERROR",
                    cause=e,
                ) from e

        logger.info(
            "Ticker infos fetched",
            tickers=tickers,
            count=len(result),
        )

        return result


__all__ = ["MarketAnalysisProvider"]
