"""Unit tests for DataProvider Protocol.

このテストファイルは、strategy パッケージの DataProvider Protocol の定義と動作を検証します。

テストTODO:
- [x] DataProvider Protocol が定義されている
- [x] get_prices() メソッドが定義されている
  - [x] tickers: list[str]
  - [x] start, end: str (YYYY-MM-DD形式)
  - [x] 戻り値: MultiIndex DataFrame
- [x] get_ticker_info() メソッドが定義されている
- [x] get_ticker_infos() メソッドが定義されている
- [x] NumPy 形式の docstring で戻り値の DataFrame 構造が明記されている
- [x] Duck typing で正しく動作する（モッククラスで確認）
"""

import inspect
from typing import Protocol

import pandas as pd

from strategy.providers.protocol import DataProvider
from strategy.types import TickerInfo


class TestDataProviderProtocol:
    """DataProvider Protocol の定義テスト。"""

    def test_正常系_DataProviderはProtocolである(self) -> None:
        """DataProvider が typing.Protocol を継承していることを確認。"""
        assert issubclass(DataProvider, Protocol)

    def test_正常系_DataProviderはruntime_checkableである(self) -> None:
        """DataProvider が runtime_checkable で isinstance チェック可能であることを確認。"""
        # runtime_checkable デコレータが適用されている場合、
        # _is_runtime_protocol 属性が True になる
        assert getattr(DataProvider, "_is_runtime_protocol", False) is True


class TestDataProviderMethodSignatures:
    """DataProvider の各メソッドシグネチャのテスト。"""

    def test_正常系_get_pricesメソッドが定義されている(self) -> None:
        """get_prices メソッドが Protocol に定義されていることを確認。"""
        assert hasattr(DataProvider, "get_prices")
        assert callable(getattr(DataProvider, "get_prices", None))

    def test_正常系_get_ticker_infoメソッドが定義されている(self) -> None:
        """get_ticker_info メソッドが Protocol に定義されていることを確認。"""
        assert hasattr(DataProvider, "get_ticker_info")
        assert callable(getattr(DataProvider, "get_ticker_info", None))

    def test_正常系_get_ticker_infosメソッドが定義されている(self) -> None:
        """get_ticker_infos メソッドが Protocol に定義されていることを確認。"""
        assert hasattr(DataProvider, "get_ticker_infos")
        assert callable(getattr(DataProvider, "get_ticker_infos", None))


class TestGetPricesMethodSignature:
    """get_prices メソッドのシグネチャテスト。"""

    def test_正常系_tickersパラメータが定義されている(self) -> None:
        """get_prices に tickers パラメータが定義されていることを確認。"""
        sig = inspect.signature(DataProvider.get_prices)
        params = sig.parameters

        assert "tickers" in params

    def test_正常系_startパラメータが定義されている(self) -> None:
        """get_prices に start パラメータが定義されていることを確認。"""
        sig = inspect.signature(DataProvider.get_prices)
        params = sig.parameters

        assert "start" in params

    def test_正常系_endパラメータが定義されている(self) -> None:
        """get_prices に end パラメータが定義されていることを確認。"""
        sig = inspect.signature(DataProvider.get_prices)
        params = sig.parameters

        assert "end" in params

    def test_正常系_戻り値はDataFrameである(self) -> None:
        """get_prices の戻り値型が pd.DataFrame であることを確認。"""
        sig = inspect.signature(DataProvider.get_prices)

        assert sig.return_annotation == pd.DataFrame


class TestGetTickerInfoMethodSignature:
    """get_ticker_info メソッドのシグネチャテスト。"""

    def test_正常系_tickerパラメータが定義されている(self) -> None:
        """get_ticker_info に ticker パラメータが定義されていることを確認。"""
        sig = inspect.signature(DataProvider.get_ticker_info)
        params = sig.parameters

        assert "ticker" in params

    def test_正常系_戻り値はTickerInfoである(self) -> None:
        """get_ticker_info の戻り値型が TickerInfo であることを確認。"""
        sig = inspect.signature(DataProvider.get_ticker_info)

        assert sig.return_annotation == TickerInfo


