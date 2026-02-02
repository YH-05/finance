"""Unit tests for RollingBetaAnalyzer class.

This module tests the RollingBetaAnalyzer which inherits from
StatisticalAnalyzer and provides rolling beta calculations
between a target column (benchmark) and other columns in the DataFrame.

Test patterns follow t-wada TDD approach.
"""

from typing import Literal

import numpy as np
import pandas as pd
import pytest

from analyze.statistics.base import StatisticalAnalyzer
from analyze.statistics.beta import RollingBetaAnalyzer


class TestRollingBetaAnalyzerInheritance:
    """Test class inheritance and interface compliance."""

    def test_正常系_StatisticalAnalyzerを継承している(self) -> None:
        """RollingBetaAnalyzerがStatisticalAnalyzerを継承していることを確認。"""
        assert issubclass(RollingBetaAnalyzer, StatisticalAnalyzer)

    def test_正常系_インスタンス生成(self) -> None:
        """RollingBetaAnalyzerインスタンスが正しく生成されることを確認。"""
        analyzer = RollingBetaAnalyzer()
        assert analyzer is not None
        assert isinstance(analyzer, StatisticalAnalyzer)


class TestRollingBetaAnalyzerInit:
    """Test __init__ method."""

    def test_正常系_デフォルトパラメータ(self) -> None:
        """デフォルトパラメータで初期化されることを確認。"""
        analyzer = RollingBetaAnalyzer()
        assert analyzer.window == 60
        assert analyzer.freq == "M"
        assert analyzer.window_years == 3

    def test_正常系_カスタムパラメータ(self) -> None:
        """カスタムパラメータで初期化されることを確認。"""
        analyzer = RollingBetaAnalyzer(window=120, freq="W", window_years=5)
        assert analyzer.window == 120
        assert analyzer.freq == "W"
        assert analyzer.window_years == 5

    def test_正常系_windowのみ指定(self) -> None:
        """windowのみ指定時に他のパラメータがデフォルトのままであることを確認。"""
        analyzer = RollingBetaAnalyzer(window=100)
        assert analyzer.window == 100
        assert analyzer.freq == "M"
        assert analyzer.window_years == 3

    def test_正常系_freqのみ指定(self) -> None:
        """freqのみ指定時に他のパラメータがデフォルトのままであることを確認。"""
        analyzer = RollingBetaAnalyzer(freq="W")
        assert analyzer.window == 60
        assert analyzer.freq == "W"
        assert analyzer.window_years == 3

    def test_正常系_window_yearsのみ指定(self) -> None:
        """window_yearsのみ指定時に他のパラメータがデフォルトのままであることを確認。"""
        analyzer = RollingBetaAnalyzer(window_years=5)
        assert analyzer.window == 60
        assert analyzer.freq == "M"
        assert analyzer.window_years == 5

    def test_正常系_freq_Wが有効(self) -> None:
        """freqに"W"を指定できることを確認。"""
        analyzer = RollingBetaAnalyzer(freq="W")
        assert analyzer.freq == "W"

    def test_正常系_freq_Mが有効(self) -> None:
        """freqに"M"を指定できることを確認。"""
        analyzer = RollingBetaAnalyzer(freq="M")
        assert analyzer.freq == "M"

    def test_正常系_window_years_3が有効(self) -> None:
        """window_yearsに3を指定できることを確認。"""
        analyzer = RollingBetaAnalyzer(window_years=3)
        assert analyzer.window_years == 3

    def test_正常系_window_years_5が有効(self) -> None:
        """window_yearsに5を指定できることを確認。"""
        analyzer = RollingBetaAnalyzer(window_years=5)
        assert analyzer.window_years == 5


