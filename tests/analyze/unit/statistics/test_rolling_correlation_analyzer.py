"""Unit tests for RollingCorrelationAnalyzer class.

This module tests the RollingCorrelationAnalyzer which inherits from
StatisticalAnalyzer and provides rolling correlation calculations
between a target column and other columns in the DataFrame.

Test patterns follow t-wada TDD approach.
"""

import math
from typing import Any

import numpy as np
import pandas as pd
import pytest

from analyze.statistics.base import StatisticalAnalyzer
from analyze.statistics.correlation import RollingCorrelationAnalyzer


class TestRollingCorrelationAnalyzerInheritance:
    """Test class inheritance and interface compliance."""

    def test_正常系_StatisticalAnalyzerを継承している(self) -> None:
        """RollingCorrelationAnalyzerがStatisticalAnalyzerを継承していることを確認。"""
        assert issubclass(RollingCorrelationAnalyzer, StatisticalAnalyzer)

    def test_正常系_インスタンス生成(self) -> None:
        """RollingCorrelationAnalyzerインスタンスが正しく生成されることを確認。"""
        analyzer = RollingCorrelationAnalyzer()
        assert analyzer is not None
        assert isinstance(analyzer, StatisticalAnalyzer)


class TestRollingCorrelationAnalyzerInit:
    """Test __init__ method."""

    def test_正常系_デフォルトパラメータ(self) -> None:
        """デフォルトパラメータで初期化されることを確認。"""
        analyzer = RollingCorrelationAnalyzer()
        assert analyzer.window == 252
        assert analyzer.min_periods == 30

    def test_正常系_カスタムパラメータ(self) -> None:
        """カスタムパラメータで初期化されることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=60, min_periods=10)
        assert analyzer.window == 60
        assert analyzer.min_periods == 10

    def test_正常系_windowのみ指定(self) -> None:
        """windowのみ指定時にmin_periodsがデフォルトのままであることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=100)
        assert analyzer.window == 100
        assert analyzer.min_periods == 30

    def test_正常系_min_periodsのみ指定(self) -> None:
        """min_periodsのみ指定時にwindowがデフォルトのままであることを確認。"""
        analyzer = RollingCorrelationAnalyzer(min_periods=20)
        assert analyzer.window == 252
        assert analyzer.min_periods == 20


