"""Unit tests for IndicatorCalculator class."""

import numpy as np
import pandas as pd
import pytest

from market_analysis.analysis.indicators import IndicatorCalculator


class TestCalculateSMA:
    """Tests for SMA calculation."""

    def test_sma_basic(self) -> None:
        """Test basic SMA calculation."""
        prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        sma = IndicatorCalculator.calculate_sma(prices, window=3)

        # First 2 values should be NaN (window-1)
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[1])

        # SMA(3) at index 2: (10+11+12)/3 = 11.0
        assert sma.iloc[2] == pytest.approx(11.0)
        # SMA(3) at index 3: (11+12+13)/3 = 12.0
        assert sma.iloc[3] == pytest.approx(12.0)
        # SMA(3) at index 4: (12+13+14)/3 = 13.0
        assert sma.iloc[4] == pytest.approx(13.0)

    def test_sma_window_1(self) -> None:
        """Test SMA with window=1 returns original values."""
        prices = pd.Series([10.0, 20.0, 30.0])
        sma = IndicatorCalculator.calculate_sma(prices, window=1)

        assert sma.iloc[0] == pytest.approx(10.0)
        assert sma.iloc[1] == pytest.approx(20.0)
        assert sma.iloc[2] == pytest.approx(30.0)

    def test_sma_insufficient_data(self) -> None:
        """Test SMA returns NaN when window > data length."""
        prices = pd.Series([10.0, 11.0])
        sma = IndicatorCalculator.calculate_sma(prices, window=5)

        assert all(pd.isna(sma))

    def test_sma_empty_series(self) -> None:
        """Test SMA with empty series returns empty series."""
        prices = pd.Series(dtype=np.float64)
        sma = IndicatorCalculator.calculate_sma(prices, window=3)

        assert len(sma) == 0

    def test_sma_invalid_window(self) -> None:
        """Test SMA raises ValueError for invalid window."""
        prices = pd.Series([10.0, 11.0, 12.0])

        with pytest.raises(ValueError, match="Window must be at least 1"):
            IndicatorCalculator.calculate_sma(prices, window=0)

        with pytest.raises(ValueError, match="Window must be at least 1"):
            IndicatorCalculator.calculate_sma(prices, window=-1)


class TestCalculateEMA:
    """Tests for EMA calculation."""

    def test_ema_basic(self) -> None:
        """Test basic EMA calculation."""
        prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        ema = IndicatorCalculator.calculate_ema(prices, window=3)

        # First 2 values should be NaN (min_periods=window)
        assert pd.isna(ema.iloc[0])
        assert pd.isna(ema.iloc[1])

        # EMA should be calculated from index 2 onwards
        assert pd.notna(ema.iloc[2])
        assert pd.notna(ema.iloc[3])
        assert pd.notna(ema.iloc[4])

    def test_ema_gives_more_weight_to_recent(self) -> None:
        """Test that EMA reacts faster than SMA to price changes."""
        # Sharp price increase
        prices = pd.Series([10.0, 10.0, 10.0, 10.0, 20.0])

        sma = IndicatorCalculator.calculate_sma(prices, window=3)
        ema = IndicatorCalculator.calculate_ema(prices, window=3)

        # EMA should be higher than SMA after sharp increase
        # because it gives more weight to recent prices
        assert ema.iloc[-1] > sma.iloc[-1]

    def test_ema_empty_series(self) -> None:
        """Test EMA with empty series returns empty series."""
        prices = pd.Series(dtype=np.float64)
        ema = IndicatorCalculator.calculate_ema(prices, window=3)

        assert len(ema) == 0

    def test_ema_invalid_window(self) -> None:
        """Test EMA raises ValueError for invalid window."""
        prices = pd.Series([10.0, 11.0, 12.0])

        with pytest.raises(ValueError, match="Window must be at least 1"):
            IndicatorCalculator.calculate_ema(prices, window=0)


