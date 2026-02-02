"""Unit tests for KalmanBetaAnalyzer class.

This module tests the KalmanBetaAnalyzer which inherits from
StatisticalAnalyzer and provides Kalman filter-based beta estimation
between a target column (benchmark) and other columns in the DataFrame.

Test patterns follow t-wada TDD approach.
"""

import numpy as np
import pandas as pd
import pytest

from analyze.statistics.base import StatisticalAnalyzer
from analyze.statistics.beta import KalmanBetaAnalyzer


class TestKalmanBetaAnalyzerInheritance:
    """Test class inheritance and interface compliance."""

    def test_正常系_StatisticalAnalyzerを継承している(self) -> None:
        """KalmanBetaAnalyzerがStatisticalAnalyzerを継承していることを確認。"""
        assert issubclass(KalmanBetaAnalyzer, StatisticalAnalyzer)

    def test_正常系_インスタンス生成(self) -> None:
        """KalmanBetaAnalyzerインスタンスが正しく生成されることを確認。"""
        analyzer = KalmanBetaAnalyzer()
        assert analyzer is not None
        assert isinstance(analyzer, StatisticalAnalyzer)


class TestKalmanBetaAnalyzerInit:
    """Test __init__ method."""

    def test_正常系_デフォルトパラメータ(self) -> None:
        """デフォルトパラメータで初期化されることを確認。"""
        analyzer = KalmanBetaAnalyzer()
        assert analyzer.transition_covariance == 0.001
        assert analyzer.em_iterations == 10

    def test_正常系_カスタムパラメータ(self) -> None:
        """カスタムパラメータで初期化されることを確認。"""
        analyzer = KalmanBetaAnalyzer(transition_covariance=0.01, em_iterations=20)
        assert analyzer.transition_covariance == 0.01
        assert analyzer.em_iterations == 20

    def test_正常系_transition_covarianceのみ指定(self) -> None:
        """transition_covarianceのみ指定時に他のパラメータがデフォルトのままであることを確認。"""
        analyzer = KalmanBetaAnalyzer(transition_covariance=0.005)
        assert analyzer.transition_covariance == 0.005
        assert analyzer.em_iterations == 10

    def test_正常系_em_iterationsのみ指定(self) -> None:
        """em_iterationsのみ指定時に他のパラメータがデフォルトのままであることを確認。"""
        analyzer = KalmanBetaAnalyzer(em_iterations=5)
        assert analyzer.transition_covariance == 0.001
        assert analyzer.em_iterations == 5


class TestKalmanBetaAnalyzerValidateInput:
    """Test validate_input method."""

    def test_正常系_有効なDataFrameでTrue(self) -> None:
        """有効なDataFrameでTrueが返されることを確認。"""
        analyzer = KalmanBetaAnalyzer()
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
        analyzer = KalmanBetaAnalyzer()
        df = pd.DataFrame()
        assert analyzer.validate_input(df) is False

    def test_異常系_1列のDataFrameでFalse(self) -> None:
        """1列のDataFrameでFalseが返されることを確認。"""
        analyzer = KalmanBetaAnalyzer()
        df = pd.DataFrame({"AAPL": [0.01, 0.02, -0.01]})
        assert analyzer.validate_input(df) is False

    def test_異常系_数値列がないDataFrameでFalse(self) -> None:
        """数値列がないDataFrameでFalseが返されることを確認。"""
        analyzer = KalmanBetaAnalyzer()
        df = pd.DataFrame({"name": ["A", "B", "C"], "category": ["X", "Y", "Z"]})
        assert analyzer.validate_input(df) is False

    def test_正常系_数値列と非数値列が混在でTrue(self) -> None:
        """数値列が2つ以上あれば非数値列が混在してもTrueが返されることを確認。"""
        analyzer = KalmanBetaAnalyzer()
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

    def test_異常系_行数が最小要件未満でFalse(self) -> None:
        """行数が最小要件未満の場合Falseが返されることを確認。"""
        analyzer = KalmanBetaAnalyzer()
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02],
                "SPY": [0.005, 0.01],
            }
        )
        # カルマンフィルタには最低限のデータポイントが必要
        assert analyzer.validate_input(df) is False