class TestGetTickerInfosMethodSignature:
    """get_ticker_infos メソッドのシグネチャテスト。"""

    def test_正常系_tickersパラメータが定義されている(self) -> None:
        """get_ticker_infos に tickers パラメータが定義されていることを確認。"""
        sig = inspect.signature(DataProvider.get_ticker_infos)
        params = sig.parameters

        assert "tickers" in params

    def test_正常系_戻り値は辞書型である(self) -> None:
        """get_ticker_infos の戻り値型が dict[str, TickerInfo] であることを確認。"""
        sig = inspect.signature(DataProvider.get_ticker_infos)

        # dict[str, TickerInfo] を確認
        return_annotation = sig.return_annotation
        # 型を文字列として確認（ジェネリック型のため）
        assert "dict" in str(return_annotation).lower()
        assert "TickerInfo" in str(return_annotation)


class MockDataProvider:
    """DataProvider Protocol を満たすモック実装。

    Duck typing により、Protocol を明示的に継承しなくても
    同じインターフェースを持てば DataProvider として扱える。
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
            取得するティッカーシンボルのリスト
        start : str
            開始日（YYYY-MM-DD形式）
        end : str
            終了日（YYYY-MM-DD形式）

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame（columns: ticker, rows: date）
            各ティッカーに対して open, high, low, close, volume を含む
        """
        dates = pd.date_range(start, periods=5, freq="D")
        columns = pd.MultiIndex.from_product(
            [tickers, ["open", "high", "low", "close", "volume"]],
            names=["ticker", "price_type"],
        )
        data = pd.DataFrame(
            index=dates,
            columns=columns,
            data=100.0,
        )
        data.index.name = "date"
        return data

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """ティッカーの情報（セクター、資産クラス等）を取得.

        Parameters
        ----------
        ticker : str
            ティッカーシンボル

        Returns
        -------
        TickerInfo
            ティッカーの詳細情報
        """
        return TickerInfo(
            ticker=ticker,
            name=f"{ticker} Inc.",
            sector="Technology",
            industry="Software",
            asset_class="equity",
        )

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """複数ティッカーの情報を一括取得.

        Parameters
        ----------
        tickers : list[str]
            ティッカーシンボルのリスト

        Returns
        -------
        dict[str, TickerInfo]
            ティッカーをキーとした情報の辞書
        """
        return {ticker: self.get_ticker_info(ticker) for ticker in tickers}