class TestRollingBetaAnalyzerValidateInput:
    """Test validate_input method."""

    def test_正常系_有効なDataFrameでTrue(self) -> None:
        """有効なDataFrameでTrueが返されることを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
                "SPY": [
                    0.005,
                    0.01,
                    -0.005,
                    0.015,
                    0.005,
                    0.01,
                    -0.005,
                    0.015,
                    0.005,
                    0.01,
                ],
            }
        )
        assert analyzer.validate_input(df) is True

    def test_異常系_空のDataFrameでFalse(self) -> None:
        """空のDataFrameでFalseが返されることを確認。"""
        analyzer = RollingBetaAnalyzer()
        df = pd.DataFrame()
        assert analyzer.validate_input(df) is False

    def test_異常系_1列のDataFrameでFalse(self) -> None:
        """1列のDataFrameでFalseが返されることを確認。"""
        analyzer = RollingBetaAnalyzer()
        df = pd.DataFrame({"AAPL": [0.01, 0.02, -0.01]})
        assert analyzer.validate_input(df) is False

    def test_異常系_数値列がないDataFrameでFalse(self) -> None:
        """数値列がないDataFrameでFalseが返されることを確認。"""
        analyzer = RollingBetaAnalyzer()
        df = pd.DataFrame({"name": ["A", "B", "C"], "category": ["X", "Y", "Z"]})
        assert analyzer.validate_input(df) is False

    def test_正常系_数値列と非数値列が混在でTrue(self) -> None:
        """数値列が2つ以上あれば非数値列が混在してもTrueが返されることを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
                "SPY": [
                    0.005,
                    0.01,
                    -0.005,
                    0.015,
                    0.005,
                    0.01,
                    -0.005,
                    0.015,
                    0.005,
                    0.01,
                ],
                "name": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
            }
        )
        assert analyzer.validate_input(df) is True

    def test_異常系_行数がwindow未満でFalse(self) -> None:
        """行数がwindow未満の場合Falseが返されることを確認。"""
        analyzer = RollingBetaAnalyzer(window=10)
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01],
                "SPY": [0.005, 0.01, -0.005],
            }
        )
        assert analyzer.validate_input(df) is False


class TestRollingBetaAnalyzerCalculate:
    """Test calculate method."""

    def test_正常系_ローリングベータが計算される(self) -> None:
        """ローリングベータが正しく計算されることを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        # Asset moves 2x the benchmark
        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 結果がDataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
        # target_column以外の列が存在することを確認
        assert "AAPL" in result.columns
        # target_column自体は結果に含まれない
        assert "SPY" not in result.columns

    def test_正常系_ベータ値が2に近い(self) -> None:
        """資産がベンチマークの2倍動く場合、ベータが約2.0になることを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        # Asset moves 2x the benchmark
        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # min_periods以降の値は2.0に近い
        valid_values = result["AAPL"].dropna()
        for val in valid_values:
            assert val == pytest.approx(2.0, rel=0.01)

    def test_正常系_先頭のNaN数(self) -> None:
        """先頭のNaN数がwindow-1であることを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 先頭4つ（window-1）がNaN
        for i in range(4):
            assert pd.isna(result["AAPL"].iloc[i])
        # 5番目以降は有効
        assert pd.notna(result["AAPL"].iloc[4])

    def test_正常系_複数列のベータ計算(self) -> None:
        """複数列のベータが同時に計算されることを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [
                    0.02,
                    0.04,
                    -0.02,
                    0.06,
                    0.02,
                    0.04,
                    -0.02,
                    0.06,
                    0.02,
                    0.04,
                ],  # beta=2
                "MSFT": [
                    0.015,
                    0.03,
                    -0.015,
                    0.045,
                    0.015,
                    0.03,
                    -0.015,
                    0.045,
                    0.015,
                    0.03,
                ],  # beta=1.5
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 両方の列が結果に含まれる
        assert "AAPL" in result.columns
        assert "MSFT" in result.columns
        assert "SPY" not in result.columns

        # AAPL は beta=2, MSFT は beta=1.5
        valid_aapl = result["AAPL"].dropna()
        valid_msft = result["MSFT"].dropna()

        for val in valid_aapl:
            assert val == pytest.approx(2.0, rel=0.01)
        for val in valid_msft:
            assert val == pytest.approx(1.5, rel=0.01)

    def test_異常系_target_columnが存在しないとValueError(self) -> None:
        """target_columnが存在しない場合ValueErrorが発生することを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01],
                "MSFT": [0.02, 0.04, -0.02, 0.06, 0.02],
            }
        )

        with pytest.raises(ValueError, match=r"target_column .* not found"):
            analyzer.calculate(df, target_column="SPY")

    def test_異常系_target_columnがNoneでValueError(self) -> None:
        """target_columnがNoneの場合ValueErrorが発生することを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
                "SPY": [
                    0.005,
                    0.01,
                    -0.005,
                    0.015,
                    0.005,
                    0.01,
                    -0.005,
                    0.015,
                    0.005,
                    0.01,
                ],
            }
        )

        with pytest.raises(ValueError, match="target_column is required"):
            analyzer.calculate(df)

    def test_正常系_indexが保持される(self) -> None:
        """結果のDataFrameがオリジナルのindexを保持することを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            },
            index=dates,
        )

        result = analyzer.calculate(df, target_column="SPY")

        # indexが保持されている
        assert list(result.index) == list(dates)

    def test_正常系_ベンチマーク分散がゼロでNaN(self) -> None:
        """ベンチマークの分散がゼロの場合、ベータがNaNになることを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
                "SPY": [
                    0.01,
                    0.01,
                    0.01,
                    0.01,
                    0.01,
                    0.01,
                    0.01,
                    0.01,
                    0.01,
                    0.01,
                ],  # constant
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        # 分散がゼロのウィンドウでNaN
        valid_values = result["AAPL"].dropna()
        assert len(valid_values) == 0 or all(pd.isna(result["AAPL"].iloc[4:]))