class TestCalculateReturns:
    """Tests for returns calculation."""

    def test_returns_basic(self) -> None:
        """Test basic returns calculation."""
        prices = pd.Series([100.0, 102.0, 101.0, 105.0])
        returns = IndicatorCalculator.calculate_returns(prices)

        # First value should be NaN
        assert pd.isna(returns.iloc[0])

        # Return at index 1: (102-100)/100 = 0.02
        assert returns.iloc[1] == pytest.approx(0.02)
        # Return at index 2: (101-102)/102 ≈ -0.0098
        assert returns.iloc[2] == pytest.approx(-0.00980392, rel=1e-4)
        # Return at index 3: (105-101)/101 ≈ 0.0396
        assert returns.iloc[3] == pytest.approx(0.0396039, rel=1e-4)

    def test_returns_multiple_periods(self) -> None:
        """Test returns with multiple periods."""
        prices = pd.Series([100.0, 102.0, 104.0, 106.0])
        returns = IndicatorCalculator.calculate_returns(prices, periods=2)

        # First 2 values should be NaN
        assert pd.isna(returns.iloc[0])
        assert pd.isna(returns.iloc[1])

        # Return at index 2: (104-100)/100 = 0.04
        assert returns.iloc[2] == pytest.approx(0.04)
        # Return at index 3: (106-102)/102 ≈ 0.0392
        assert returns.iloc[3] == pytest.approx(0.0392156, rel=1e-4)

    def test_returns_log(self) -> None:
        """Test logarithmic returns calculation."""
        prices = pd.Series([100.0, 110.0, 100.0])
        returns = IndicatorCalculator.calculate_returns(prices, log_returns=True)

        # First value should be NaN
        assert pd.isna(returns.iloc[0])

        # Log return at index 1: ln(110/100) ≈ 0.0953
        assert returns.iloc[1] == pytest.approx(np.log(1.1), rel=1e-4)

    def test_returns_empty_series(self) -> None:
        """Test returns with empty series returns empty series."""
        prices = pd.Series(dtype=np.float64)
        returns = IndicatorCalculator.calculate_returns(prices)

        assert len(returns) == 0

    def test_returns_invalid_periods(self) -> None:
        """Test returns raises ValueError for invalid periods."""
        prices = pd.Series([100.0, 102.0])

        with pytest.raises(ValueError, match="Periods must be at least 1"):
            IndicatorCalculator.calculate_returns(prices, periods=0)


class TestCalculateVolatility:
    """Tests for volatility calculation."""

    def test_volatility_basic(self) -> None:
        """Test basic volatility calculation."""
        # Create returns with known standard deviation
        returns = pd.Series([0.01, -0.01, 0.02, -0.02, 0.01, -0.01, 0.02])
        vol = IndicatorCalculator.calculate_volatility(
            returns, window=3, annualize=False
        )

        # First 2 values should be NaN (window-1)
        assert pd.isna(vol.iloc[0])
        assert pd.isna(vol.iloc[1])

        # Volatility should be calculated from index 2 onwards
        assert pd.notna(vol.iloc[2])

    def test_volatility_annualized(self) -> None:
        """Test annualized volatility calculation."""
        returns = pd.Series([0.01, -0.01, 0.02, -0.02, 0.01])
        vol_not_annualized = IndicatorCalculator.calculate_volatility(
            returns, window=3, annualize=False
        )
        vol_annualized = IndicatorCalculator.calculate_volatility(
            returns, window=3, annualize=True, annualization_factor=252
        )

        # Annualized volatility should be sqrt(252) times the non-annualized
        for i in range(len(vol_annualized)):
            if pd.notna(vol_annualized.iloc[i]):
                expected = vol_not_annualized.iloc[i] * np.sqrt(252)
                assert vol_annualized.iloc[i] == pytest.approx(expected, rel=1e-6)

    def test_volatility_custom_factor(self) -> None:
        """Test volatility with custom annualization factor."""
        returns = pd.Series([0.01, -0.01, 0.02, -0.02, 0.01])
        vol_daily = IndicatorCalculator.calculate_volatility(
            returns, window=3, annualize=True, annualization_factor=252
        )
        vol_weekly = IndicatorCalculator.calculate_volatility(
            returns, window=3, annualize=True, annualization_factor=52
        )

        # Daily annualized should be higher than weekly annualized
        # because sqrt(252) > sqrt(52)
        for i in range(len(vol_daily)):
            if pd.notna(vol_daily.iloc[i]):
                assert vol_daily.iloc[i] > vol_weekly.iloc[i]

    def test_volatility_empty_series(self) -> None:
        """Test volatility with empty series returns empty series."""
        returns = pd.Series(dtype=np.float64)
        vol = IndicatorCalculator.calculate_volatility(returns, window=3)

        assert len(vol) == 0

    def test_volatility_invalid_window(self) -> None:
        """Test volatility raises ValueError for invalid window."""
        returns = pd.Series([0.01, -0.01, 0.02])

        with pytest.raises(ValueError, match="Window must be at least 2"):
            IndicatorCalculator.calculate_volatility(returns, window=1)

    def test_volatility_invalid_annualization_factor(self) -> None:
        """Test volatility raises ValueError for invalid annualization factor."""
        returns = pd.Series([0.01, -0.01, 0.02])

        with pytest.raises(ValueError, match="Annualization factor must be at least 1"):
            IndicatorCalculator.calculate_volatility(
                returns, window=2, annualization_factor=0
            )


