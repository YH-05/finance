"""Unit tests for strategy.types module.

Tests for type definitions:
- AssetClass type alias
- PresetPeriod type alias
- Holding dataclass
- TickerInfo dataclass
- Period dataclass
"""

from datetime import date
from typing import get_args

import pytest
from strategy.types import (
    AssetClass,
    Holding,
    Period,
    PresetPeriod,
    TickerInfo,
)


class TestHolding:
    """Holding dataclass のテスト."""

    # =========================================================================
    # 正常系テスト
    # =========================================================================

    def test_正常系_有効なティッカーと比率で初期化される(self) -> None:
        """有効なティッカーと比率でHoldingが作成されることを確認."""
        holding = Holding(ticker="VOO", weight=0.5)

        assert holding.ticker == "VOO"
        assert holding.weight == 0.5

    def test_正常系_weight_0で初期化できる(self) -> None:
        """weight=0.0でHoldingが作成できることを確認（下限境界値）."""
        holding = Holding(ticker="BND", weight=0.0)

        assert holding.ticker == "BND"
        assert holding.weight == 0.0

    def test_正常系_weight_1で初期化できる(self) -> None:
        """weight=1.0でHoldingが作成できることを確認（上限境界値）."""
        holding = Holding(ticker="GLD", weight=1.0)

        assert holding.ticker == "GLD"
        assert holding.weight == 1.0

    def test_正常系_frozenでイミュータブル(self) -> None:
        """Holdingがイミュータブル（frozen）であることを確認."""
        holding = Holding(ticker="VTI", weight=0.3)

        with pytest.raises(AttributeError):
            holding.ticker = "SPY"

        with pytest.raises(AttributeError):
            holding.weight = 0.5

    # =========================================================================
    # 異常系テスト
    # =========================================================================

    def test_異常系_空文字列のティッカーでValueError(self) -> None:
        """空文字列のティッカーでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match="ticker must be non-empty string"):
            Holding(ticker="", weight=0.5)

    def test_異常系_空白のみのティッカーでValueError(self) -> None:
        """空白のみのティッカーでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match="ticker must be non-empty string"):
            Holding(ticker="   ", weight=0.5)

    def test_異常系_weight_負の値でValueError(self) -> None:
        """負の値のweightでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match=r"weight must be between 0\.0 and 1\.0"):
            Holding(ticker="VOO", weight=-0.1)

    def test_異常系_weight_1超でValueError(self) -> None:
        """1.0を超えるweightでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match=r"weight must be between 0\.0 and 1\.0"):
            Holding(ticker="VOO", weight=1.1)

    def test_異常系_weight_大きな負の値でValueError(self) -> None:
        """大きな負の値のweightでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match=r"weight must be between 0\.0 and 1\.0"):
            Holding(ticker="VOO", weight=-100.0)

    def test_異常系_weight_大きな正の値でValueError(self) -> None:
        """大きな正の値のweightでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match=r"weight must be between 0\.0 and 1\.0"):
            Holding(ticker="VOO", weight=100.0)

    # =========================================================================
    # 境界値テスト
    # =========================================================================

    @pytest.mark.parametrize(
        "weight",
        [
            0.0,
            0.0001,
            0.5,
            0.9999,
            1.0,
        ],
    )
    def test_境界値_有効なweight範囲(self, weight: float) -> None:
        """0.0から1.0の範囲内のweightが受け入れられることを確認."""
        holding = Holding(ticker="TEST", weight=weight)
        assert holding.weight == weight

    @pytest.mark.parametrize(
        "weight",
        [
            -0.0001,
            1.0001,
        ],
    )
    def test_境界値_無効なweight範囲(self, weight: float) -> None:
        """0.0から1.0の範囲外のweightが拒否されることを確認."""
        with pytest.raises(ValueError, match=r"weight must be between 0\.0 and 1\.0"):
            Holding(ticker="TEST", weight=weight)