class TestRollingBetaAnalyzerAnalyze:
    """Test analyze convenience method (inherited from StatisticalAnalyzer)."""

    def test_正常系_analyzeメソッドが使える(self) -> None:
        """analyzeメソッドが正しく動作することを確認。"""
        analyzer = RollingBetaAnalyzer(window=5)
        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            }
        )

        result = analyzer.analyze(df, target_column="SPY")

        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns

    def test_異常系_validate失敗でValueError(self) -> None:
        """validate_inputが失敗した場合ValueErrorが発生することを確認。"""
        analyzer = RollingBetaAnalyzer()
        df = pd.DataFrame()  # 空のDataFrame

        with pytest.raises(ValueError, match="Input validation failed"):
            analyzer.analyze(df, target_column="SPY")


class TestRollingBetaAnalyzerName:
    """Test name property."""

    def test_正常系_nameプロパティがクラス名を返す(self) -> None:
        """nameプロパティがクラス名を返すことを確認。"""
        analyzer = RollingBetaAnalyzer()
        assert analyzer.name == "RollingBetaAnalyzer"


class TestRollingBetaAnalyzerDocstrings:
    """Test that all public methods have docstrings."""

    def test_正常系_クラスにDocstringがある(self) -> None:
        """クラスにDocstringがあることを確認。"""
        assert RollingBetaAnalyzer.__doc__ is not None
        assert "rolling beta" in RollingBetaAnalyzer.__doc__.lower()

    def test_正常系_initにDocstringがある(self) -> None:
        """__init__にDocstringがあることを確認。"""
        assert RollingBetaAnalyzer.__init__.__doc__ is not None

    def test_正常系_calculateにDocstringがある(self) -> None:
        """calculateにDocstringがあることを確認。"""
        assert RollingBetaAnalyzer.calculate.__doc__ is not None

    def test_正常系_validate_inputにDocstringがある(self) -> None:
        """validate_inputにDocstringがあることを確認。"""
        assert RollingBetaAnalyzer.validate_input.__doc__ is not None