class TestCalculateBollingerBands:
    """Tests for Bollinger Bands calculation."""

    def test_bollinger_basic(self) -> None:
        """Test basic Bollinger Bands calculation."""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0, 106.0])
        bands = IndicatorCalculator.calculate_bollinger_bands(prices, window=5)

        # Check that all three bands are returned
        assert "upper" in bands
        assert "middle" in bands
        assert "lower" in bands

        # First 4 values should be NaN (window-1)
        assert pd.isna(bands["middle"].iloc[0])
        assert pd.isna(bands["middle"].iloc[3])

        # Valid values from index 4 onwards
        assert pd.notna(bands["middle"].iloc[4])
        assert pd.notna(bands["upper"].iloc[4])
        assert pd.notna(bands["lower"].iloc[4])

    def test_bollinger_band_order(self) -> None:
        """Test that upper > middle > lower."""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0, 106.0])
        bands = IndicatorCalculator.calculate_bollinger_bands(prices, window=5)

        for i in range(4, len(prices)):
            assert bands["upper"].iloc[i] > bands["middle"].iloc[i]
            assert bands["middle"].iloc[i] > bands["lower"].iloc[i]

    def test_bollinger_middle_equals_sma(self) -> None:
        """Test that middle band equals SMA."""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0, 106.0])
        bands = IndicatorCalculator.calculate_bollinger_bands(prices, window=5)
        sma = IndicatorCalculator.calculate_sma(prices, window=5)

        for i in range(len(prices)):
            if pd.notna(bands["middle"].iloc[i]):
                assert bands["middle"].iloc[i] == pytest.approx(sma.iloc[i])

    def test_bollinger_custom_std(self) -> None:
        """Test Bollinger Bands with custom standard deviation."""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0, 106.0])
        bands_2std = IndicatorCalculator.calculate_bollinger_bands(
            prices, window=5, num_std=2.0
        )
        bands_1std = IndicatorCalculator.calculate_bollinger_bands(
            prices, window=5, num_std=1.0
        )

        # Bands with 2 std should be wider than 1 std
        for i in range(4, len(prices)):
            width_2std = bands_2std["upper"].iloc[i] - bands_2std["lower"].iloc[i]
            width_1std = bands_1std["upper"].iloc[i] - bands_1std["lower"].iloc[i]
            assert width_2std > width_1std

    def test_bollinger_empty_series(self) -> None:
        """Test Bollinger Bands with empty series returns empty series."""
        prices = pd.Series(dtype=np.float64)
        bands = IndicatorCalculator.calculate_bollinger_bands(prices, window=5)

        assert len(bands["upper"]) == 0
        assert len(bands["middle"]) == 0
        assert len(bands["lower"]) == 0

    def test_bollinger_invalid_window(self) -> None:
        """Test Bollinger Bands raises ValueError for invalid window."""
        prices = pd.Series([100.0, 102.0, 101.0])

        with pytest.raises(ValueError, match="Window must be at least 2"):
            IndicatorCalculator.calculate_bollinger_bands(prices, window=1)

    def test_bollinger_invalid_num_std(self) -> None:
        """Test Bollinger Bands raises ValueError for invalid num_std."""
        prices = pd.Series([100.0, 102.0, 101.0])

        with pytest.raises(ValueError, match="num_std must be positive"):
            IndicatorCalculator.calculate_bollinger_bands(prices, window=2, num_std=0)

        with pytest.raises(ValueError, match="num_std must be positive"):
            IndicatorCalculator.calculate_bollinger_bands(prices, window=2, num_std=-1)

    def test_bollinger_constant_prices(self) -> None:
        """Test Bollinger Bands with constant prices."""
        prices = pd.Series([100.0] * 10)
        bands = IndicatorCalculator.calculate_bollinger_bands(prices, window=5)

        # With constant prices, std=0, so upper=middle=lower
        for i in range(4, len(prices)):
            assert bands["upper"].iloc[i] == pytest.approx(100.0)
            assert bands["middle"].iloc[i] == pytest.approx(100.0)
            assert bands["lower"].iloc[i] == pytest.approx(100.0)