class TestTickerInfo:
    """TickerInfo dataclass のテスト."""

    # =========================================================================
    # 正常系テスト
    # =========================================================================

    def test_正常系_必須フィールドのみで初期化される(self) -> None:
        """必須フィールドのみでTickerInfoが作成されることを確認."""
        info = TickerInfo(ticker="VOO", name="Vanguard S&P 500 ETF")

        assert info.ticker == "VOO"
        assert info.name == "Vanguard S&P 500 ETF"
        assert info.sector is None
        assert info.industry is None
        assert info.asset_class == "equity"

    def test_正常系_全フィールドで初期化される(self) -> None:
        """全フィールドを指定してTickerInfoが作成されることを確認."""
        info = TickerInfo(
            ticker="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            asset_class="equity",
        )

        assert info.ticker == "AAPL"
        assert info.name == "Apple Inc."
        assert info.sector == "Technology"
        assert info.industry == "Consumer Electronics"
        assert info.asset_class == "equity"

    def test_正常系_債券の資産クラス(self) -> None:
        """asset_class='bond'でTickerInfoが作成されることを確認."""
        info = TickerInfo(
            ticker="BND",
            name="Vanguard Total Bond Market ETF",
            asset_class="bond",
        )

        assert info.asset_class == "bond"

    def test_正常系_コモディティの資産クラス(self) -> None:
        """asset_class='commodity'でTickerInfoが作成されることを確認."""
        info = TickerInfo(
            ticker="GLD",
            name="SPDR Gold Shares",
            asset_class="commodity",
        )

        assert info.asset_class == "commodity"

    def test_正常系_不動産の資産クラス(self) -> None:
        """asset_class='real_estate'でTickerInfoが作成されることを確認."""
        info = TickerInfo(
            ticker="VNQ",
            name="Vanguard Real Estate ETF",
            asset_class="real_estate",
        )

        assert info.asset_class == "real_estate"

    def test_正常系_現金の資産クラス(self) -> None:
        """asset_class='cash'でTickerInfoが作成されることを確認."""
        info = TickerInfo(
            ticker="CASH",
            name="Cash Equivalent",
            asset_class="cash",
        )

        assert info.asset_class == "cash"

    def test_正常系_その他の資産クラス(self) -> None:
        """asset_class='other'でTickerInfoが作成されることを確認."""
        info = TickerInfo(
            ticker="OTHER",
            name="Other Asset",
            asset_class="other",
        )

        assert info.asset_class == "other"

    def test_正常系_frozenでイミュータブル(self) -> None:
        """TickerInfoがイミュータブル（frozen）であることを確認."""
        info = TickerInfo(ticker="VOO", name="Vanguard S&P 500 ETF")

        with pytest.raises(AttributeError):
            info.ticker = "SPY"

    # =========================================================================
    # パラメトライズテスト
    # =========================================================================

    @pytest.mark.parametrize(
        "asset_class",
        ["equity", "bond", "commodity", "real_estate", "cash", "other"],
    )
    def test_パラメトライズ_全ての資産クラスが有効(
        self, asset_class: AssetClass
    ) -> None:
        """全てのAssetClass値が有効であることを確認."""
        info = TickerInfo(
            ticker="TEST",
            name="Test Asset",
            asset_class=asset_class,
        )
        assert info.asset_class == asset_class


