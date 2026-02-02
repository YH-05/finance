"""Unit tests for analyze.technical.indicators module.

テスト対象: analyze.technical.indicators.TechnicalIndicators

TDD Red フェーズ: テスト対象のモジュールはまだ存在しないため、
全テストは ImportError で失敗する状態です。

テスト TODO リスト:
====================

SMA (単純移動平均):
  - [x] test_正常系_有効なデータでSMA計算成功
  - [x] test_正常系_window1でSMA計算成功
  - [x] test_異常系_windowが0以下でValueError
  - [x] test_エッジケース_空のSeriesで空結果

EMA (指数移動平均):
  - [x] test_正常系_有効なデータでEMA計算成功
  - [x] test_正常系_EMAはSMAより直近に重み付け
  - [x] test_異常系_windowが0以下でValueError
  - [x] test_エッジケース_空のSeriesで空結果

Returns (リターン計算):
  - [x] test_正常系_有効なデータでリターン計算成功
  - [x] test_正常系_複数期間でリターン計算成功
  - [x] test_正常系_対数リターン計算成功
  - [x] test_異常系_periodsが0以下でValueError
  - [x] test_エッジケース_空のSeriesで空結果

Volatility (ボラティリティ):
  - [x] test_正常系_有効なリターンでボラティリティ計算成功
  - [x] test_正常系_年率換算ボラティリティ計算成功
  - [x] test_異常系_windowが1以下でValueError
  - [x] test_異常系_annualization_factorが0以下でValueError
  - [x] test_エッジケース_空のSeriesで空結果

Bollinger Bands (ボリンジャーバンド):
  - [x] test_正常系_有効なデータでボリンジャーバンド計算成功
  - [x] test_正常系_upper_middle_lowerの順序が正しい
  - [x] test_正常系_middleがSMAと等しい
  - [x] test_異常系_windowが1以下でValueError
  - [x] test_異常系_num_stdが0以下でValueError
  - [x] test_エッジケース_空のSeriesで空結果

RSI (Relative Strength Index) - 新規追加:
  - [x] test_正常系_有効なデータでRSI計算成功
  - [x] test_正常系_RSIは0から100の範囲
  - [x] test_正常系_上昇トレンドでRSIは50以上
  - [x] test_正常系_下降トレンドでRSIは50以下
  - [x] test_異常系_periodが1未満でValueError
  - [x] test_エッジケース_空のSeriesで空結果

MACD (Moving Average Convergence Divergence) - 新規追加:
  - [x] test_正常系_有効なデータでMACD計算成功
  - [x] test_正常系_MACDはmacd_signal_histogramを返す
  - [x] test_異常系_fast_periodがslow_period以上でValueError
  - [x] test_エッジケース_空のSeriesで空結果

calculate_all (一括計算):
  - [x] test_正常系_全指標を一括計算成功
  - [x] test_正常系_カスタムウィンドウで一括計算成功
"""

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: このインポートは実装が存在しないため失敗します (Red フェーズ)
# 実装完了後は以下のインポートが成功するようになります
from analyze.technical.indicators import TechnicalIndicators