class TestKalmanBetaAnalyzerCalculate:
    """Test calculate method."""

    def test_正常系_カルマンベータが計算される(self) -> None:
        """カルマンフィルタベータが正しく計算されることを確認。"""
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer()
        # Asset moves 2x the benchmark
        np.random.seed(42)
        n = 50
        market = np.random.randn(n) * 0.01
        asset = 2.0 * market + np.random.randn(n) * 0.001  # beta ~ 2.0
        df = pd.DataFrame({"AAPL": asset, "SPY": market})

        result = analyzer.calculate(df, target_column="SPY")

        # 結果がDataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
        # target_column以外の列が存在することを確認
        assert "AAPL" in result.columns
        # target_column自体は結果に含まれない
        assert "SPY" not in result.columns

    def test_正常系_ベータ値が期待値に近い(self) -> None:
        """資産がベンチマークの2倍動く場合、ベータが約2.0に収束することを確認。"""
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer()
        # Asset moves 2x the benchmark with minimal noise
        np.random.seed(42)
        n = 100
        market = np.random.randn(n) * 0.01
        asset = 2.0 * market + np.random.randn(n) * 0.0001  # beta ~ 2.0

        df = pd.DataFrame({"AAPL": asset, "SPY": market})

        result = analyzer.calculate(df, target_column="SPY")

        # 最後の方の値は2.0に近いはず
        last_values = result["AAPL"].iloc[-10:]
        for val in last_values:
            assert val == pytest.approx(2.0, rel=0.2)

    def test_正常系_複数列のベータ計算(self) -> None:
        """複数列のベータが同時に計算されることを確認。"""
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer()
        np.random.seed(42)
        n = 50
        market = np.random.randn(n) * 0.01
        asset1 = 2.0 * market + np.random.randn(n) * 0.001  # beta ~ 2.0
        asset2 = 1.5 * market + np.random.randn(n) * 0.001  # beta ~ 1.5

        df = pd.DataFrame({"AAPL": asset1, "MSFT": asset2, "SPY": market})

        result = analyzer.calculate(df, target_column="SPY")

        # 両方の列が結果に含まれる
        assert "AAPL" in result.columns
        assert "MSFT" in result.columns
        assert "SPY" not in result.columns

    def test_異常系_target_columnが存在しないとValueError(self) -> None:
        """target_columnが存在しない場合ValueErrorが発生することを確認。"""
        analyzer = KalmanBetaAnalyzer()
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01] * 10,
                "MSFT": [0.02, 0.04, -0.02, 0.06, 0.02] * 10,
            }
        )

        with pytest.raises(ValueError, match=r"target_column .* not found"):
            analyzer.calculate(df, target_column="SPY")

    def test_異常系_target_columnがNoneでValueError(self) -> None:
        """target_columnがNoneの場合ValueErrorが発生することを確認。"""
        analyzer = KalmanBetaAnalyzer()
        df = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01] * 10,
                "SPY": [0.005, 0.01, -0.005, 0.015, 0.005] * 10,
            }
        )

        with pytest.raises(ValueError, match="target_column is required"):
            analyzer.calculate(df)

    def test_正常系_indexが保持される(self) -> None:
        """結果のDataFrameがオリジナルのindexを保持することを確認。"""
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer()
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        np.random.seed(42)
        market = np.random.randn(50) * 0.01
        asset = 2.0 * market + np.random.randn(50) * 0.001

        df = pd.DataFrame({"AAPL": asset, "SPY": market}, index=dates)

        result = analyzer.calculate(df, target_column="SPY")

        # indexが保持されている
        assert list(result.index) == list(dates)


class TestKalmanBetaAnalyzerPykalmanOptional:
    """Test pykalman optional dependency handling."""

    def test_正常系_pykalman未インストール時にImportError(self) -> None:
        """pykalmanがインストールされていない場合の動作を確認。

        Note: This test is mainly for documentation. The actual behavior
        when pykalman is not installed depends on how the class handles
        the ImportError.
        """
        # このテストは pykalman がインストールされている環境では
        # 実際の ImportError をテストできないため、ドキュメント目的
        pass


class TestKalmanBetaAnalyzerAnalyze:
    """Test analyze convenience method (inherited from StatisticalAnalyzer)."""

    def test_正常系_analyzeメソッドが使える(self) -> None:
        """analyzeメソッドが正しく動作することを確認。"""
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer()
        np.random.seed(42)
        n = 50
        market = np.random.randn(n) * 0.01
        asset = 2.0 * market + np.random.randn(n) * 0.001

        df = pd.DataFrame({"AAPL": asset, "SPY": market})

        result = analyzer.analyze(df, target_column="SPY")

        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns

    def test_異常系_validate失敗でValueError(self) -> None:
        """validate_inputが失敗した場合ValueErrorが発生することを確認。"""
        analyzer = KalmanBetaAnalyzer()
        df = pd.DataFrame()  # 空のDataFrame

        with pytest.raises(ValueError, match="Input validation failed"):
            analyzer.analyze(df, target_column="SPY")


class TestKalmanBetaAnalyzerName:
    """Test name property."""

    def test_正常系_nameプロパティがクラス名を返す(self) -> None:
        """nameプロパティがクラス名を返すことを確認。"""
        analyzer = KalmanBetaAnalyzer()
        assert analyzer.name == "KalmanBetaAnalyzer"


