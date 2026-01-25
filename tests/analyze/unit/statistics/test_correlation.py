"""Unit tests for analyze.statistics.correlation module.

This module tests correlation analysis functions including:
- calculate_correlation: Calculate pairwise correlation coefficient
- calculate_correlation_matrix: Calculate correlation matrix for multiple series
- calculate_rolling_correlation: Calculate rolling correlation
- calculate_beta: Calculate beta coefficient against benchmark
- calculate_rolling_beta: Calculate rolling beta coefficient
- CorrelationAnalyzer: Comprehensive correlation analysis class

Test patterns are inherited from market_analysis.analysis.correlation tests.
"""

import math

import numpy as np
import pandas as pd
import pytest

from analyze.statistics.correlation import (
    CorrelationAnalyzer,
    CorrelationResult,
    calculate_beta,
    calculate_correlation,
    calculate_correlation_matrix,
    calculate_rolling_beta,
    calculate_rolling_correlation,
)


class TestCalculateCorrelation:
    """Tests for calculate_correlation function."""

    def test_正常系_完全正相関(self) -> None:
        """完全正相関（r=1.0）が正しく計算されることを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        result = calculate_correlation(a, b)
        assert result == pytest.approx(1.0)

    def test_正常系_完全負相関(self) -> None:
        """完全負相関（r=-1.0）が正しく計算されることを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([10.0, 8.0, 6.0, 4.0, 2.0])

        result = calculate_correlation(a, b)
        assert result == pytest.approx(-1.0)

    def test_正常系_無相関_定数系列(self) -> None:
        """定数系列との相関がNaNであることを確認（分散がゼロ）。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([3.0, 3.0, 3.0, 3.0, 3.0])

        result = calculate_correlation(a, b)
        assert math.isnan(result)

    def test_正常系_相関係数の範囲(
        self, sample_series: pd.Series, benchmark_returns: pd.Series
    ) -> None:
        """相関係数が[-1, 1]の範囲内であることを確認。"""
        # 異なる長さを揃える
        a = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0])
        b = pd.Series([2.0, 4.0, 1.0, 6.0, 3.0])

        result = calculate_correlation(a, b)
        assert -1.0 <= result <= 1.0

    def test_正常系_Spearman相関(self) -> None:
        """Spearman順位相関が正しく計算されることを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([1.0, 4.0, 9.0, 16.0, 25.0])  # 単調増加

        result = calculate_correlation(a, b, method="spearman")
        # 単調増加なのでSpearman相関は1.0
        assert result == pytest.approx(1.0)

    def test_正常系_Kendall相関(self) -> None:
        """Kendall tau相関が正しく計算されることを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        result = calculate_correlation(a, b, method="kendall")
        assert result == pytest.approx(1.0)

    def test_異常系_系列長が異なるとValueError(self) -> None:
        """系列長が異なる場合ValueErrorが発生することを確認。"""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0])

        with pytest.raises(ValueError, match="must have equal length"):
            calculate_correlation(a, b)

    def test_異常系_無効なメソッドでValueError(self) -> None:
        """無効な相関メソッドでValueErrorが発生することを確認。"""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Invalid method"):
            calculate_correlation(a, b, method="invalid")  # type: ignore[arg-type]

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_correlation(empty_series, empty_series)
        assert math.isnan(result)

    def test_正常系_NaN含むデータで有効ペアのみ計算(self) -> None:
        """NaN値を含むデータで有効なペアのみで計算されることを確認。"""
        a = pd.Series([1.0, np.nan, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, np.nan, 10.0])

        result = calculate_correlation(a, b)
        assert not math.isnan(result)
        assert -1.0 <= result <= 1.0

    def test_エッジケース_データ不足でNaN(self) -> None:
        """データが2点未満の場合NaNが返されることを確認。"""
        a = pd.Series([1.0])
        b = pd.Series([2.0])

        result = calculate_correlation(a, b)
        assert math.isnan(result)


class TestCalculateCorrelationMatrix:
    """Tests for calculate_correlation_matrix function."""

    def test_正常系_行列が対称(self, sample_dataframe: pd.DataFrame) -> None:
        """相関行列が対称であることを確認。"""
        matrix = calculate_correlation_matrix(sample_dataframe)

        assert matrix.loc["A", "B"] == pytest.approx(matrix.loc["B", "A"])
        assert matrix.loc["A", "C"] == pytest.approx(matrix.loc["C", "A"])
        assert matrix.loc["B", "C"] == pytest.approx(matrix.loc["C", "B"])

    def test_正常系_対角成分は1(self, sample_dataframe: pd.DataFrame) -> None:
        """対角成分が1.0であることを確認。"""
        matrix = calculate_correlation_matrix(sample_dataframe)

        assert matrix.loc["A", "A"] == pytest.approx(1.0)
        assert matrix.loc["B", "B"] == pytest.approx(1.0)
        assert matrix.loc["C", "C"] == pytest.approx(1.0)

    def test_正常系_全値が範囲内(self, sample_dataframe: pd.DataFrame) -> None:
        """全ての値が[-1, 1]の範囲内であることを確認。"""
        matrix = calculate_correlation_matrix(sample_dataframe)

        for col in matrix.columns:
            for row in matrix.index:
                assert -1.0 <= matrix.loc[row, col] <= 1.0

    def test_正常系_行列形状(self, sample_dataframe: pd.DataFrame) -> None:
        """行列の形状が正しいことを確認。"""
        matrix = calculate_correlation_matrix(sample_dataframe)

        assert matrix.shape == (3, 3)
        assert list(matrix.columns) == ["A", "B", "C"]
        assert list(matrix.index) == ["A", "B", "C"]

    def test_異常系_列数不足でValueError(self) -> None:
        """列数が2未満の場合ValueErrorが発生することを確認。"""
        data = pd.DataFrame({"A": [1.0, 2.0, 3.0]})

        with pytest.raises(ValueError, match="at least 2 columns"):
            calculate_correlation_matrix(data)

    def test_正常系_Spearman行列(self) -> None:
        """Spearman相関行列が正しく計算されることを確認。"""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0, 5.0],
                "B": [1.0, 4.0, 9.0, 16.0, 25.0],  # Aと単調関係
            }
        )

        matrix = calculate_correlation_matrix(data, method="spearman")
        assert matrix.loc["A", "B"] == pytest.approx(1.0)

    def test_異常系_無効なメソッドでValueError(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """無効な相関メソッドでValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="Invalid method"):
            calculate_correlation_matrix(
                sample_dataframe,
                method="invalid",  # type: ignore[arg-type]
            )


