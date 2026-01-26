"""DataProvider Protocol definition.

データ取得の抽象インターフェースを定義する。
market パッケージ、テスト用モック、将来の商用プロバイダーを統一的に扱うための Protocol。
"""

from typing import Protocol, runtime_checkable

import pandas as pd

from strategy.types import TickerInfo


@runtime_checkable
class DataProvider(Protocol):
    """データプロバイダーの抽象インターフェース.

    market パッケージ、テスト用モック、将来の商用プロバイダーなど、
    異なるデータソースを統一的に扱うためのプロトコル。

    Notes
    -----
    このプロトコルは runtime_checkable であり、isinstance() によるチェックが可能。
    Duck typing により、このプロトコルを明示的に継承しなくても、
    同じシグネチャのメソッドを持つクラスは DataProvider として扱える。

    Examples
    --------
    >>> class MockProvider:
    ...     def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
    ...         return pd.DataFrame()
    ...     def get_ticker_info(self, ticker: str) -> TickerInfo:
    ...         return TickerInfo(ticker=ticker, name=f"{ticker} Inc.")
    ...     def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
    ...         return {t: self.get_ticker_info(t) for t in tickers}
    >>> provider = MockProvider()
    >>> isinstance(provider, DataProvider)
    True
    """

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

            例:
            ```
                            AAPL                    GOOGL
                        open  high  low  close  vol  open  high ...
            2024-01-01  150.0 152.0 149.0 151.0 1M   140.0 142.0 ...
            2024-01-02  151.0 153.0 150.0 152.0 1.2M 141.0 143.0 ...
            ```

        Notes
        -----
        - 日付は文字列（YYYY-MM-DD形式）で指定する
        - 戻り値の DataFrame は日付でソートされている
        - 欠損日（休日等）はスキップされる場合がある

        Examples
        --------
        >>> provider = get_provider()
        >>> df = provider.get_prices(["AAPL", "GOOGL"], "2024-01-01", "2024-12-31")
        >>> df.columns.names
        ['ticker', 'price_type']
        >>> df.index.name
        'date'
        """
        ...

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
            - ticker: ティッカーシンボル
            - name: 銘柄名
            - sector: セクター（オプション）
            - industry: 業種（オプション）
            - asset_class: 資産クラス（"equity", "bond" など）

        Examples
        --------
        >>> provider = get_provider()
        >>> info = provider.get_ticker_info("AAPL")
        >>> info.ticker
        'AAPL'
        >>> info.name
        'Apple Inc.'
        """
        ...

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
            入力したすべてのティッカーが辞書のキーとして含まれる。

        Examples
        --------
        >>> provider = get_provider()
        >>> infos = provider.get_ticker_infos(["AAPL", "GOOGL"])
        >>> infos["AAPL"].name
        'Apple Inc.'
        >>> infos["GOOGL"].name
        'Alphabet Inc.'
        """
        ...
