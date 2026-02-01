"""Unit tests for DataProvider Protocol.

このテストファイルは、DataProvider Protocol の定義と動作を検証します。

テストTODO:
- [x] DataProvider が typing.Protocol で定義されている
- [x] 全メソッドが datetime | str の日付型をサポート
- [x] 戻り値の DataFrame スキーマがドキュメント化されている
- [x] Duck typing で正しく動作する（モッククラスで確認）
"""

from datetime import datetime
from typing import Protocol

import pandas as pd

from factor.providers.base import DataProvider


class TestDataProviderProtocol:
    """DataProvider Protocol の定義テスト。"""

    def test_正常系_DataProviderはProtocolである(self) -> None:
        """DataProvider が typing.Protocol を継承していることを確認。"""
        # Protocol クラスは Protocol を継承している
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
        # メソッドが callable であることを確認
        assert callable(getattr(DataProvider, "get_prices", None))

    def test_正常系_get_volumesメソッドが定義されている(self) -> None:
        """get_volumes メソッドが Protocol に定義されていることを確認。"""
        assert hasattr(DataProvider, "get_volumes")
        assert callable(getattr(DataProvider, "get_volumes", None))

    def test_正常系_get_fundamentalsメソッドが定義されている(self) -> None:
        """get_fundamentals メソッドが Protocol に定義されていることを確認。"""
        assert hasattr(DataProvider, "get_fundamentals")
        assert callable(getattr(DataProvider, "get_fundamentals", None))

    def test_正常系_get_market_capメソッドが定義されている(self) -> None:
        """get_market_cap メソッドが Protocol に定義されていることを確認。"""
        assert hasattr(DataProvider, "get_market_cap")
        assert callable(getattr(DataProvider, "get_market_cap", None))


class MockDataProvider:
    """DataProvider Protocol を満たすモック実装。

    Duck typing により、Protocol を明示的に継承しなくても
    同じインターフェースを持てば DataProvider として扱える。
    """

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """価格データ (OHLCV) を取得。

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame (index: Date, columns: (symbol, OHLCV))
        """
        # テスト用のダミーデータを返す
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        columns = pd.MultiIndex.from_product(
            [symbols, ["Open", "High", "Low", "Close", "Volume"]],
            names=["symbol", "price_type"],
        )
        data = pd.DataFrame(
            index=dates,
            columns=columns,
            data=100.0,  # ダミー値
        )
        data.index.name = "Date"
        return data

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """出来高データを取得。

        Returns
        -------
        pd.DataFrame
            index: Date, columns: symbols
        """
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            index=dates,
            columns=pd.Index(symbols),
            data=1000000,  # ダミー値
        )
        data.index.name = "Date"
        return data

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """財務データを取得。

        Parameters
        ----------
        metrics : list[str]
            取得する指標 (e.g., ["per", "pbr", "roe", "roa"])

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame (index: Date, columns: (symbol, metric))
        """
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        columns = pd.MultiIndex.from_product(
            [symbols, metrics],
            names=["symbol", "metric"],
        )
        data = pd.DataFrame(
            index=dates,
            columns=columns,
            data=10.0,  # ダミー値
        )
        data.index.name = "Date"
        return data

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """時価総額データを取得。

        Returns
        -------
        pd.DataFrame
            index: Date, columns: symbols
        """
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            index=dates,
            columns=pd.Index(symbols),
            data=1e12,  # ダミー値（1兆円）
        )
        data.index.name = "Date"
        return data