class TestRollingBetaAnalyzerExports:
    """Test module exports."""

    def test_正常系_RollingBetaAnalyzerがエクスポートされている(self) -> None:
        """RollingBetaAnalyzerがエクスポートされていることを確認。"""
        from analyze.statistics.beta import __all__

        assert "RollingBetaAnalyzer" in __all__


class TestRollingBetaAnalyzerParametrized:
    """Parametrized tests for window, freq, and window_years combinations."""

    @pytest.mark.parametrize(
        "window,freq,window_years",
        [
            (60, "M", 3),
            (120, "M", 5),
            (36, "M", 3),
            (60, "W", 3),
            (156, "W", 3),
            (260, "W", 5),
        ],
    )
    def test_パラメトライズ_様々なパラメータの組み合わせで初期化できる(
        self, window: int, freq: Literal["W", "M"], window_years: Literal[3, 5]
    ) -> None:
        """様々なwindow, freq, window_yearsの組み合わせで初期化されることを確認。"""
        analyzer = RollingBetaAnalyzer(
            window=window, freq=freq, window_years=window_years
        )

        assert analyzer.window == window
        assert analyzer.freq == freq
        assert analyzer.window_years == window_years

    @pytest.mark.parametrize(
        "window",
        [5, 10, 20, 60, 120],
    )
    def test_パラメトライズ_様々なwindowサイズでベータが計算できる(
        self, window: int
    ) -> None:
        """様々なwindowサイズでベータが計算されることを確認。"""
        analyzer = RollingBetaAnalyzer(window=window)

        # 十分なデータを生成（windowの2倍）
        n = window * 2
        # Asset moves 2x the benchmark
        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02] * (n // 5 + 1),
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01] * (n // 5 + 1),
            }
        ).iloc[:n]

        result = analyzer.calculate(df, target_column="SPY")

        # 結果がDataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
        # 先頭のNaN数がwindow-1であることを確認
        nan_count = result["AAPL"].iloc[: window - 1].isna().sum()
        assert nan_count == window - 1
        # window以降は有効な値
        assert pd.notna(result["AAPL"].iloc[window - 1])

    @pytest.mark.parametrize(
        "window,expected_nan_count",
        [
            (5, 4),
            (10, 9),
            (20, 19),
            (60, 59),
        ],
    )
    def test_パラメトライズ_先頭のNaN数がwindowから1を引いた数(
        self, window: int, expected_nan_count: int
    ) -> None:
        """先頭のNaN数がwindow-1であることを確認。"""
        analyzer = RollingBetaAnalyzer(window=window)

        n = window * 2
        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02] * (n // 5 + 1),
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01] * (n // 5 + 1),
            }
        ).iloc[:n]

        result = analyzer.calculate(df, target_column="SPY")

        nan_count = result["AAPL"].iloc[:expected_nan_count].isna().sum()
        assert nan_count == expected_nan_count

    @pytest.mark.parametrize(
        "freq",
        ["W", "M"],
    )
    def test_パラメトライズ_全freqオプションが有効(
        self, freq: Literal["W", "M"]
    ) -> None:
        """全てのfreqオプションが正しく動作することを確認。"""
        analyzer = RollingBetaAnalyzer(window=5, freq=freq)

        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        assert isinstance(result, pd.DataFrame)
        assert analyzer.freq == freq

    @pytest.mark.parametrize(
        "window_years",
        [3, 5],
    )
    def test_パラメトライズ_全window_yearsオプションが有効(
        self, window_years: Literal[3, 5]
    ) -> None:
        """全てのwindow_yearsオプションが正しく動作することを確認。"""
        analyzer = RollingBetaAnalyzer(window=5, window_years=window_years)

        df = pd.DataFrame(
            {
                "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
                "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
            }
        )

        result = analyzer.calculate(df, target_column="SPY")

        assert isinstance(result, pd.DataFrame)
        assert analyzer.window_years == window_years
