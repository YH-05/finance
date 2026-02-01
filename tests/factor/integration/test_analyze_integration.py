"""Tests for analyze package integration with factor package.

This module tests the integration between analyze package's technical
analysis functions and factor calculations.
"""

import numpy as np
import pandas as pd
import pytest
from factor.integration.analyze_integration import (
    EnhancedFactorAnalyzer,
    calculate_factor_with_indicators,
    create_enhanced_analyzer,
)


class TestEnhancedFactorAnalyzer:
    """Tests for EnhancedFactorAnalyzer class."""

    @pytest.fixture
    def sample_price_data(self) -> pd.DataFrame:
        """Create sample price data for testing."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        # Create realistic price data with trend
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        return pd.DataFrame(
            {
                "close": prices,
                "open": prices - 0.5,
                "high": prices + 1,
                "low": prices - 1,
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=pd.DatetimeIndex(dates, name="Date"),
        )

    def test_正常系_テクニカル指標を計算できる(
        self, sample_price_data: pd.DataFrame
    ) -> None:
        """EnhancedFactorAnalyzer がテクニカル指標を計算できることを確認。"""
        analyzer = EnhancedFactorAnalyzer()
        result = analyzer.compute_indicators(sample_price_data)

        assert isinstance(result, dict)
        assert "returns" in result
        assert "sma_20" in result or "volatility" in result

    def test_正常系_RSIを計算できる(self, sample_price_data: pd.DataFrame) -> None:
        """RSI が計算できることを確認。"""
        analyzer = EnhancedFactorAnalyzer()
        prices: pd.Series = sample_price_data["close"]  # type: ignore[assignment]
        result = analyzer.compute_rsi(prices)

        assert isinstance(result, pd.Series)
        # RSI は 0-100 の範囲
        valid_values = result.dropna()
        if len(valid_values) > 0:
            assert valid_values.min() >= 0
            assert valid_values.max() <= 100

    def test_正常系_相関を計算できる(self, sample_price_data: pd.DataFrame) -> None:
        """相関計算ができることを確認。"""
        analyzer = EnhancedFactorAnalyzer()

        # 2つのシリーズを準備
        series_a: pd.Series = sample_price_data["close"]  # type: ignore[assignment]
        series_b: pd.Series = series_a * 1.1 + np.random.randn(100) * 0.1

        result = analyzer.compute_correlation(series_a, series_b)

        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0

    def test_正常系_ボラティリティを計算できる(
        self, sample_price_data: pd.DataFrame
    ) -> None:
        """ボラティリティが計算できることを確認。"""
        analyzer = EnhancedFactorAnalyzer()
        prices: pd.Series = sample_price_data["close"]  # type: ignore[assignment]
        result = analyzer.compute_volatility(
            prices,
            window=20,
        )

        assert isinstance(result, pd.Series)
        # ボラティリティは非負
        valid_values = result.dropna()
        if len(valid_values) > 0:
            assert valid_values.min() >= 0

    def test_異常系_空のデータでエラーハンドリング(self) -> None:
        """空のデータでも適切にエラーハンドリングされることを確認。"""
        analyzer = EnhancedFactorAnalyzer()
        empty_data = pd.DataFrame()

        result = analyzer.compute_indicators(empty_data)
        assert isinstance(result, dict)
        # 空のデータでも辞書を返す（中身は空でもよい）


class TestCalculateFactorWithIndicators:
    """Tests for calculate_factor_with_indicators function."""

    @pytest.fixture
    def sample_price_data(self) -> pd.DataFrame:
        """Create sample price data for testing."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        prices = 100 + np.cumsum(np.random.randn(50) * 0.5)
        return pd.DataFrame(
            {"close": prices},
            index=pd.DatetimeIndex(dates, name="Date"),
        )

    def test_正常系_ファクター値とテクニカル指標を同時計算できる(
        self, sample_price_data: pd.DataFrame
    ) -> None:
        """ファクター値とテクニカル指標を同時に計算できることを確認。"""
        prices: pd.Series = sample_price_data["close"]  # type: ignore[assignment]
        result = calculate_factor_with_indicators(
            prices=prices,
            factor_window=20,
            include_rsi=True,
            include_volatility=True,
        )

        assert isinstance(result, dict)
        # ファクター値（モメンタム等）が含まれる
        assert "factor_value" in result or "momentum" in result


class TestCreateEnhancedAnalyzer:
    """Tests for create_enhanced_analyzer factory function."""

    def test_正常系_ファクトリ関数でアナライザを作成できる(self) -> None:
        """create_enhanced_analyzer でインスタンスを作成できることを確認。"""
        analyzer = create_enhanced_analyzer()

        assert isinstance(analyzer, EnhancedFactorAnalyzer)
