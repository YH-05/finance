"""Unit tests for analyze.statistics.descriptive module.

This module tests descriptive statistics functions including:
- calculate_mean: Calculate arithmetic mean
- calculate_median: Calculate median value
- calculate_std: Calculate standard deviation
- calculate_var: Calculate variance
- calculate_skewness: Calculate skewness
- calculate_kurtosis: Calculate kurtosis
- describe: Generate comprehensive descriptive statistics
- calculate_quantile: Calculate specific quantile
- calculate_percentile_rank: Calculate percentile rank of a value
"""

import math

import numpy as np
import pandas as pd
import pytest
from analyze.statistics.descriptive import (
    DescriptiveStats,
    calculate_kurtosis,
    calculate_mean,
    calculate_median,
    calculate_percentile_rank,
    calculate_quantile,
    calculate_skewness,
    calculate_std,
    calculate_var,
    describe,
)


class TestCalculateMean:
    """Tests for calculate_mean function."""

    def test_正常系_基本的な平均値計算(self, sample_series: pd.Series) -> None:
        """基本的な平均値が正しく計算されることを確認。"""
        result = calculate_mean(sample_series)
        # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] の平均は 5.5
        assert result == pytest.approx(5.5)

    def test_正常系_NaN含むデータでNaNを除外して計算(
        self, sample_series_with_nan: pd.Series
    ) -> None:
        """NaN値を除外して平均が計算されることを確認。"""
        result = calculate_mean(sample_series_with_nan)
        # [1, 2, 4, 5, 7, 8, 9, 10] の平均は 5.75
        assert result == pytest.approx(5.75)

    def test_正常系_定数系列の平均(self, constant_series: pd.Series) -> None:
        """定数系列の平均が正しく計算されることを確認。"""
        result = calculate_mean(constant_series)
        assert result == pytest.approx(5.0)

    def test_正常系_負の値を含むデータ(self) -> None:
        """負の値を含むデータで平均が正しく計算されることを確認。"""
        series = pd.Series([-10.0, -5.0, 0.0, 5.0, 10.0])
        result = calculate_mean(series)
        assert result == pytest.approx(0.0)

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_mean(empty_series)
        assert math.isnan(result)

    def test_エッジケース_単一要素(self) -> None:
        """単一要素の場合、その値が平均になることを確認。"""
        series = pd.Series([42.0])
        result = calculate_mean(series)
        assert result == pytest.approx(42.0)


class TestCalculateMedian:
    """Tests for calculate_median function."""

    def test_正常系_奇数個データの中央値(self) -> None:
        """奇数個のデータで中央値が正しく計算されることを確認。"""
        series = pd.Series([1.0, 3.0, 5.0, 7.0, 9.0])
        result = calculate_median(series)
        assert result == pytest.approx(5.0)

    def test_正常系_偶数個データの中央値(self, sample_series: pd.Series) -> None:
        """偶数個のデータで中央値が正しく計算されることを確認。"""
        result = calculate_median(sample_series)
        # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] の中央値は 5.5
        assert result == pytest.approx(5.5)

    def test_正常系_NaN含むデータでNaNを除外して計算(
        self, sample_series_with_nan: pd.Series
    ) -> None:
        """NaN値を除外して中央値が計算されることを確認。"""
        result = calculate_median(sample_series_with_nan)
        # [1, 2, 4, 5, 7, 8, 9, 10] の中央値は 6.0
        assert result == pytest.approx(6.0)

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_median(empty_series)
        assert math.isnan(result)

    def test_エッジケース_単一要素(self) -> None:
        """単一要素の場合、その値が中央値になることを確認。"""
        series = pd.Series([42.0])
        result = calculate_median(series)
        assert result == pytest.approx(42.0)