class TestCalculateAll:
    """Tests for calculate_all convenience method."""

    def test_calculate_all_default(self) -> None:
        """Test calculate_all with default parameters."""
        prices = pd.Series(
            [100.0 + i for i in range(250)]  # 250 data points
        )
        result = IndicatorCalculator.calculate_all(prices)

        # Check that all expected indicators are present
        assert "returns" in result
        assert "sma_20" in result
        assert "sma_50" in result
        assert "sma_200" in result
        assert "ema_12" in result
        assert "ema_26" in result
        assert "volatility" in result

    def test_calculate_all_custom_windows(self) -> None:
        """Test calculate_all with custom windows."""
        prices = pd.Series([100.0 + i for i in range(50)])
        result = IndicatorCalculator.calculate_all(
            prices,
            sma_windows=[5, 10],
            ema_windows=[8],
        )

        assert "sma_5" in result
        assert "sma_10" in result
        assert "ema_8" in result

        # Default windows should not be present
        assert "sma_20" not in result
        assert "ema_12" not in result

    def test_calculate_all_with_short_data(self) -> None:
        """Test calculate_all with short data series."""
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0])
        result = IndicatorCalculator.calculate_all(
            prices,
            sma_windows=[3],
            ema_windows=[3],
            volatility_window=3,
        )

        # Returns should have 4 valid values (first is NaN)
        assert result["returns"].notna().sum() == 4

        # SMA and EMA should have 3 valid values
        assert result["sma_3"].notna().sum() == 3
        assert result["ema_3"].notna().sum() == 3


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_nan_values_in_input(self) -> None:
        """Test handling of NaN values in input series."""
        prices = pd.Series([100.0, np.nan, 102.0, 103.0, 104.0])

        sma = IndicatorCalculator.calculate_sma(prices, window=2)
        returns = IndicatorCalculator.calculate_returns(prices)

        # NaN should propagate appropriately
        assert pd.isna(sma.iloc[1])  # NaN in input
        assert pd.isna(sma.iloc[2])  # Affected by NaN
        assert pd.isna(returns.iloc[2])  # Division involving NaN

    def test_single_value_series(self) -> None:
        """Test with single-value series."""
        prices = pd.Series([100.0])

        sma = IndicatorCalculator.calculate_sma(prices, window=1)
        assert sma.iloc[0] == pytest.approx(100.0)

        returns = IndicatorCalculator.calculate_returns(prices)
        assert pd.isna(returns.iloc[0])

    def test_constant_prices(self) -> None:
        """Test with constant prices (no variation)."""
        prices = pd.Series([100.0] * 10)

        returns = IndicatorCalculator.calculate_returns(prices)
        vol = IndicatorCalculator.calculate_volatility(
            returns, window=5, annualize=False
        )

        # Returns should be 0 (except first NaN)
        assert all(returns.iloc[1:] == 0)

        # Volatility should be 0 (constant prices have no volatility)
        # Note: First return is NaN, so volatility window starts from index 1
        # With window=5, valid values start from index 5 (1 + 5 - 1)
        valid_vol = vol.dropna()
        assert np.allclose(valid_vol.to_numpy(), 0.0, atol=1e-10)

    def test_large_window_relative_to_data(self) -> None:
        """Test with window size equal to data length."""
        prices = pd.Series([10.0, 20.0, 30.0])

        sma = IndicatorCalculator.calculate_sma(prices, window=3)

        # Only last value should be valid
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[1])
        assert sma.iloc[2] == pytest.approx(20.0)  # (10+20+30)/3