class TestCalculateRollingCorrelation:
    """Tests for calculate_rolling_correlation function."""

    def test_正常系_ローリング相関計算(self) -> None:
        """ローリング相関が正しく計算されることを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0])

        rolling = calculate_rolling_correlation(a, b, window=5)

        # 最初の4値はNaN（window-1）
        assert pd.isna(rolling.iloc[0])
        assert pd.isna(rolling.iloc[1])
        assert pd.isna(rolling.iloc[2])
        assert pd.isna(rolling.iloc[3])

        # index 4以降は有効な相関値
        for i in range(4, 10):
            assert rolling.iloc[i] == pytest.approx(1.0)

    def test_正常系_先頭のNaN数(self) -> None:
        """先頭のNaN数がwindow-1であることを確認。"""
        a = pd.Series(range(20), dtype=np.float64)
        b = pd.Series(range(20), dtype=np.float64)

        rolling = calculate_rolling_correlation(a, b, window=10)

        assert rolling.iloc[:9].isna().all()
        assert rolling.iloc[9:].notna().all()

    def test_異常系_系列長が異なるとValueError(self) -> None:
        """系列長が異なる場合ValueErrorが発生することを確認。"""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0])

        with pytest.raises(ValueError, match="must have equal length"):
            calculate_rolling_correlation(a, b, window=2)

    def test_異常系_無効なwindowでValueError(self) -> None:
        """window < 2の場合ValueErrorが発生することを確認。"""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Window must be at least 2"):
            calculate_rolling_correlation(a, b, window=1)

    def test_正常系_カスタムmin_periods(self) -> None:
        """カスタムmin_periodsが適用されることを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        rolling = calculate_rolling_correlation(a, b, window=5, min_periods=3)

        # min_periods=3なので、index 2から有効
        assert pd.isna(rolling.iloc[0])
        assert pd.isna(rolling.iloc[1])
        assert pd.notna(rolling.iloc[2])

    def test_異常系_無効なmin_periodsでValueError(self) -> None:
        """min_periods < 2の場合ValueErrorが発生することを確認。"""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="min_periods must be at least 2"):
            calculate_rolling_correlation(a, b, window=3, min_periods=1)