class TestCalculateStd:
    """Tests for calculate_std function."""

    def test_正常系_標準偏差計算(self, sample_series: pd.Series) -> None:
        """標準偏差が正しく計算されることを確認。"""
        result = calculate_std(sample_series)
        # numpy.std(ddof=1) と一致することを確認
        expected = sample_series.std(ddof=1)
        assert result == pytest.approx(expected)

    def test_正常系_ddof0で母集団標準偏差(self, sample_series: pd.Series) -> None:
        """ddof=0で母集団標準偏差が計算されることを確認。"""
        result = calculate_std(sample_series, ddof=0)
        expected = sample_series.std(ddof=0)
        assert result == pytest.approx(expected)

    def test_正常系_NaN含むデータでNaNを除外して計算(
        self, sample_series_with_nan: pd.Series
    ) -> None:
        """NaN値を除外して標準偏差が計算されることを確認。"""
        result = calculate_std(sample_series_with_nan)
        expected = sample_series_with_nan.std(ddof=1)
        assert result == pytest.approx(expected)

    def test_正常系_定数系列の標準偏差はゼロ(self, constant_series: pd.Series) -> None:
        """定数系列の標準偏差が0であることを確認。"""
        result = calculate_std(constant_series)
        assert result == pytest.approx(0.0)

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_std(empty_series)
        assert math.isnan(result)

    def test_異常系_負のddofでValueError(self, sample_series: pd.Series) -> None:
        """負のddofでValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="ddof must be non-negative"):
            calculate_std(sample_series, ddof=-1)


class TestCalculateVar:
    """Tests for calculate_var function."""

    def test_正常系_分散計算(self, sample_series: pd.Series) -> None:
        """分散が正しく計算されることを確認。"""
        result = calculate_var(sample_series)
        expected = sample_series.var(ddof=1)
        assert result == pytest.approx(expected)

    def test_正常系_ddof0で母集団分散(self, sample_series: pd.Series) -> None:
        """ddof=0で母集団分散が計算されることを確認。"""
        result = calculate_var(sample_series, ddof=0)
        expected = sample_series.var(ddof=0)
        assert result == pytest.approx(expected)

    def test_正常系_分散と標準偏差の関係(self, sample_series: pd.Series) -> None:
        """分散が標準偏差の2乗であることを確認。"""
        var = calculate_var(sample_series)
        std = calculate_std(sample_series)
        assert var == pytest.approx(std**2)

    def test_正常系_定数系列の分散はゼロ(self, constant_series: pd.Series) -> None:
        """定数系列の分散が0であることを確認。"""
        result = calculate_var(constant_series)
        assert result == pytest.approx(0.0)

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_var(empty_series)
        assert math.isnan(result)

    def test_異常系_負のddofでValueError(self, sample_series: pd.Series) -> None:
        """負のddofでValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="ddof must be non-negative"):
            calculate_var(sample_series, ddof=-1)


class TestCalculateSkewness:
    """Tests for calculate_skewness function."""

    def test_正常系_対称分布のSkewnessはゼロに近い(self) -> None:
        """対称分布の歪度が0に近いことを確認。"""
        # 対称な分布
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 4.0, 3.0, 2.0, 1.0])
        result = calculate_skewness(series)
        assert result == pytest.approx(0.0, abs=0.1)

    def test_正常系_右に歪んだ分布は正のSkewness(
        self, skewed_series: pd.Series
    ) -> None:
        """右に歪んだ分布で正の歪度を持つことを確認。"""
        result = calculate_skewness(skewed_series)
        assert result > 0

    def test_正常系_左に歪んだ分布は負のSkewness(self) -> None:
        """左に歪んだ分布で負の歪度を持つことを確認。"""
        # 左に歪んだ分布（低い値に裾が長い＝mean < median）
        series = pd.Series([1.0, 2.0, 10.0, 15.0, 16.0, 16.5, 17.0, 17.5, 18.0, 19.0])
        result = calculate_skewness(series)
        assert result < 0

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_skewness(empty_series)
        assert math.isnan(result)

    def test_異常系_データ不足でNaN(self) -> None:
        """データが2個以下の場合NaNが返されることを確認。"""
        series = pd.Series([1.0, 2.0])
        result = calculate_skewness(series)
        assert math.isnan(result)


