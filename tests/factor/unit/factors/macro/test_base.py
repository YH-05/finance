"""Unit tests for BaseMacroFactor abstract base class.

BaseMacroFactor is an abstract base class that defines the interface for all
macro factor implementations (interest rate, flight-to-quality, inflation, etc.).
"""

from abc import ABC

import pandas as pd
import pytest

# AIDEV-NOTE: These imports will fail until the implementation is created.
# This is intentional - tests are in Red state (TDD).
from factor.factors.macro.base import BaseMacroFactor


class TestBaseMacroFactorInterface:
    """Tests for BaseMacroFactor interface contract."""

    def test_正常系_BaseMacroFactorは抽象クラスである(self) -> None:
        """BaseMacroFactorが抽象クラスであることを確認。"""
        # BaseMacroFactor should be an abstract base class
        assert issubclass(BaseMacroFactor, ABC)

    def test_正常系_抽象クラスは直接インスタンス化できない(self) -> None:
        """BaseMacroFactorを直接インスタンス化できないことを確認。"""
        # BaseMacroFactor should not be instantiable directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseMacroFactor()  # type: ignore

    def test_正常系_nameプロパティが定義されている(self) -> None:
        """nameプロパティが抽象メソッドとして定義されていることを確認。"""
        # name should be defined as an abstract property
        assert hasattr(BaseMacroFactor, "name")

    def test_正常系_required_seriesプロパティが定義されている(self) -> None:
        """required_seriesプロパティが抽象メソッドとして定義されていることを確認。"""
        # required_series should be defined as an abstract property
        assert hasattr(BaseMacroFactor, "required_series")

    def test_正常系_calculateメソッドが定義されている(self) -> None:
        """calculateメソッドが抽象メソッドとして定義されていることを確認。"""
        # calculate should be defined as an abstract method
        assert hasattr(BaseMacroFactor, "calculate")


class ConcreteMacroFactor(BaseMacroFactor):
    """Concrete implementation of BaseMacroFactor for testing."""

    @property
    def name(self) -> str:
        """Return factor name."""
        return "TestFactor"

    @property
    def required_series(self) -> list[str]:
        """Return required FRED series IDs."""
        return ["TEST_SERIES_1", "TEST_SERIES_2"]

    def calculate(
        self,
        data: pd.DataFrame,
        **kwargs: pd.Series | pd.DataFrame | None,
    ) -> pd.DataFrame:
        """Calculate factor from input data."""
        # kwargs ignored in this test implementation
        _ = kwargs
        return data.copy()


class TestConcreteMacroFactorImplementation:
    """Tests for concrete implementation of BaseMacroFactor."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = ConcreteMacroFactor()

    def test_正常系_nameプロパティが文字列を返す(self) -> None:
        """nameプロパティがstr型を返すことを確認。"""
        assert isinstance(self.factor.name, str)
        assert self.factor.name == "TestFactor"

    def test_正常系_required_seriesプロパティがリストを返す(self) -> None:
        """required_seriesプロパティがlist[str]を返すことを確認。"""
        result = self.factor.required_series
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)
        assert result == ["TEST_SERIES_1", "TEST_SERIES_2"]

    def test_正常系_calculateメソッドがDataFrameを返す(self) -> None:
        """calculateメソッドがpd.DataFrameを返すことを確認。"""
        input_data = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        result = self.factor.calculate(input_data)
        assert isinstance(result, pd.DataFrame)

    def test_正常系_空のDataFrameも処理できる(self) -> None:
        """空のDataFrameを入力した場合も処理できることを確認。"""
        empty_data = pd.DataFrame()
        result = self.factor.calculate(empty_data)
        assert isinstance(result, pd.DataFrame)


class TestBaseMacroFactorRequiredSeriesContract:
    """Tests for required_series property contract."""

    def test_正常系_required_seriesはFRED系列IDのリストを想定(self) -> None:
        """required_seriesがFREDの系列IDリストであることを確認。"""
        factor = ConcreteMacroFactor()
        series_ids = factor.required_series

        # FRED series IDs are typically uppercase alphanumeric
        for series_id in series_ids:
            assert isinstance(series_id, str)
            assert len(series_id) > 0

    def test_正常系_required_seriesは重複を含まない(self) -> None:
        """required_seriesが重複を含まないことを確認。"""
        factor = ConcreteMacroFactor()
        series_ids = factor.required_series
        assert len(series_ids) == len(set(series_ids))


class TestBaseMacroFactorCalculateContract:
    """Tests for calculate method contract."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = ConcreteMacroFactor()

    def test_正常系_calculateは日時インデックスを保持する(self) -> None:
        """calculateメソッドが日時インデックスを保持することを確認。"""
        dates = pd.date_range("2020-01-01", periods=10, freq="B")
        input_data = pd.DataFrame(
            {"col1": range(10), "col2": range(10, 20)},
            index=dates,
        )
        result = self.factor.calculate(input_data)

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_calculateはNaN処理を行う(self) -> None:
        """calculateメソッドがNaN値を適切に処理することを確認。"""
        import numpy as np

        dates = pd.date_range("2020-01-01", periods=5, freq="B")
        input_data = pd.DataFrame(
            {"col1": [1.0, np.nan, 3.0, np.nan, 5.0]},
            index=dates,
        )
        result = self.factor.calculate(input_data)

        # The basic concrete implementation just copies, so NaN should be preserved
        assert result.isna().any().any()