class TestCalculateSMA:
    """SMA（単純移動平均）計算のテスト。"""

    def test_正常系_有効なデータでSMA計算成功(self) -> None:
        """有効な価格データで SMA が正しく計算されることを確認。"""
        prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        sma = TechnicalIndicators.calculate_sma(prices, window=3)

        # 最初の (window-1) 個は NaN
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[1])

        # SMA(3) at index 2: (10+11+12)/3 = 11.0
        assert sma.iloc[2] == pytest.approx(11.0)
        # SMA(3) at index 3: (11+12+13)/3 = 12.0
        assert sma.iloc[3] == pytest.approx(12.0)
        # SMA(3) at index 4: (12+13+14)/3 = 13.0
        assert sma.iloc[4] == pytest.approx(13.0)

    def test_正常系_window1でSMA計算成功(self) -> None:
        """window=1 で SMA が元の値と等しいことを確認。"""
        prices = pd.Series([10.0, 20.0, 30.0])
        sma = TechnicalIndicators.calculate_sma(prices, window=1)

        assert sma.iloc[0] == pytest.approx(10.0)
        assert sma.iloc[1] == pytest.approx(20.0)
        assert sma.iloc[2] == pytest.approx(30.0)

    def test_異常系_windowが0以下でValueError(self) -> None:
        """window が 0 以下の場合、ValueError が発生することを確認。"""
        prices = pd.Series([10.0, 11.0, 12.0])

        with pytest.raises(ValueError, match="window must be at least 1"):
            TechnicalIndicators.calculate_sma(prices, window=0)

        with pytest.raises(ValueError, match="window must be at least 1"):
            TechnicalIndicators.calculate_sma(prices, window=-1)

    def test_エッジケース_空のSeriesで空結果(self) -> None:
        """空の Series で空の結果が返されることを確認。"""
        prices = pd.Series(dtype=np.float64)
        sma = TechnicalIndicators.calculate_sma(prices, window=3)

        assert len(sma) == 0

    def test_エッジケース_データポイント不足で全NaN(self) -> None:
        """データポイントが window より少ない場合、全て NaN になることを確認。"""
        prices = pd.Series([10.0, 11.0])
        sma = TechnicalIndicators.calculate_sma(prices, window=5)

        assert all(pd.isna(sma))


class TestCalculateEMA:
    """EMA（指数移動平均）計算のテスト。"""

    def test_正常系_有効なデータでEMA計算成功(self) -> None:
        """有効な価格データで EMA が正しく計算されることを確認。"""
        prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        ema = TechnicalIndicators.calculate_ema(prices, window=3)

        # 最初の (window-1) 個は NaN
        assert pd.isna(ema.iloc[0])
        assert pd.isna(ema.iloc[1])

        # EMA は index 2 以降で計算される
        assert pd.notna(ema.iloc[2])
        assert pd.notna(ema.iloc[3])
        assert pd.notna(ema.iloc[4])

    def test_正常系_EMAはSMAより直近に重み付け(self) -> None:
        """EMA が SMA より直近の価格に重み付けされることを確認。"""
        # 急激な価格上昇
        prices = pd.Series([10.0, 10.0, 10.0, 10.0, 20.0])

        sma = TechnicalIndicators.calculate_sma(prices, window=3)
        ema = TechnicalIndicators.calculate_ema(prices, window=3)

        # EMA は急激な変化により早く反応するため、SMA より大きい
        assert ema.iloc[-1] > sma.iloc[-1]

    def test_異常系_windowが0以下でValueError(self) -> None:
        """window が 0 以下の場合、ValueError が発生することを確認。"""
        prices = pd.Series([10.0, 11.0, 12.0])

        with pytest.raises(ValueError, match="window must be at least 1"):
            TechnicalIndicators.calculate_ema(prices, window=0)

    def test_エッジケース_空のSeriesで空結果(self) -> None:
        """空の Series で空の結果が返されることを確認。"""
        prices = pd.Series(dtype=np.float64)
        ema = TechnicalIndicators.calculate_ema(prices, window=3)

        assert len(ema) == 0