class TestCalculateKurtosis:
    """Tests for calculate_kurtosis function."""

    def test_正常系_正規分布に近い分布のKurtosisはゼロに近い(self) -> None:
        """正規分布に近い分布の尖度が0に近いことを確認（excess kurtosis）。"""
        # ある程度正規分布に近いデータ
        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 1000))
        result = calculate_kurtosis(series)
        # excess kurtosis なので 0 に近い（正規分布は 0）
        assert result == pytest.approx(0.0, abs=0.3)

    def test_正常系_尖った分布は正のKurtosis(self) -> None:
        """尖った分布（重い裾）で正の尖度を持つことを確認。"""
        # 裾の重い分布をシミュレート
        series = pd.Series([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0, -100.0])
        result = calculate_kurtosis(series)
        assert result > 0

    def test_正常系_平坦な分布は負のKurtosis(self) -> None:
        """平坦な分布（軽い裾）で負の尖度を持つことを確認。"""
        # 一様分布に近いデータ
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        result = calculate_kurtosis(series)
        # 一様分布の excess kurtosis は約 -1.2
        assert result < 0

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_kurtosis(empty_series)
        assert math.isnan(result)

    def test_異常系_データ不足でNaN(self) -> None:
        """データが3個以下の場合NaNが返されることを確認。"""
        series = pd.Series([1.0, 2.0, 3.0])
        result = calculate_kurtosis(series)
        assert math.isnan(result)


class TestDescribe:
    """Tests for describe function."""

    def test_正常系_DescriptiveStatsが返される(self, sample_series: pd.Series) -> None:
        """describe関数がDescriptiveStatsモデルを返すことを確認。"""
        result = describe(sample_series)
        assert isinstance(result, DescriptiveStats)

    def test_正常系_全フィールドが正しく計算される(
        self, sample_series: pd.Series
    ) -> None:
        """DescriptiveStatsの全フィールドが正しく計算されることを確認。"""
        result = describe(sample_series)

        assert result.count == 10
        assert result.mean == pytest.approx(5.5)
        assert result.median == pytest.approx(5.5)
        assert result.std == pytest.approx(sample_series.std(ddof=1))
        assert result.var == pytest.approx(sample_series.var(ddof=1))
        assert result.min == pytest.approx(1.0)
        assert result.max == pytest.approx(10.0)
        assert result.q25 == pytest.approx(3.25)
        assert result.q50 == pytest.approx(5.5)
        assert result.q75 == pytest.approx(7.75)

    def test_正常系_NaN含むデータで正しく計算(
        self, sample_series_with_nan: pd.Series
    ) -> None:
        """NaN値を含むデータで正しくカウントされることを確認。"""
        result = describe(sample_series_with_nan)
        # NaNを除外したカウント
        assert result.count == 8

    def test_異常系_空のSeriesで適切なデフォルト値(
        self, empty_series: pd.Series
    ) -> None:
        """空のSeriesの場合、count=0でNaN値を含むDescriptiveStatsが返されることを確認。"""
        result = describe(empty_series)
        assert result.count == 0
        assert math.isnan(result.mean)
        assert math.isnan(result.median)


