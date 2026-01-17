"""Unit tests for Factor base class.

このテストモジュールは、Factor基底クラスとその関連型の振る舞いを検証します。

テスト対象:
- Factor: ファクター基底クラス（ABC）
- FactorMetadata: ファクターのメタデータを保持するdataclass
- FactorComputeOptions: ファクター計算オプションを保持するdataclass
"""

from abc import ABC
from dataclasses import FrozenInstanceError
from datetime import datetime

import pandas as pd
import pytest

from factor.core.base import Factor, FactorComputeOptions, FactorMetadata
from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.providers.base import DataProvider

# =============================================================================
# テスト用のモッククラス
# =============================================================================


class MockDataProvider:
    """DataProviderプロトコルを実装するモッククラス。"""

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック価格データを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        data = {symbol: range(len(dates)) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック出来高データを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        data = {symbol: [1000] * len(dates) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モックファンダメンタルデータを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        arrays = [[s for s in symbols for _ in metrics], metrics * len(symbols)]
        columns = pd.MultiIndex.from_arrays(arrays, names=["symbol", "metric"])
        df = pd.DataFrame(1.0, index=dates, columns=columns)
        df.index.name = "Date"
        return df

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック時価総額データを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        data = {symbol: [1e9] * len(dates) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df


class ConcreteFactor(Factor):
    """テスト用の具象Factorクラス。"""

    name = "test_factor"
    description = "テスト用ファクター"
    category = FactorCategory.MOMENTUM

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """テスト用のファクター計算を実装。"""
        prices = provider.get_prices(universe, start_date, end_date)
        return prices.pct_change()


class ConcreteFactorWithMetadata(Factor):
    """メタデータをカスタマイズした具象Factorクラス。"""

    name = "custom_factor"
    description = "カスタムファクター"
    category = FactorCategory.VALUE
    _required_data: list[str] = ["price", "fundamentals"]
    _frequency: str = "daily"
    _lookback_period: int | None = 20
    _higher_is_better: bool = False
    _default_parameters: dict[str, int | float] = {"window": 20}

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """テスト用のファクター計算を実装。"""
        prices = provider.get_prices(universe, start_date, end_date)
        return prices.pct_change()


# =============================================================================
# FactorMetadata のテスト
# =============================================================================


class TestFactorMetadata:
    """FactorMetadataのテスト。"""

    def test_正常系_必須フィールドのみで初期化(self) -> None:
        """必須フィールドのみでFactorMetadataが作成できることを確認。"""
        metadata = FactorMetadata(
            name="test_factor",
            description="テストファクター",
            category="price",
            required_data=["price"],
            frequency="daily",
        )

        assert metadata.name == "test_factor"
        assert metadata.description == "テストファクター"
        assert metadata.category == "price"
        assert metadata.required_data == ["price"]
        assert metadata.frequency == "daily"

    def test_正常系_全フィールドで初期化(self) -> None:
        """全フィールドを指定してFactorMetadataが作成できることを確認。"""
        metadata = FactorMetadata(
            name="momentum_factor",
            description="モメンタムファクター",
            category="price",
            required_data=["price", "volume"],
            frequency="daily",
            lookback_period=252,
            higher_is_better=True,
            default_parameters={"lookback": 252, "skip_recent": 21},
        )

        assert metadata.name == "momentum_factor"
        assert metadata.lookback_period == 252
        assert metadata.higher_is_better is True
        assert metadata.default_parameters == {"lookback": 252, "skip_recent": 21}

    def test_正常系_デフォルト値が適用される(self) -> None:
        """デフォルト値が正しく適用されることを確認。"""
        metadata = FactorMetadata(
            name="test",
            description="test",
            category="value",
            required_data=["price"],
            frequency="daily",
        )

        assert metadata.lookback_period is None
        assert metadata.higher_is_better is True
        assert metadata.default_parameters == {}

    def test_正常系_frozenでイミュータブル(self) -> None:
        """FactorMetadataがfrozenでイミュータブルであることを確認。"""
        metadata = FactorMetadata(
            name="test",
            description="test",
            category="quality",
            required_data=["price"],
            frequency="daily",
        )

        with pytest.raises(FrozenInstanceError):
            metadata.name = "changed"

    def test_正常系_category値の検証(self) -> None:
        """categoryフィールドが有効なLiteral値を受け付けることを確認。"""
        valid_categories = ["price", "value", "quality", "size", "macro", "alternative"]

        for category in valid_categories:
            metadata = FactorMetadata(
                name="test",
                description="test",
                category=category,  # type: ignore[arg-type]
                required_data=["price"],
                frequency="daily",
            )
            assert metadata.category == category

    def test_正常系_frequency値の検証(self) -> None:
        """frequencyフィールドが有効なLiteral値を受け付けることを確認。"""
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly"]

        for frequency in valid_frequencies:
            metadata = FactorMetadata(
                name="test",
                description="test",
                category="price",
                required_data=["price"],
                frequency=frequency,  # type: ignore[arg-type]
            )
            assert metadata.frequency == frequency


# =============================================================================
# FactorComputeOptions のテスト
# =============================================================================


class TestFactorComputeOptions:
    """FactorComputeOptionsのテスト。"""

    def test_正常系_デフォルト値で初期化(self) -> None:
        """デフォルト値でFactorComputeOptionsが作成できることを確認。"""
        options = FactorComputeOptions()

        assert options.handle_missing == "drop"
        assert options.min_periods == 20
        assert options.universe_filter is None

    def test_正常系_カスタム値で初期化(self) -> None:
        """カスタム値でFactorComputeOptionsが作成できることを確認。"""
        options = FactorComputeOptions(
            handle_missing="fill_zero",
            min_periods=10,
            universe_filter="market_cap > 1e9",
        )

        assert options.handle_missing == "fill_zero"
        assert options.min_periods == 10
        assert options.universe_filter == "market_cap > 1e9"

    def test_正常系_frozenでイミュータブル(self) -> None:
        """FactorComputeOptionsがfrozenでイミュータブルであることを確認。"""
        options = FactorComputeOptions()

        with pytest.raises(FrozenInstanceError):
            options.min_periods = 100

    def test_正常系_handle_missing値の検証(self) -> None:
        """handle_missingフィールドが有効なLiteral値を受け付けることを確認。"""
        valid_values = ["drop", "fill_zero", "fill_mean"]

        for value in valid_values:
            options = FactorComputeOptions(handle_missing=value)  # type: ignore[arg-type]
            assert options.handle_missing == value


# =============================================================================
# Factor 基底クラスのテスト
# =============================================================================


class TestFactorABC:
    """Factor ABCクラスの構造テスト。"""

    def test_正常系_ABCを継承している(self) -> None:
        """FactorがABCを継承していることを確認。"""
        assert issubclass(Factor, ABC)

    def test_正常系_computeが抽象メソッド(self) -> None:
        """compute()が抽象メソッドとして定義されていることを確認。"""
        assert hasattr(Factor, "compute")
        assert getattr(Factor.compute, "__isabstractmethod__", False) is True

    def test_異常系_computeを実装しないとインスタンス化できない(self) -> None:
        """compute()を実装しないクラスはインスタンス化できないことを確認。"""

        class IncompleteFactor(Factor):
            name = "incomplete"
            description = "不完全なファクター"
            category = FactorCategory.PRICE

        with pytest.raises(TypeError, match="abstract method"):
            IncompleteFactor()  # type: ignore[abstract]

    def test_正常系_具象クラスをインスタンス化できる(self) -> None:
        """compute()を実装した具象クラスはインスタンス化できることを確認。"""
        factor = ConcreteFactor()

        assert factor is not None
        assert isinstance(factor, Factor)


class TestFactorClassAttributes:
    """Factorクラス属性のテスト。"""

    def test_正常系_name属性がクラス属性として定義されている(self) -> None:
        """name属性がクラス属性として定義されていることを確認。"""
        assert hasattr(Factor, "name")
        assert hasattr(ConcreteFactor, "name")
        assert ConcreteFactor.name == "test_factor"

    def test_正常系_description属性がクラス属性として定義されている(self) -> None:
        """description属性がクラス属性として定義されていることを確認。"""
        assert hasattr(Factor, "description")
        assert hasattr(ConcreteFactor, "description")
        assert ConcreteFactor.description == "テスト用ファクター"

    def test_正常系_category属性がクラス属性として定義されている(self) -> None:
        """category属性がクラス属性として定義されていることを確認。"""
        assert hasattr(Factor, "category")
        assert hasattr(ConcreteFactor, "category")
        assert ConcreteFactor.category == FactorCategory.MOMENTUM

    def test_正常系_インスタンスからクラス属性にアクセスできる(self) -> None:
        """インスタンスからクラス属性にアクセスできることを確認。"""
        factor = ConcreteFactor()

        assert factor.name == "test_factor"
        assert factor.description == "テスト用ファクター"
        assert factor.category == FactorCategory.MOMENTUM


class TestFactorMetadataProperty:
    """Factor.metadataプロパティのテスト。"""

    def test_正常系_metadataプロパティが存在する(self) -> None:
        """metadataプロパティが存在することを確認。"""
        factor = ConcreteFactor()

        assert hasattr(factor, "metadata")

    def test_正常系_metadataがFactorMetadataを返す(self) -> None:
        """metadataプロパティがFactorMetadataインスタンスを返すことを確認。"""
        factor = ConcreteFactor()

        metadata = factor.metadata

        assert isinstance(metadata, FactorMetadata)

    def test_正常系_metadataにクラス属性が反映される(self) -> None:
        """metadataにクラス属性の値が正しく反映されることを確認。"""
        factor = ConcreteFactor()

        metadata = factor.metadata

        assert metadata.name == "test_factor"
        assert metadata.description == "テスト用ファクター"
        # category は文字列 "momentum" になる（FactorCategory.MOMENTUM.value）
        assert metadata.category in ["momentum", "price"]


class TestFactorCompute:
    """Factor.compute()メソッドのテスト。"""

    def test_正常系_computeがDataFrameを返す(self) -> None:
        """compute()がpd.DataFrameを返すことを確認。"""
        factor = ConcreteFactor()
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL", "GOOGL"],
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_戻り値のindexがDate(self) -> None:
        """compute()の戻り値のindexがDateであることを確認。"""
        factor = ConcreteFactor()
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL", "GOOGL"],
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_戻り値のcolumnsがsymbols(self) -> None:
        """compute()の戻り値のcolumnsがsymbolsであることを確認。"""
        factor = ConcreteFactor()
        provider = MockDataProvider()
        universe = ["AAPL", "GOOGL", "MSFT"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert list(result.columns) == universe

    def test_正常系_datetime型の日付を受け付ける(self) -> None:
        """compute()がdatetime型の日付を受け付けることを確認。"""
        factor = ConcreteFactor()
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_str型の日付を受け付ける(self) -> None:
        """compute()がstr型の日付を受け付けることを確認。"""
        factor = ConcreteFactor()
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert isinstance(result, pd.DataFrame)


class TestFactorValidateInputs:
    """Factor.validate_inputs()メソッドのテスト。"""

    def test_正常系_有効な入力で例外なし(self) -> None:
        """有効な入力値でvalidate_inputs()が例外をスローしないことを確認。"""
        factor = ConcreteFactor()

        # 例外がスローされないことを確認
        factor.validate_inputs(
            universe=["AAPL", "GOOGL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )

    def test_異常系_空のuniverseでValidationError(self) -> None:
        """空のuniverseでValidationErrorがスローされることを確認。"""
        factor = ConcreteFactor()

        with pytest.raises(ValidationError):
            factor.validate_inputs(
                universe=[],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            )

    def test_異常系_start_dateがend_dateより後でValidationError(self) -> None:
        """start_dateがend_dateより後の場合にValidationErrorがスローされることを確認。"""
        factor = ConcreteFactor()

        with pytest.raises(ValidationError):
            factor.validate_inputs(
                universe=["AAPL"],
                start_date=datetime(2024, 12, 31),
                end_date=datetime(2024, 1, 1),
            )

    def test_異常系_start_dateとend_dateが同一でValidationError(self) -> None:
        """start_dateとend_dateが同一の場合にValidationErrorがスローされることを確認。"""
        factor = ConcreteFactor()

        with pytest.raises(ValidationError):
            factor.validate_inputs(
                universe=["AAPL"],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 1),
            )


class TestFactorDocstring:
    """Factor docstringのテスト。"""

    def test_正常系_Factorクラスにdocstringがある(self) -> None:
        """Factorクラスにdocstringが存在することを確認。"""
        assert Factor.__doc__ is not None
        assert len(Factor.__doc__) > 0

    def test_正常系_computeメソッドにdocstringがある(self) -> None:
        """compute()メソッドにdocstringが存在することを確認。"""
        assert Factor.compute.__doc__ is not None
        assert len(Factor.compute.__doc__) > 0

    def test_正常系_validate_inputsメソッドにdocstringがある(self) -> None:
        """validate_inputs()メソッドにdocstringが存在することを確認。"""
        assert Factor.validate_inputs.__doc__ is not None
        assert len(Factor.validate_inputs.__doc__) > 0

    def test_正常系_metadataプロパティにdocstringがある(self) -> None:
        """metadataプロパティにdocstringが存在することを確認。"""
        # プロパティのdocstringはfget経由でアクセス
        assert Factor.metadata.fget is not None
        assert Factor.metadata.fget.__doc__ is not None


class TestDataProviderProtocol:
    """DataProviderプロトコル互換性のテスト。"""

    def test_正常系_MockDataProviderがDataProviderを満たす(self) -> None:
        """MockDataProviderがDataProviderプロトコルを満たすことを確認。"""
        provider = MockDataProvider()

        # runtime_checkableなプロトコルなのでisinstanceでチェック可能
        assert isinstance(provider, DataProvider)