class TestRollingCorrelationAnalyzerValidateInput:
    """Test validate_input method."""

    def test_正常系_有効なDataFrameでTrue(self) -> None:
        """有効なDataFrameでTrueが返されることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [100.0, 101.0, 102.0, 103.0, 104.0],
                "SPY": [400.0, 401.0, 402.0, 403.0, 404.0],
            }
        )
        assert analyzer.validate_input(df) is True

    def test_異常系_空のDataFrameでFalse(self) -> None:
        """空のDataFrameでFalseが返されることを確認。"""
        analyzer = RollingCorrelationAnalyzer()
        df = pd.DataFrame()
        assert analyzer.validate_input(df) is False

    def test_異常系_1列のDataFrameでFalse(self) -> None:
        """1列のDataFrameでFalseが返されることを確認。"""
        analyzer = RollingCorrelationAnalyzer()
        df = pd.DataFrame({"AAPL": [100.0, 101.0, 102.0]})
        assert analyzer.validate_input(df) is False

    def test_異常系_数値列がないDataFrameでFalse(self) -> None:
        """数値列がないDataFrameでFalseが返されることを確認。"""
        analyzer = RollingCorrelationAnalyzer()
        df = pd.DataFrame({"name": ["A", "B", "C"], "category": ["X", "Y", "Z"]})
        assert analyzer.validate_input(df) is False

    def test_正常系_数値列と非数値列が混在でTrue(self) -> None:
        """数値列が2つ以上あれば非数値列が混在してもTrueが返されることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [100.0, 101.0, 102.0, 103.0, 104.0],
                "SPY": [400.0, 401.0, 402.0, 403.0, 404.0],
                "name": ["A", "B", "C", "D", "E"],
            }
        )
        assert analyzer.validate_input(df) is True

    def test_異常系_行数がmin_periods未満でFalse(self) -> None:
        """行数がmin_periods未満の場合Falseが返されることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=10, min_periods=5)
        df = pd.DataFrame(
            {
                "AAPL": [100.0, 101.0, 102.0],
                "SPY": [400.0, 401.0, 402.0],
            }
        )
        assert analyzer.validate_input(df) is False


class TestRollingCorrelationAnalyzerCalculate:
    """Test calculate method."""

    def test_正常系_ローリング相関が計算される(self) -> None:
        """ローリング相関が正しく計算されることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "SPY": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 結果がDataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
        # target_column以外の列が存在することを確認
        assert "AAPL" in result.columns
        # target_column自体は結果に含まれない
        assert "SPY" not in result.columns

    def test_正常系_完全相関でローリング値が1(self) -> None:
        """完全正相関のデータでローリング相関が1.0になることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "SPY": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # min_periods以降の値は1.0に近い
        valid_values = result["AAPL"].dropna()
        for val in valid_values:
            assert val == pytest.approx(1.0)

    def test_正常系_先頭のNaN数(self) -> None:
        """先頭のNaN数がmin_periods-1であることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "SPY": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 先頭2つ（min_periods-1）がNaN
        assert pd.isna(result["AAPL"].iloc[0])
        assert pd.isna(result["AAPL"].iloc[1])
        # 3番目以降は有効
        assert pd.notna(result["AAPL"].iloc[2])

    def test_正常系_複数列の相関計算(self) -> None:
        """複数列の相関が同時に計算されることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "MSFT": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
                "SPY": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 両方の列が結果に含まれる
        assert "AAPL" in result.columns
        assert "MSFT" in result.columns
        assert "SPY" not in result.columns

        # AAPL は正相関、MSFT は負相関
        valid_aapl = result["AAPL"].dropna()
        valid_msft = result["MSFT"].dropna()

        for val in valid_aapl:
            assert val == pytest.approx(1.0)
        for val in valid_msft:
            assert val == pytest.approx(-1.0)

    def test_異常系_target_columnが存在しないとValueError(self) -> None:
        """target_columnが存在しない場合ValueErrorが発生することを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [1.0, 2.0, 3.0, 4.0, 5.0],
                "MSFT": [2.0, 4.0, 6.0, 8.0, 10.0],
            }
        )

        with pytest.raises(ValueError, match=r"target_column .* not found"):
            analyzer.calculate(df, target_column="SPY")

    def test_正常系_indexが保持される(self) -> None:
        """結果のDataFrameがオリジナルのindexを保持することを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame(
            {
                "AAPL": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "SPY": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            },
            index=dates,
        )

        result = analyzer.calculate(df, target_column="SPY")

        # indexが保持されている
        assert list(result.index) == list(dates)


class TestRollingCorrelationAnalyzerAnalyze:
    """Test analyze convenience method (inherited from StatisticalAnalyzer)."""

    def test_正常系_analyzeメソッドが使える(self) -> None:
        """analyzeメソッドが正しく動作することを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        df = pd.DataFrame(
            {
                "AAPL": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "SPY": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            }
        )

        result = analyzer.analyze(df, target_column="SPY")

        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns

    def test_異常系_validate失敗でValueError(self) -> None:
        """validate_inputが失敗した場合ValueErrorが発生することを確認。"""
        analyzer = RollingCorrelationAnalyzer()
        df = pd.DataFrame()  # 空のDataFrame

        with pytest.raises(ValueError, match="Input validation failed"):
            analyzer.analyze(df, target_column="SPY")


class TestRollingCorrelationAnalyzerName:
    """Test name property."""

    def test_正常系_nameプロパティがクラス名を返す(self) -> None:
        """nameプロパティがクラス名を返すことを確認。"""
        analyzer = RollingCorrelationAnalyzer()
        assert analyzer.name == "RollingCorrelationAnalyzer"