class TestMockDataProviderDuckTyping:
    """MockDataProvider が DataProvider Protocol を満たすことを確認するテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.start = "2024-01-01"
        self.end = "2024-12-31"

    def test_正常系_MockはDataProviderのインスタンスとして認識される(self) -> None:
        """MockDataProvider が isinstance チェックを通過することを確認。"""
        assert isinstance(self.provider, DataProvider)


class TestGetPrices:
    """get_prices メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.tickers = ["AAPL", "GOOGL"]

    def test_正常系_str型の日付で価格データを取得(self) -> None:
        """str 型の日付パラメータ（YYYY-MM-DD形式）で get_prices が動作することを確認。"""
        start = "2024-01-01"
        end = "2024-12-31"

        result = self.provider.get_prices(self.tickers, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "date"

    def test_正常系_戻り値がMultiIndexDataFrameである(self) -> None:
        """get_prices の戻り値が MultiIndex DataFrame であることを確認。"""
        result = self.provider.get_prices(
            self.tickers,
            "2024-01-01",
            "2024-12-31",
        )

        assert isinstance(result.columns, pd.MultiIndex)
        # columns の levels を確認
        assert "ticker" in result.columns.names
        assert "price_type" in result.columns.names

    def test_正常系_OHLCVカラムが含まれる(self) -> None:
        """get_prices の戻り値に OHLCV カラムが含まれることを確認。"""
        result = self.provider.get_prices(
            self.tickers,
            "2024-01-01",
            "2024-12-31",
        )

        # 各ティッカーに対して OHLCV カラムが存在することを確認
        price_types = result.columns.get_level_values("price_type").unique()
        expected_types = {"open", "high", "low", "close", "volume"}
        assert set(price_types) == expected_types

    def test_正常系_指定したティッカーが含まれる(self) -> None:
        """get_prices の戻り値に指定したティッカーが含まれることを確認。"""
        result = self.provider.get_prices(
            self.tickers,
            "2024-01-01",
            "2024-12-31",
        )

        tickers_in_result = result.columns.get_level_values("ticker").unique()
        assert set(tickers_in_result) == set(self.tickers)


class TestGetTickerInfo:
    """get_ticker_info メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()

    def test_正常系_TickerInfoを取得(self) -> None:
        """get_ticker_info が TickerInfo を返すことを確認。"""
        result = self.provider.get_ticker_info("AAPL")

        assert isinstance(result, TickerInfo)

    def test_正常系_tickerが正しく設定される(self) -> None:
        """返される TickerInfo の ticker が正しいことを確認。"""
        result = self.provider.get_ticker_info("AAPL")

        assert result.ticker == "AAPL"

    def test_正常系_nameが設定される(self) -> None:
        """返される TickerInfo の name が設定されていることを確認。"""
        result = self.provider.get_ticker_info("AAPL")

        assert result.name is not None
        assert len(result.name) > 0


class TestGetTickerInfos:
    """get_ticker_infos メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.tickers = ["AAPL", "GOOGL", "MSFT"]

    def test_正常系_辞書を取得(self) -> None:
        """get_ticker_infos が dict を返すことを確認。"""
        result = self.provider.get_ticker_infos(self.tickers)

        assert isinstance(result, dict)

    def test_正常系_全てのティッカーが含まれる(self) -> None:
        """返される辞書に全てのティッカーが含まれることを確認。"""
        result = self.provider.get_ticker_infos(self.tickers)

        assert set(result.keys()) == set(self.tickers)

    def test_正常系_各値がTickerInfoである(self) -> None:
        """返される辞書の各値が TickerInfo であることを確認。"""
        result = self.provider.get_ticker_infos(self.tickers)

        for ticker, info in result.items():
            assert isinstance(info, TickerInfo)
            assert info.ticker == ticker


class TestDocstringDocumentation:
    """DataProvider の docstring ドキュメントテスト。"""

    def test_正常系_get_pricesにdocstringがある(self) -> None:
        """get_prices メソッドに docstring があることを確認。"""
        docstring = DataProvider.get_prices.__doc__
        assert docstring is not None
        assert len(docstring) > 0

    def test_正常系_get_pricesのdocstringにReturnsセクションがある(self) -> None:
        """get_prices の docstring に Returns セクションがあることを確認。"""
        docstring = DataProvider.get_prices.__doc__
        assert docstring is not None
        assert "Returns" in docstring

    def test_正常系_get_pricesのdocstringにMultiIndexの説明がある(self) -> None:
        """get_prices の docstring に MultiIndex DataFrame の説明があることを確認。"""
        docstring = DataProvider.get_prices.__doc__
        assert docstring is not None
        assert "MultiIndex" in docstring

    def test_正常系_get_ticker_infoにdocstringがある(self) -> None:
        """get_ticker_info メソッドに docstring があることを確認。"""
        docstring = DataProvider.get_ticker_info.__doc__
        assert docstring is not None
        assert len(docstring) > 0

    def test_正常系_get_ticker_infosにdocstringがある(self) -> None:
        """get_ticker_infos メソッドに docstring があることを確認。"""
        docstring = DataProvider.get_ticker_infos.__doc__
        assert docstring is not None
        assert len(docstring) > 0


class TestDataProviderTypeAnnotations:
    """DataProvider の型アノテーションテスト。"""

    def test_正常系_get_pricesの型アノテーションが正しい(self) -> None:
        """get_prices メソッドの型アノテーションを確認。"""
        sig = inspect.signature(DataProvider.get_prices)
        params = sig.parameters

        # パラメータの存在確認
        assert "tickers" in params
        assert "start" in params
        assert "end" in params

        # 戻り値の型確認
        assert sig.return_annotation == pd.DataFrame

    def test_正常系_get_ticker_infoの型アノテーションが正しい(self) -> None:
        """get_ticker_info メソッドの型アノテーションを確認。"""
        sig = inspect.signature(DataProvider.get_ticker_info)
        params = sig.parameters

        assert "ticker" in params
        assert sig.return_annotation == TickerInfo

    def test_正常系_get_ticker_infosの型アノテーションが正しい(self) -> None:
        """get_ticker_infos メソッドの型アノテーションを確認。"""
        sig = inspect.signature(DataProvider.get_ticker_infos)
        params = sig.parameters

        assert "tickers" in params
        # 戻り値が辞書型であることを確認
        assert "dict" in str(sig.return_annotation).lower()