class TestCalculateQuantile:
    """Tests for calculate_quantile function."""

    def test_正常系_50パーセンタイルは中央値(self, sample_series: pd.Series) -> None:
        """50パーセンタイルが中央値と一致することを確認。"""
        q50 = calculate_quantile(sample_series, 0.5)
        median = calculate_median(sample_series)
        assert q50 == pytest.approx(median)

    def test_正常系_25パーセンタイル(self, sample_series: pd.Series) -> None:
        """25パーセンタイルが正しく計算されることを確認。"""
        result = calculate_quantile(sample_series, 0.25)
        expected = sample_series.quantile(0.25)
        assert result == pytest.approx(expected)

    def test_正常系_75パーセンタイル(self, sample_series: pd.Series) -> None:
        """75パーセンタイルが正しく計算されることを確認。"""
        result = calculate_quantile(sample_series, 0.75)
        expected = sample_series.quantile(0.75)
        assert result == pytest.approx(expected)

    def test_正常系_最小値は0パーセンタイル(self, sample_series: pd.Series) -> None:
        """0パーセンタイルが最小値と一致することを確認。"""
        result = calculate_quantile(sample_series, 0.0)
        assert result == pytest.approx(sample_series.min())

    def test_正常系_最大値は100パーセンタイル(self, sample_series: pd.Series) -> None:
        """1.0パーセンタイルが最大値と一致することを確認。"""
        result = calculate_quantile(sample_series, 1.0)
        assert result == pytest.approx(sample_series.max())

    def test_異常系_範囲外のq値でValueError(self, sample_series: pd.Series) -> None:
        """q値が[0, 1]範囲外の場合ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="q must be between 0 and 1"):
            calculate_quantile(sample_series, 1.5)

        with pytest.raises(ValueError, match="q must be between 0 and 1"):
            calculate_quantile(sample_series, -0.1)

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_quantile(empty_series, 0.5)
        assert math.isnan(result)


class TestCalculatePercentileRank:
    """Tests for calculate_percentile_rank function."""

    def test_正常系_最小値のパーセンタイルランク(
        self, sample_series: pd.Series
    ) -> None:
        """最小値のパーセンタイルランクが0に近いことを確認。"""
        result = calculate_percentile_rank(sample_series, 1.0)
        # 1.0は10個中最小なので、パーセンタイルランクは低い
        assert result == pytest.approx(0.0, abs=0.15)

    def test_正常系_最大値のパーセンタイルランク(
        self, sample_series: pd.Series
    ) -> None:
        """最大値のパーセンタイルランクが100に近いことを確認。"""
        result = calculate_percentile_rank(sample_series, 10.0)
        # 10.0は10個中最大なので、パーセンタイルランクは高い
        assert result == pytest.approx(100.0, abs=15.0)

    def test_正常系_中央値のパーセンタイルランク(
        self, sample_series: pd.Series
    ) -> None:
        """中央値のパーセンタイルランクが約50であることを確認。"""
        median = calculate_median(sample_series)
        result = calculate_percentile_rank(sample_series, median)
        assert result == pytest.approx(50.0, abs=10.0)

    def test_正常系_範囲外の値_下限(self, sample_series: pd.Series) -> None:
        """データ範囲より小さい値のパーセンタイルランクが0であることを確認。"""
        result = calculate_percentile_rank(sample_series, 0.0)
        assert result == pytest.approx(0.0)

    def test_正常系_範囲外の値_上限(self, sample_series: pd.Series) -> None:
        """データ範囲より大きい値のパーセンタイルランクが100であることを確認。"""
        result = calculate_percentile_rank(sample_series, 100.0)
        assert result == pytest.approx(100.0)

    def test_異常系_空のSeriesでNaN(self, empty_series: pd.Series) -> None:
        """空のSeriesの場合NaNが返されることを確認。"""
        result = calculate_percentile_rank(empty_series, 5.0)
        assert math.isnan(result)


class TestDescriptiveStatsModel:
    """Tests for DescriptiveStats Pydantic model."""

    def test_正常系_モデル作成(self) -> None:
        """DescriptiveStatsモデルが正しく作成されることを確認。"""
        stats = DescriptiveStats(
            count=10,
            mean=5.5,
            median=5.5,
            std=3.0276,
            var=9.1667,
            min=1.0,
            max=10.0,
            q25=3.25,
            q50=5.5,
            q75=7.75,
            skewness=0.0,
            kurtosis=-1.2,
        )

        assert stats.count == 10
        assert stats.mean == pytest.approx(5.5)

    def test_正常系_NaN値を含むモデル(self) -> None:
        """NaN値を含むDescriptiveStatsモデルが作成できることを確認。"""
        stats = DescriptiveStats(
            count=0,
            mean=float("nan"),
            median=float("nan"),
            std=float("nan"),
            var=float("nan"),
            min=float("nan"),
            max=float("nan"),
            q25=float("nan"),
            q50=float("nan"),
            q75=float("nan"),
            skewness=float("nan"),
            kurtosis=float("nan"),
        )

        assert stats.count == 0
        assert math.isnan(stats.mean)

    def test_正常系_モデルのdict変換(self) -> None:
        """DescriptiveStatsモデルがdictに変換できることを確認。"""
        stats = DescriptiveStats(
            count=10,
            mean=5.5,
            median=5.5,
            std=3.0,
            var=9.0,
            min=1.0,
            max=10.0,
            q25=3.0,
            q50=5.5,
            q75=8.0,
            skewness=0.0,
            kurtosis=-1.2,
        )

        stats_dict = stats.model_dump()
        assert "count" in stats_dict
        assert "mean" in stats_dict
        assert stats_dict["count"] == 10