class TestRollingCorrelationAnalyzerDocstrings:
    """Test that all public methods have docstrings."""

    def test_正常系_クラスにDocstringがある(self) -> None:
        """クラスにDocstringがあることを確認。"""
        assert RollingCorrelationAnalyzer.__doc__ is not None
        assert "rolling correlation" in RollingCorrelationAnalyzer.__doc__.lower()

    def test_正常系_initにDocstringがある(self) -> None:
        """__init__にDocstringがあることを確認。"""
        assert RollingCorrelationAnalyzer.__init__.__doc__ is not None

    def test_正常系_calculateにDocstringがある(self) -> None:
        """calculateにDocstringがあることを確認。"""
        assert RollingCorrelationAnalyzer.calculate.__doc__ is not None

    def test_正常系_validate_inputにDocstringがある(self) -> None:
        """validate_inputにDocstringがあることを確認。"""
        assert RollingCorrelationAnalyzer.validate_input.__doc__ is not None


class TestRollingCorrelationAnalyzerExports:
    """Test module exports."""

    def test_正常系_RollingCorrelationAnalyzerがエクスポートされている(self) -> None:
        """RollingCorrelationAnalyzerがエクスポートされていることを確認。"""
        from analyze.statistics.correlation import __all__

        assert "RollingCorrelationAnalyzer" in __all__


class TestRollingCorrelationAnalyzerParametrized:
    """Parametrized tests for window and min_periods combinations."""

    @pytest.mark.parametrize(
        "window,min_periods",
        [
            (5, 3),
            (10, 5),
            (20, 10),
            (60, 30),
            (252, 30),
        ],
    )
    def test_パラメトライズ_様々なwindowとmin_periodsの組み合わせで計算できる(
        self, window: int, min_periods: int
    ) -> None:
        """様々なwindowとmin_periodsの組み合わせで相関が計算されることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=window, min_periods=min_periods)

        # 十分なデータを生成（windowの2倍）
        n = max(window * 2, 60)
        df = pd.DataFrame(
            {
                "AAPL": [1.0 + i * 0.1 for i in range(n)],
                "SPY": [2.0 + i * 0.2 for i in range(n)],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 結果がDataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
        # 先頭のNaN数がmin_periods-1であることを確認
        nan_count = result["AAPL"].iloc[: min_periods - 1].isna().sum()
        assert nan_count == min_periods - 1
        # min_periods以降は有効な値
        assert pd.notna(result["AAPL"].iloc[min_periods - 1])

    @pytest.mark.parametrize(
        "window,min_periods,expected_nan_count",
        [
            (5, 3, 2),
            (10, 5, 4),
            (20, 10, 9),
        ],
    )
    def test_パラメトライズ_先頭のNaN数がmin_periodsから1を引いた数(
        self, window: int, min_periods: int, expected_nan_count: int
    ) -> None:
        """先頭のNaN数がmin_periods-1であることを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=window, min_periods=min_periods)

        n = window * 2
        df = pd.DataFrame(
            {
                "AAPL": [1.0 + i * 0.1 for i in range(n)],
                "SPY": [2.0 + i * 0.2 for i in range(n)],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        nan_count = result["AAPL"].iloc[:expected_nan_count].isna().sum()
        assert nan_count == expected_nan_count

    @pytest.mark.parametrize(
        "window,min_periods",
        [
            (5, 5),
            (10, 10),
            (20, 20),
        ],
    )
    def test_パラメトライズ_windowとmin_periodsが同じ場合も動作(
        self, window: int, min_periods: int
    ) -> None:
        """windowとmin_periodsが同じ場合も正しく動作することを確認。"""
        analyzer = RollingCorrelationAnalyzer(window=window, min_periods=min_periods)

        n = window * 2
        df = pd.DataFrame(
            {
                "AAPL": [1.0 + i * 0.1 for i in range(n)],
                "SPY": [2.0 + i * 0.2 for i in range(n)],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # min_periods-1 = window-1 がNaN
        nan_count = result["AAPL"].iloc[: window - 1].isna().sum()
        assert nan_count == window - 1