class TestCalculateReturns:
    """リターン計算のテスト。"""

    def test_正常系_有効なデータでリターン計算成功(self) -> None:
        """有効な価格データでリターンが正しく計算されることを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0, 105.0])
        returns = TechnicalIndicators.calculate_returns(prices)

        # 最初の値は NaN
        assert pd.isna(returns.iloc[0])

        # Return at index 1: (102-100)/100 = 0.02
        assert returns.iloc[1] == pytest.approx(0.02)
        # Return at index 2: (101-102)/102 = -0.0098
        assert returns.iloc[2] == pytest.approx(-0.00980392, rel=1e-4)
        # Return at index 3: (105-101)/101 = 0.0396
        assert returns.iloc[3] == pytest.approx(0.0396039, rel=1e-4)

    def test_正常系_複数期間でリターン計算成功(self) -> None:
        """複数期間でリターンが正しく計算されることを確認。"""
        prices = pd.Series([100.0, 102.0, 104.0, 106.0])
        returns = TechnicalIndicators.calculate_returns(prices, periods=2)

        # 最初の 2 値は NaN
        assert pd.isna(returns.iloc[0])
        assert pd.isna(returns.iloc[1])

        # Return at index 2: (104-100)/100 = 0.04
        assert returns.iloc[2] == pytest.approx(0.04)

    def test_正常系_対数リターン計算成功(self) -> None:
        """対数リターンが正しく計算されることを確認。"""
        prices = pd.Series([100.0, 110.0, 100.0])
        returns = TechnicalIndicators.calculate_returns(prices, log_returns=True)

        # 最初の値は NaN
        assert pd.isna(returns.iloc[0])

        # Log return at index 1: ln(110/100) = 0.0953
        assert returns.iloc[1] == pytest.approx(np.log(1.1), rel=1e-4)

    def test_異常系_periodsが0以下でValueError(self) -> None:
        """periods が 0 以下の場合、ValueError が発生することを確認。"""
        prices = pd.Series([100.0, 102.0])

        with pytest.raises(ValueError, match="periods must be at least 1"):
            TechnicalIndicators.calculate_returns(prices, periods=0)

    def test_エッジケース_空のSeriesで空結果(self) -> None:
        """空の Series で空の結果が返されることを確認。"""
        prices = pd.Series(dtype=np.float64)
        returns = TechnicalIndicators.calculate_returns(prices)

        assert len(returns) == 0


class TestCalculateVolatility:
    """ボラティリティ計算のテスト。"""

    def test_正常系_有効なリターンでボラティリティ計算成功(self) -> None:
        """有効なリターンデータでボラティリティが計算されることを確認。"""
        returns = pd.Series([0.01, -0.01, 0.02, -0.02, 0.01, -0.01, 0.02])
        vol = TechnicalIndicators.calculate_volatility(
            returns, window=3, annualize=False
        )

        # 最初の (window-1) 個は NaN
        assert pd.isna(vol.iloc[0])
        assert pd.isna(vol.iloc[1])

        # ボラティリティは index 2 以降で計算される
        assert pd.notna(vol.iloc[2])

    def test_正常系_年率換算ボラティリティ計算成功(self) -> None:
        """年率換算ボラティリティが正しく計算されることを確認。"""
        returns = pd.Series([0.01, -0.01, 0.02, -0.02, 0.01])
        vol_daily = TechnicalIndicators.calculate_volatility(
            returns, window=3, annualize=False
        )
        vol_annualized = TechnicalIndicators.calculate_volatility(
            returns, window=3, annualize=True, annualization_factor=252
        )

        # 年率換算ボラティリティ = 日次ボラティリティ * sqrt(252)
        for i in range(len(vol_annualized)):
            if pd.notna(vol_annualized.iloc[i]):
                expected = vol_daily.iloc[i] * np.sqrt(252)
                assert vol_annualized.iloc[i] == pytest.approx(expected, rel=1e-6)

    def test_異常系_windowが1以下でValueError(self) -> None:
        """window が 1 以下の場合、ValueError が発生することを確認。"""
        returns = pd.Series([0.01, -0.01, 0.02])

        with pytest.raises(ValueError, match="window must be at least 2"):
            TechnicalIndicators.calculate_volatility(returns, window=1)

    def test_異常系_annualization_factorが0以下でValueError(self) -> None:
        """annualization_factor が 0 以下の場合、ValueError が発生することを確認。"""
        returns = pd.Series([0.01, -0.01, 0.02])

        with pytest.raises(ValueError, match="annualization_factor must be at least 1"):
            TechnicalIndicators.calculate_volatility(
                returns, window=2, annualization_factor=0
            )

    def test_エッジケース_空のSeriesで空結果(self) -> None:
        """空の Series で空の結果が返されることを確認。"""
        returns = pd.Series(dtype=np.float64)
        vol = TechnicalIndicators.calculate_volatility(returns, window=3)

        assert len(vol) == 0


class TestCalculateBollingerBands:
    """ボリンジャーバンド計算のテスト。"""

    def test_正常系_有効なデータでボリンジャーバンド計算成功(self) -> None:
        """有効な価格データでボリンジャーバンドが計算されることを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0, 106.0])
        bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5)

        # 3 つのバンドが返される
        assert "upper" in bands
        assert "middle" in bands
        assert "lower" in bands

        # 最初の (window-1) 個は NaN
        assert pd.isna(bands["middle"].iloc[0])
        assert pd.isna(bands["middle"].iloc[3])

        # 有効な値は index 4 以降
        assert pd.notna(bands["middle"].iloc[4])
        assert pd.notna(bands["upper"].iloc[4])
        assert pd.notna(bands["lower"].iloc[4])

    def test_正常系_upper_middle_lowerの順序が正しい(self) -> None:
        """upper > middle > lower の順序が保たれていることを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0, 106.0])
        bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5)

        for i in range(4, len(prices)):
            assert bands["upper"].iloc[i] > bands["middle"].iloc[i]
            assert bands["middle"].iloc[i] > bands["lower"].iloc[i]

    def test_正常系_middleがSMAと等しい(self) -> None:
        """middle バンドが SMA と等しいことを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0, 106.0])
        bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5)
        sma = TechnicalIndicators.calculate_sma(prices, window=5)

        for i in range(len(prices)):
            if pd.notna(bands["middle"].iloc[i]):
                assert bands["middle"].iloc[i] == pytest.approx(sma.iloc[i])

    def test_異常系_windowが1以下でValueError(self) -> None:
        """window が 1 以下の場合、ValueError が発生することを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0])

        with pytest.raises(ValueError, match="window must be at least 2"):
            TechnicalIndicators.calculate_bollinger_bands(prices, window=1)

    def test_異常系_num_stdが0以下でValueError(self) -> None:
        """num_std が 0 以下の場合、ValueError が発生することを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0])

        with pytest.raises(ValueError, match="num_std must be positive"):
            TechnicalIndicators.calculate_bollinger_bands(prices, window=2, num_std=0)

        with pytest.raises(ValueError, match="num_std must be positive"):
            TechnicalIndicators.calculate_bollinger_bands(prices, window=2, num_std=-1)

    def test_エッジケース_空のSeriesで空結果(self) -> None:
        """空の Series で空の結果が返されることを確認。"""
        prices = pd.Series(dtype=np.float64)
        bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5)

        assert len(bands["upper"]) == 0
        assert len(bands["middle"]) == 0
        assert len(bands["lower"]) == 0

    def test_エッジケース_一定価格でバンド幅0(self) -> None:
        """一定の価格で全バンドが同じ値になることを確認。"""
        prices = pd.Series([100.0] * 10)
        bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5)

        # 標準偏差が 0 なので、全バンドが同じ値
        for i in range(4, len(prices)):
            assert bands["upper"].iloc[i] == pytest.approx(100.0)
            assert bands["middle"].iloc[i] == pytest.approx(100.0)
            assert bands["lower"].iloc[i] == pytest.approx(100.0)