class TestCalculateBeta:
    """Tests for calculate_beta function."""

    def test_正常系_ベータ2の資産(self) -> None:
        """ベンチマークの2倍動く資産のベータが2.0であることを確認。"""
        # 資産はベンチマークの2倍動く
        asset = pd.Series([0.02, 0.04, -0.02, 0.06, 0.02])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = calculate_beta(asset, benchmark)
        assert beta == pytest.approx(2.0)

    def test_正常系_ベータ1の資産(self) -> None:
        """ベンチマークと同じ動きをする資産のベータが1.0であることを確認。"""
        asset = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = calculate_beta(asset, benchmark)
        assert beta == pytest.approx(1.0)

    def test_正常系_ベータ0_5の資産(self) -> None:
        """ベンチマークの0.5倍動く資産のベータが0.5であることを確認。"""
        # 資産はベンチマークの半分動く
        asset = pd.Series([0.005, 0.01, -0.005, 0.015, 0.005])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = calculate_beta(asset, benchmark)
        assert beta == pytest.approx(0.5)

    def test_正常系_負のベータ(self) -> None:
        """逆相関の資産で負のベータが計算されることを確認。"""
        # 資産はベンチマークと逆に動く
        asset = pd.Series([-0.01, -0.02, 0.01, -0.03, -0.01])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = calculate_beta(asset, benchmark)
        assert beta == pytest.approx(-1.0)

    def test_異常系_系列長が異なるとValueError(self) -> None:
        """系列長が異なる場合ValueErrorが発生することを確認。"""
        asset = pd.Series([0.01, 0.02])
        benchmark = pd.Series([0.01])

        with pytest.raises(ValueError, match="must have equal length"):
            calculate_beta(asset, benchmark)

    def test_正常系_NaN含むデータで有効ペアのみ計算(self) -> None:
        """NaN値を含むデータで有効なペアのみで計算されることを確認。"""
        asset = pd.Series([0.01, np.nan, 0.03, 0.04, 0.05])
        benchmark = pd.Series([0.005, 0.01, np.nan, 0.02, 0.025])

        beta = calculate_beta(asset, benchmark)
        assert not math.isnan(beta)

    def test_異常系_ベンチマーク分散ゼロでNaN(self) -> None:
        """ベンチマークの分散がゼロの場合NaNが返されることを確認。"""
        asset = pd.Series([0.01, 0.02, 0.03])
        benchmark = pd.Series([0.01, 0.01, 0.01])

        beta = calculate_beta(asset, benchmark)
        assert math.isnan(beta)

    def test_エッジケース_データ不足でNaN(self) -> None:
        """データが2点未満の場合NaNが返されることを確認。"""
        asset = pd.Series([0.01])
        benchmark = pd.Series([0.005])

        beta = calculate_beta(asset, benchmark)
        assert math.isnan(beta)


class TestCalculateRollingBeta:
    """Tests for calculate_rolling_beta function."""

    def test_正常系_ローリングベータ計算(self) -> None:
        """ローリングベータが正しく計算されることを確認。"""
        # 資産はベンチマークの2倍動く
        asset = pd.Series([0.02, 0.04, -0.02, 0.06, 0.02] * 10)
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01] * 10)

        rolling = calculate_rolling_beta(asset, benchmark, window=20)

        # 最初の19値はNaN
        assert rolling.iloc[:19].isna().all()

        # ベータは約2.0
        valid_betas = rolling.dropna()
        for beta in valid_betas:
            assert beta == pytest.approx(2.0, rel=0.01)

    def test_正常系_先頭のNaN数(self) -> None:
        """先頭のNaN数がwindow-1であることを確認。"""
        asset = pd.Series(np.random.randn(30))
        benchmark = pd.Series(np.random.randn(30))

        rolling = calculate_rolling_beta(asset, benchmark, window=10)
        assert rolling.iloc[:9].isna().all()

    def test_異常系_無効なwindowでValueError(self) -> None:
        """window < 2の場合ValueErrorが発生することを確認。"""
        asset = pd.Series([0.01, 0.02, 0.03])
        benchmark = pd.Series([0.01, 0.02, 0.03])

        with pytest.raises(ValueError, match="Window must be at least 2"):
            calculate_rolling_beta(asset, benchmark, window=1)

    def test_異常系_系列長が異なるとValueError(self) -> None:
        """系列長が異なる場合ValueErrorが発生することを確認。"""
        asset = pd.Series([0.01, 0.02, 0.03])
        benchmark = pd.Series([0.01, 0.02])

        with pytest.raises(ValueError, match="must have equal length"):
            calculate_rolling_beta(asset, benchmark, window=2)

    def test_正常系_カスタムmin_periods(self) -> None:
        """カスタムmin_periodsが適用されることを確認。"""
        asset = pd.Series([0.02, 0.04, -0.02, 0.06, 0.02])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        rolling = calculate_rolling_beta(asset, benchmark, window=5, min_periods=3)

        # min_periods=3なので、index 2から有効
        assert pd.isna(rolling.iloc[0])
        assert pd.isna(rolling.iloc[1])
        assert pd.notna(rolling.iloc[2])