class TestPeriod:
    """Period dataclass のテスト."""

    # =========================================================================
    # 正常系テスト
    # =========================================================================

    def test_正常系_開始日と終了日で初期化される(self) -> None:
        """開始日と終了日でPeriodが作成されることを確認."""
        start = date(2020, 1, 1)
        end = date(2024, 12, 31)

        period = Period(start=start, end=end)

        assert period.start == start
        assert period.end == end
        assert period.preset is None

    def test_正常系_プリセット付きで初期化される(self) -> None:
        """プリセット付きでPeriodが作成されることを確認."""
        start = date(2023, 1, 1)
        end = date(2024, 1, 1)

        period = Period(start=start, end=end, preset="1y")

        assert period.start == start
        assert period.end == end
        assert period.preset == "1y"

    def test_正常系_frozenでイミュータブル(self) -> None:
        """Periodがイミュータブル（frozen）であることを確認."""
        period = Period(start=date(2020, 1, 1), end=date(2024, 12, 31))

        with pytest.raises(AttributeError):
            period.start = date(2021, 1, 1)

    # =========================================================================
    # from_preset クラスメソッドのテスト
    # =========================================================================

    def test_正常系_from_preset_1y(self) -> None:
        """from_preset('1y')で1年前からの期間が作成されることを確認."""
        period = Period.from_preset("1y")
        today = date.today()

        assert period.end == today
        assert period.preset == "1y"
        # 1年前（おおよそ365日前）
        expected_start = date(today.year - 1, today.month, today.day)
        assert period.start == expected_start

    def test_正常系_from_preset_3y(self) -> None:
        """from_preset('3y')で3年前からの期間が作成されることを確認."""
        period = Period.from_preset("3y")
        today = date.today()

        assert period.end == today
        assert period.preset == "3y"
        expected_start = date(today.year - 3, today.month, today.day)
        assert period.start == expected_start

    def test_正常系_from_preset_5y(self) -> None:
        """from_preset('5y')で5年前からの期間が作成されることを確認."""
        period = Period.from_preset("5y")
        today = date.today()

        assert period.end == today
        assert period.preset == "5y"
        expected_start = date(today.year - 5, today.month, today.day)
        assert period.start == expected_start

    def test_正常系_from_preset_10y(self) -> None:
        """from_preset('10y')で10年前からの期間が作成されることを確認."""
        period = Period.from_preset("10y")
        today = date.today()

        assert period.end == today
        assert period.preset == "10y"
        expected_start = date(today.year - 10, today.month, today.day)
        assert period.start == expected_start

    def test_正常系_from_preset_ytd(self) -> None:
        """from_preset('ytd')で今年の1月1日からの期間が作成されることを確認."""
        period = Period.from_preset("ytd")
        today = date.today()

        assert period.end == today
        assert period.preset == "ytd"
        assert period.start == date(today.year, 1, 1)

    def test_正常系_from_preset_max(self) -> None:
        """from_preset('max')で可能な限り過去からの期間が作成されることを確認."""
        period = Period.from_preset("max")
        today = date.today()

        assert period.end == today
        assert period.preset == "max"
        # max は30年前から今日まで（仕様に基づく）
        expected_start = date(today.year - 30, today.month, today.day)
        assert period.start == expected_start

    # =========================================================================
    # パラメトライズテスト
    # =========================================================================

    @pytest.mark.parametrize(
        "preset",
        ["1y", "3y", "5y", "10y", "ytd", "max"],
    )
    def test_パラメトライズ_全てのプリセットが有効(self, preset: PresetPeriod) -> None:
        """全てのPresetPeriod値がfrom_presetで使用できることを確認."""
        period = Period.from_preset(preset)

        assert period.preset == preset
        assert period.end == date.today()
        assert period.start < period.end


class TestAssetClassTypeAlias:
    """AssetClass 型エイリアスのテスト."""

    def test_正常系_全ての有効な値(self) -> None:
        """AssetClassの全ての有効な値を確認."""
        # Literal型のget_argsで有効な値を取得
        valid_values = get_args(AssetClass)
        expected = {"equity", "bond", "commodity", "real_estate", "cash", "other"}

        assert set(valid_values) == expected

    def test_正常系_値の数(self) -> None:
        """AssetClassが6つの値を持つことを確認."""
        valid_values = get_args(AssetClass)
        assert len(valid_values) == 6


class TestPresetPeriodTypeAlias:
    """PresetPeriod 型エイリアスのテスト."""

    def test_正常系_全ての有効な値(self) -> None:
        """PresetPeriodの全ての有効な値を確認."""
        valid_values = get_args(PresetPeriod)
        expected = {"1y", "3y", "5y", "10y", "ytd", "max"}

        assert set(valid_values) == expected

    def test_正常系_値の数(self) -> None:
        """PresetPeriodが6つの値を持つことを確認."""
        valid_values = get_args(PresetPeriod)
        assert len(valid_values) == 6