class TestCalculateRSI:
    """RSI（Relative Strength Index）計算のテスト。

    RSI は 0-100 の範囲で推移し、70 以上で買われ過ぎ、30 以下で売られ過ぎを示す。
    """

    def test_正常系_有効なデータでRSI計算成功(self) -> None:
        """有効な価格データで RSI が計算されることを確認。"""
        prices = pd.Series([44.0, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42])
        rsi = TechnicalIndicators.calculate_rsi(prices, period=6)

        # 最初の period 個は NaN
        for i in range(6):
            assert pd.isna(rsi.iloc[i])

        # RSI は index 6 以降で計算される
        assert pd.notna(rsi.iloc[6])
        assert pd.notna(rsi.iloc[7])

    def test_正常系_RSIは0から100の範囲(self) -> None:
        """RSI が 0 から 100 の範囲であることを確認。"""
        prices = pd.Series([100.0, 102.0, 98.0, 103.0, 97.0, 105.0, 95.0, 108.0])
        rsi = TechnicalIndicators.calculate_rsi(prices, period=5)

        for i in range(len(rsi)):
            if pd.notna(rsi.iloc[i]):
                assert 0 <= rsi.iloc[i] <= 100

    def test_正常系_上昇トレンドでRSIは50以上(self) -> None:
        """上昇トレンドで RSI が 50 以上になることを確認。"""
        # 連続して上昇する価格
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0])
        rsi = TechnicalIndicators.calculate_rsi(prices, period=5)

        # 最後の値は 100 に近い（全て上昇なので）
        last_valid_rsi = rsi.dropna().iloc[-1]
        assert last_valid_rsi >= 50

    def test_正常系_下降トレンドでRSIは50以下(self) -> None:
        """下降トレンドで RSI が 50 以下になることを確認。"""
        # 連続して下降する価格
        prices = pd.Series([107.0, 106.0, 105.0, 104.0, 103.0, 102.0, 101.0, 100.0])
        rsi = TechnicalIndicators.calculate_rsi(prices, period=5)

        # 最後の値は 0 に近い（全て下降なので）
        last_valid_rsi = rsi.dropna().iloc[-1]
        assert last_valid_rsi <= 50

    def test_異常系_periodが1未満でValueError(self) -> None:
        """period が 1 未満の場合、ValueError が発生することを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0])

        with pytest.raises(ValueError, match="period must be at least 1"):
            TechnicalIndicators.calculate_rsi(prices, period=0)

    def test_エッジケース_空のSeriesで空結果(self) -> None:
        """空の Series で空の結果が返されることを確認。"""
        prices = pd.Series(dtype=np.float64)
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)

        assert len(rsi) == 0


class TestCalculateMACD:
    """MACD（Moving Average Convergence Divergence）計算のテスト。

    MACD は短期 EMA - 長期 EMA で計算され、シグナル線との乖離で売買シグナルを判断。
    """

    def test_正常系_有効なデータでMACD計算成功(self) -> None:
        """有効な価格データで MACD が計算されることを確認。"""
        # 十分なデータポイント（26 + 9 = 35 以上推奨）
        prices = pd.Series([100.0 + i * 0.5 for i in range(40)])
        macd = TechnicalIndicators.calculate_macd(
            prices, fast_period=12, slow_period=26, signal_period=9
        )

        # 3 つの値が返される
        assert "macd" in macd
        assert "signal" in macd
        assert "histogram" in macd

        # MACD は slow_period 以降で計算開始
        assert pd.notna(macd["macd"].iloc[26])

    def test_正常系_MACDはmacd_signal_histogramを返す(self) -> None:
        """MACD、シグナル線、ヒストグラムが正しく計算されることを確認。"""
        prices = pd.Series([100.0 + i * 0.5 for i in range(40)])
        macd = TechnicalIndicators.calculate_macd(
            prices, fast_period=12, slow_period=26, signal_period=9
        )

        # ヒストグラムは MACD - シグナル
        for i in range(len(macd["histogram"])):
            if pd.notna(macd["histogram"].iloc[i]):
                expected = macd["macd"].iloc[i] - macd["signal"].iloc[i]
                assert macd["histogram"].iloc[i] == pytest.approx(expected, rel=1e-6)

    def test_異常系_fast_periodがslow_period以上でValueError(self) -> None:
        """fast_period が slow_period 以上の場合、ValueError が発生することを確認。"""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0])

        with pytest.raises(
            ValueError, match="fast_period must be less than slow_period"
        ):
            TechnicalIndicators.calculate_macd(
                prices, fast_period=26, slow_period=12, signal_period=9
            )

        with pytest.raises(
            ValueError, match="fast_period must be less than slow_period"
        ):
            TechnicalIndicators.calculate_macd(
                prices, fast_period=12, slow_period=12, signal_period=9
            )

    def test_エッジケース_空のSeriesで空結果(self) -> None:
        """空の Series で空の結果が返されることを確認。"""
        prices = pd.Series(dtype=np.float64)
        macd = TechnicalIndicators.calculate_macd(prices)

        assert len(macd["macd"]) == 0
        assert len(macd["signal"]) == 0
        assert len(macd["histogram"]) == 0


class TestCalculateAll:
    """calculate_all（一括計算）のテスト。"""

    def test_正常系_全指標を一括計算成功(self) -> None:
        """全ての指標が一括で計算されることを確認。"""
        prices = pd.Series([100.0 + i for i in range(250)])
        result = TechnicalIndicators.calculate_all(prices)

        # 基本指標が含まれる
        assert "returns" in result
        assert "sma_20" in result
        assert "sma_50" in result
        assert "sma_200" in result
        assert "ema_12" in result
        assert "ema_26" in result
        assert "volatility" in result
        # 新規追加指標
        assert "rsi" in result
        assert "macd" in result
        assert "macd_signal" in result
        assert "macd_histogram" in result

    def test_正常系_カスタムウィンドウで一括計算成功(self) -> None:
        """カスタムウィンドウで指標が計算されることを確認。"""
        prices = pd.Series([100.0 + i for i in range(50)])
        result = TechnicalIndicators.calculate_all(
            prices,
            sma_windows=[5, 10],
            ema_windows=[8],
        )

        assert "sma_5" in result
        assert "sma_10" in result
        assert "ema_8" in result

        # デフォルトのウィンドウは含まれない
        assert "sma_20" not in result
        assert "ema_12" not in result


class TestEdgeCases:
    """エッジケースと境界条件のテスト。"""

    def test_NaN値を含む入力の処理(self) -> None:
        """入力に NaN が含まれる場合の処理を確認。"""
        prices = pd.Series([100.0, np.nan, 102.0, 103.0, 104.0])

        sma = TechnicalIndicators.calculate_sma(prices, window=2)
        returns = TechnicalIndicators.calculate_returns(prices)

        # NaN は適切に伝播する
        assert pd.isna(sma.iloc[1])  # 入力の NaN
        assert pd.isna(sma.iloc[2])  # NaN の影響を受ける
        assert pd.isna(returns.iloc[2])  # NaN を含む計算

    def test_単一値のSeries(self) -> None:
        """単一値の Series での処理を確認。"""
        prices = pd.Series([100.0])

        sma = TechnicalIndicators.calculate_sma(prices, window=1)
        assert sma.iloc[0] == pytest.approx(100.0)

        returns = TechnicalIndicators.calculate_returns(prices)
        assert pd.isna(returns.iloc[0])

    def test_一定価格での変動なし(self) -> None:
        """一定価格（変動なし）での処理を確認。"""
        prices = pd.Series([100.0] * 10)

        returns = TechnicalIndicators.calculate_returns(prices)
        vol = TechnicalIndicators.calculate_volatility(
            returns, window=5, annualize=False
        )

        # リターンは 0（最初の NaN を除く）
        assert all(returns.iloc[1:] == 0)

        # ボラティリティは 0
        valid_vol = vol.dropna()
        assert np.allclose(valid_vol.to_numpy(), 0.0, atol=1e-10)

    def test_windowとデータ長が等しい場合(self) -> None:
        """window がデータ長と等しい場合の処理を確認。"""
        prices = pd.Series([10.0, 20.0, 30.0])

        sma = TechnicalIndicators.calculate_sma(prices, window=3)

        # 最後の値のみ有効
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[1])
        assert sma.iloc[2] == pytest.approx(20.0)  # (10+20+30)/3