class TestCorrelationAnalyzer:
    """Tests for CorrelationAnalyzer class."""

    def test_正常系_インスタンス生成(self) -> None:
        """CorrelationAnalyzerインスタンスが正しく生成されることを確認。"""
        analyzer = CorrelationAnalyzer()
        assert analyzer is not None

    def test_正常系_analyze結果の型(self, sample_dataframe: pd.DataFrame) -> None:
        """analyzeメソッドがCorrelationResultを返すことを確認。"""
        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(sample_dataframe, period="1Y")

        assert isinstance(result, CorrelationResult)

    def test_正常系_analyze結果のシンボル(self, sample_dataframe: pd.DataFrame) -> None:
        """analyzeメソッドがシンボルを正しく取得することを確認。"""
        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(sample_dataframe)

        assert result.symbols == ["A", "B", "C"]

    def test_正常系_analyze結果のperiod(self, sample_dataframe: pd.DataFrame) -> None:
        """analyzeメソッドがperiodを正しく設定することを確認。"""
        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(sample_dataframe, period="2024-01-01 to 2024-12-31")

        assert result.period == "2024-01-01 to 2024-12-31"

    def test_正常系_analyze結果のmethod(self, sample_dataframe: pd.DataFrame) -> None:
        """analyzeメソッドがmethodを正しく設定することを確認。"""
        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(sample_dataframe, method="spearman")

        assert result.method == "spearman"

    def test_正常系_analyze結果の相関行列(self) -> None:
        """analyzeメソッドが正しい相関行列を返すことを確認。"""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0, 5.0],
                "B": [2.0, 4.0, 6.0, 8.0, 10.0],  # Aと完全相関
            }
        )

        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(data)

        # 対角は1.0
        assert result.correlation_matrix.loc["A", "A"] == pytest.approx(1.0)
        assert result.correlation_matrix.loc["B", "B"] == pytest.approx(1.0)

        # 完全相関なので1.0
        assert result.correlation_matrix.loc["A", "B"] == pytest.approx(1.0)

    def test_正常系_静的メソッドの呼び出し(self) -> None:
        """静的メソッドがクラスから直接呼び出せることを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        # 静的メソッドとして呼び出し
        corr = CorrelationAnalyzer.calculate_correlation(a, b)
        assert corr == pytest.approx(1.0)


class TestCorrelationResult:
    """Tests for CorrelationResult Pydantic model."""

    def test_正常系_モデル作成(self, sample_dataframe: pd.DataFrame) -> None:
        """CorrelationResultモデルが正しく作成されることを確認。"""
        matrix = calculate_correlation_matrix(sample_dataframe)

        result = CorrelationResult(
            symbols=["A", "B", "C"],
            correlation_matrix=matrix,
            period="1Y",
            method="pearson",
        )

        assert result.symbols == ["A", "B", "C"]
        assert result.period == "1Y"
        assert result.method == "pearson"

    def test_正常系_デフォルトperiod(self, sample_dataframe: pd.DataFrame) -> None:
        """periodのデフォルト値が空文字列であることを確認。"""
        matrix = calculate_correlation_matrix(sample_dataframe)

        result = CorrelationResult(
            symbols=["A", "B", "C"],
            correlation_matrix=matrix,
            method="pearson",
        )

        assert result.period == ""

    def test_正常系_相関行列へのアクセス(self, sample_dataframe: pd.DataFrame) -> None:
        """CorrelationResultから相関行列にアクセスできることを確認。"""
        matrix = calculate_correlation_matrix(sample_dataframe)

        result = CorrelationResult(
            symbols=["A", "B", "C"],
            correlation_matrix=matrix,
            period="1Y",
            method="pearson",
        )

        # 行列の値にアクセス
        assert result.correlation_matrix.loc["A", "B"] == matrix.loc["A", "B"]


class TestParametrizedCorrelation:
    """Parametrized tests for correlation functions."""

    @pytest.mark.parametrize(
        "method",
        ["pearson", "spearman", "kendall"],
    )
    def test_パラメトライズ_全相関メソッドが動作(self, method: str) -> None:
        """全ての相関メソッドが正しく動作することを確認。"""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        result = calculate_correlation(a, b, method=method)  # type: ignore[arg-type]
        assert result == pytest.approx(1.0)

    @pytest.mark.parametrize(
        "window,expected_nan_count",
        [
            (5, 4),
            (10, 9),
            (3, 2),
        ],
    )
    def test_パラメトライズ_ローリング相関のNaN数(
        self, window: int, expected_nan_count: int
    ) -> None:
        """ローリング相関の先頭NaN数がwindow-1であることを確認。"""
        a = pd.Series(range(20), dtype=np.float64)
        b = pd.Series(range(20), dtype=np.float64)

        rolling = calculate_rolling_correlation(a, b, window=window)
        nan_count = rolling.iloc[:expected_nan_count].isna().sum()

        assert nan_count == expected_nan_count