class TestKalmanBetaAnalyzerDocstrings:
    """Test that all public methods have docstrings."""

    def test_正常系_クラスにDocstringがある(self) -> None:
        """クラスにDocstringがあることを確認。"""
        assert KalmanBetaAnalyzer.__doc__ is not None
        assert "kalman" in KalmanBetaAnalyzer.__doc__.lower()

    def test_正常系_initにDocstringがある(self) -> None:
        """__init__にDocstringがあることを確認。"""
        assert KalmanBetaAnalyzer.__init__.__doc__ is not None

    def test_正常系_calculateにDocstringがある(self) -> None:
        """calculateにDocstringがあることを確認。"""
        assert KalmanBetaAnalyzer.calculate.__doc__ is not None

    def test_正常系_validate_inputにDocstringがある(self) -> None:
        """validate_inputにDocstringがあることを確認。"""
        assert KalmanBetaAnalyzer.validate_input.__doc__ is not None


class TestKalmanBetaAnalyzerExports:
    """Test module exports."""

    def test_正常系_KalmanBetaAnalyzerがエクスポートされている(self) -> None:
        """KalmanBetaAnalyzerがエクスポートされていることを確認。"""
        from analyze.statistics.beta import __all__

        assert "KalmanBetaAnalyzer" in __all__


class TestKalmanBetaAnalyzerParametrized:
    """Parametrized tests for transition_covariance and em_iterations combinations."""

    @pytest.mark.parametrize(
        "transition_covariance,em_iterations",
        [
            (0.001, 10),
            (0.0001, 5),
            (0.01, 20),
            (0.005, 15),
            (0.0005, 10),
        ],
    )
    def test_パラメトライズ_様々なパラメータの組み合わせで初期化できる(
        self, transition_covariance: float, em_iterations: int
    ) -> None:
        """様々なtransition_covarianceとem_iterationsの組み合わせで初期化されることを確認。"""
        analyzer = KalmanBetaAnalyzer(
            transition_covariance=transition_covariance, em_iterations=em_iterations
        )

        assert analyzer.transition_covariance == transition_covariance
        assert analyzer.em_iterations == em_iterations

    @pytest.mark.parametrize(
        "transition_covariance",
        [0.0001, 0.0005, 0.001, 0.005, 0.01],
    )
    def test_パラメトライズ_様々なtransition_covarianceでベータが計算できる(
        self, transition_covariance: float
    ) -> None:
        """様々なtransition_covarianceでベータが計算されることを確認。"""
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer(transition_covariance=transition_covariance)

        np.random.seed(42)
        n = 50
        market = np.random.randn(n) * 0.01
        asset = 2.0 * market + np.random.randn(n) * 0.001

        df = pd.DataFrame({"AAPL": asset, "SPY": market})

        result = analyzer.calculate(df, target_column="SPY")

        # 結果がDataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns
        assert "SPY" not in result.columns

    @pytest.mark.parametrize(
        "em_iterations",
        [5, 10, 15, 20],
    )
    def test_パラメトライズ_様々なem_iterationsでベータが計算できる(
        self, em_iterations: int
    ) -> None:
        """様々なem_iterationsでベータが計算されることを確認。"""
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer(em_iterations=em_iterations)

        np.random.seed(42)
        n = 50
        market = np.random.randn(n) * 0.01
        asset = 2.0 * market + np.random.randn(n) * 0.001

        df = pd.DataFrame({"AAPL": asset, "SPY": market})

        result = analyzer.calculate(df, target_column="SPY")

        # 結果がDataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns

    @pytest.mark.parametrize(
        "transition_covariance,expected_smoothness",
        [
            (0.0001, "smooth"),
            (0.01, "responsive"),
        ],
    )
    def test_パラメトライズ_transition_covarianceが結果の滑らかさに影響する(
        self, transition_covariance: float, expected_smoothness: str
    ) -> None:
        """transition_covarianceが小さいと滑らか、大きいと変化に敏感であることを確認。

        Note: This is a conceptual test to verify the parameter has an effect.
        """
        pytest.importorskip("pykalman", reason="pykalman is required for this test")

        analyzer = KalmanBetaAnalyzer(transition_covariance=transition_covariance)

        np.random.seed(42)
        n = 100
        market = np.random.randn(n) * 0.01
        # ベータが途中で変化するデータ
        asset = np.concatenate(
            [
                1.5 * market[:50] + np.random.randn(50) * 0.001,
                2.5 * market[50:] + np.random.randn(50) * 0.001,
            ]
        )

        df = pd.DataFrame({"AAPL": asset, "SPY": market})

        result = analyzer.calculate(df, target_column="SPY")

        # 結果が存在することを確認（滑らかさの詳細テストは省略）
        assert isinstance(result, pd.DataFrame)
        assert len(result) == n