class TestMockDataProviderDuckTyping:
    """MockDataProvider が DataProvider Protocol を満たすことを確認するテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.symbols = ["AAPL", "GOOGL", "MSFT"]
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 12, 31)
        self.start_date_str = "2024-01-01"
        self.end_date_str = "2024-12-31"

    def test_正常系_MockはDataProviderのインスタンスとして認識される(self) -> None:
        """MockDataProvider が isinstance チェックを通過することを確認。"""
        # runtime_checkable が適用されている場合のみ有効
        assert isinstance(self.provider, DataProvider)


class TestGetPrices:
    """get_prices メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.symbols = ["AAPL", "GOOGL"]

    def test_正常系_datetime型の日付で価格データを取得(self) -> None:
        """datetime 型の日付パラメータで get_prices が動作することを確認。"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        result = self.provider.get_prices(self.symbols, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_str型の日付で価格データを取得(self) -> None:
        """str 型の日付パラメータで get_prices が動作することを確認。"""
        start = "2024-01-01"
        end = "2024-12-31"

        result = self.provider.get_prices(self.symbols, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_戻り値がMultiIndexDataFrameである(self) -> None:
        """get_prices の戻り値が MultiIndex DataFrame であることを確認。"""
        result = self.provider.get_prices(
            self.symbols,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

        assert isinstance(result.columns, pd.MultiIndex)
        # columns の levels を確認
        assert "symbol" in result.columns.names
        assert "price_type" in result.columns.names

    def test_正常系_OHLCVカラムが含まれる(self) -> None:
        """get_prices の戻り値に OHLCV カラムが含まれることを確認。"""
        result = self.provider.get_prices(
            self.symbols,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

        # 各シンボルに対して OHLCV カラムが存在することを確認
        price_types = result.columns.get_level_values("price_type").unique()
        expected_types = {"Open", "High", "Low", "Close", "Volume"}
        assert set(price_types) == expected_types


class TestGetVolumes:
    """get_volumes メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.symbols = ["AAPL", "GOOGL"]

    def test_正常系_datetime型の日付で出来高データを取得(self) -> None:
        """datetime 型の日付パラメータで get_volumes が動作することを確認。"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        result = self.provider.get_volumes(self.symbols, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_str型の日付で出来高データを取得(self) -> None:
        """str 型の日付パラメータで get_volumes が動作することを確認。"""
        start = "2024-01-01"
        end = "2024-12-31"

        result = self.provider.get_volumes(self.symbols, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_カラムがシンボル名である(self) -> None:
        """get_volumes の戻り値のカラムがシンボル名であることを確認。"""
        result = self.provider.get_volumes(
            self.symbols,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

        assert list(result.columns) == self.symbols


class TestGetFundamentals:
    """get_fundamentals メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.symbols = ["AAPL", "GOOGL"]
        self.metrics = ["per", "pbr", "roe", "roa"]

    def test_正常系_datetime型の日付で財務データを取得(self) -> None:
        """datetime 型の日付パラメータで get_fundamentals が動作することを確認。"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        result = self.provider.get_fundamentals(self.symbols, self.metrics, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_str型の日付で財務データを取得(self) -> None:
        """str 型の日付パラメータで get_fundamentals が動作することを確認。"""
        start = "2024-01-01"
        end = "2024-12-31"

        result = self.provider.get_fundamentals(self.symbols, self.metrics, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_戻り値がMultiIndexDataFrameである(self) -> None:
        """get_fundamentals の戻り値が MultiIndex DataFrame であることを確認。"""
        result = self.provider.get_fundamentals(
            self.symbols,
            self.metrics,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

        assert isinstance(result.columns, pd.MultiIndex)
        assert "symbol" in result.columns.names
        assert "metric" in result.columns.names

    def test_正常系_指定したメトリクスが含まれる(self) -> None:
        """get_fundamentals の戻り値に指定したメトリクスが含まれることを確認。"""
        result = self.provider.get_fundamentals(
            self.symbols,
            self.metrics,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

        metrics_in_result = result.columns.get_level_values("metric").unique()
        assert set(metrics_in_result) == set(self.metrics)


class TestGetMarketCap:
    """get_market_cap メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.symbols = ["AAPL", "GOOGL"]

    def test_正常系_datetime型の日付で時価総額データを取得(self) -> None:
        """datetime 型の日付パラメータで get_market_cap が動作することを確認。"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        result = self.provider.get_market_cap(self.symbols, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_str型の日付で時価総額データを取得(self) -> None:
        """str 型の日付パラメータで get_market_cap が動作することを確認。"""
        start = "2024-01-01"
        end = "2024-12-31"

        result = self.provider.get_market_cap(self.symbols, start, end)

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"

    def test_正常系_カラムがシンボル名である(self) -> None:
        """get_market_cap の戻り値のカラムがシンボル名であることを確認。"""
        result = self.provider.get_market_cap(
            self.symbols,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

        assert list(result.columns) == self.symbols


class TestDateTypeSupport:
    """日付型サポートのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MockDataProvider()
        self.symbols = ["AAPL"]

    def test_正常系_全メソッドがdatetime型をサポート(self) -> None:
        """全メソッドが datetime 型の日付をサポートすることを確認。"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        # 各メソッドが datetime 型で動作することを確認
        prices = self.provider.get_prices(self.symbols, start, end)
        assert isinstance(prices, pd.DataFrame)

        volumes = self.provider.get_volumes(self.symbols, start, end)
        assert isinstance(volumes, pd.DataFrame)

        fundamentals = self.provider.get_fundamentals(self.symbols, ["per"], start, end)
        assert isinstance(fundamentals, pd.DataFrame)

        market_cap = self.provider.get_market_cap(self.symbols, start, end)
        assert isinstance(market_cap, pd.DataFrame)

    def test_正常系_全メソッドがstr型をサポート(self) -> None:
        """全メソッドが str 型の日付をサポートすることを確認。"""
        start = "2024-01-01"
        end = "2024-12-31"

        # 各メソッドが str 型で動作することを確認
        prices = self.provider.get_prices(self.symbols, start, end)
        assert isinstance(prices, pd.DataFrame)

        volumes = self.provider.get_volumes(self.symbols, start, end)
        assert isinstance(volumes, pd.DataFrame)

        fundamentals = self.provider.get_fundamentals(self.symbols, ["per"], start, end)
        assert isinstance(fundamentals, pd.DataFrame)

        market_cap = self.provider.get_market_cap(self.symbols, start, end)
        assert isinstance(market_cap, pd.DataFrame)

    def test_正常系_混合型の日付もサポート(self) -> None:
        """datetime と str の混合でも動作することを確認。"""
        start = datetime(2024, 1, 1)
        end = "2024-12-31"

        # 混合型でも動作することを確認
        prices = self.provider.get_prices(self.symbols, start, end)
        assert isinstance(prices, pd.DataFrame)


class TestDataProviderTypeAnnotations:
    """DataProvider の型アノテーションテスト。"""

    def test_正常系_get_pricesの型アノテーションが正しい(self) -> None:
        """get_prices メソッドの型アノテーションを確認。"""
        import inspect

        sig = inspect.signature(DataProvider.get_prices)
        params = sig.parameters

        # パラメータの存在確認
        assert "symbols" in params
        assert "start_date" in params
        assert "end_date" in params

        # 戻り値の型確認
        assert sig.return_annotation == pd.DataFrame

    def test_正常系_get_volumesの型アノテーションが正しい(self) -> None:
        """get_volumes メソッドの型アノテーションを確認。"""
        import inspect

        sig = inspect.signature(DataProvider.get_volumes)
        params = sig.parameters

        assert "symbols" in params
        assert "start_date" in params
        assert "end_date" in params
        assert sig.return_annotation == pd.DataFrame

    def test_正常系_get_fundamentalsの型アノテーションが正しい(self) -> None:
        """get_fundamentals メソッドの型アノテーションを確認。"""
        import inspect

        sig = inspect.signature(DataProvider.get_fundamentals)
        params = sig.parameters

        assert "symbols" in params
        assert "metrics" in params
        assert "start_date" in params
        assert "end_date" in params
        assert sig.return_annotation == pd.DataFrame

    def test_正常系_get_market_capの型アノテーションが正しい(self) -> None:
        """get_market_cap メソッドの型アノテーションを確認。"""
        import inspect

        sig = inspect.signature(DataProvider.get_market_cap)
        params = sig.parameters

        assert "symbols" in params
        assert "start_date" in params
        assert "end_date" in params
        assert sig.return_annotation == pd.DataFrame
