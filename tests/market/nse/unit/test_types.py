"""Unit tests for market.nse.types module.

Tests verify all type definitions for the NSE data retrieval module,
including Enum types (NseIndex), frozen dataclasses (NseConfig),
data record dataclasses (StockQuote, IndexConstituent, FinancialResult),
RetryConfig re-export, and module exports.

Test TODO List:
- [x] Module exports: __all__ completeness and importability
- [x] NseIndex Enum: values, str inheritance, member count
- [x] NseConfig: frozen, defaults from constants, field types
- [x] NseConfig: timeout/polite_delay/delay_jitter/cookie_refresh_interval range validation
- [x] RetryConfig: re-exported from market.retry
- [x] StockQuote: frozen, all fields, field types
- [x] IndexConstituent: frozen, all fields, field types
- [x] FinancialResult: frozen, all fields, field types
"""

from dataclasses import FrozenInstanceError
from enum import Enum

import pytest

from market.nse.constants import (
    DEFAULT_DELAY_JITTER,
    DEFAULT_POLITE_DELAY,
    DEFAULT_TIMEOUT,
)
from market.nse.types import (
    FinancialResult,
    IndexConstituent,
    NseConfig,
    NseIndex,
    RetryConfig,
    StockQuote,
    __all__,
)

# =============================================================================
# Module exports
# =============================================================================


class TestModuleExports:
    """Test module __all__ exports and structure."""

    def test_正常系_モジュールがインポートできる(self) -> None:
        """types モジュールが正常にインポートできること。"""
        from market.nse import types

        assert types is not None

    def test_正常系_allが定義されている(self) -> None:
        """__all__ がリストとして定義されていること。"""
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_正常系_allの全項目がモジュールに存在する(self) -> None:
        """__all__ の全項目がモジュールの属性として存在すること。"""
        from market.nse import types

        for name in __all__:
            assert hasattr(types, name), f"{name} is not defined in types module"

    def test_正常系_allが8項目を含む(self) -> None:
        """__all__ が全8型定義をエクスポートしていること。"""
        expected = {
            "CorporateEvent",
            "FinancialResult",
            "IndexConstituent",
            "MarketStatus",
            "NseConfig",
            "NseIndex",
            "RetryConfig",
            "StockQuote",
        }
        assert set(__all__) == expected

    def test_正常系_モジュールDocstringが存在する(self) -> None:
        """モジュールの docstring が存在すること。"""
        from market.nse import types

        assert types.__doc__ is not None
        assert len(types.__doc__) > 0


# =============================================================================
# NseIndex Enum
# =============================================================================


class TestNseIndexEnum:
    """NseIndex Enum のテスト。"""

    def test_正常系_str_Enumを継承している(self) -> None:
        """NseIndex が str と Enum を継承していること。"""
        assert issubclass(NseIndex, str)
        assert issubclass(NseIndex, Enum)

    def test_正常系_NIFTY_50の値が正しい(self) -> None:
        """NseIndex.NIFTY_50 の値が 'NIFTY 50' であること。"""
        assert NseIndex.NIFTY_50 == "NIFTY 50"
        assert NseIndex.NIFTY_50.value == "NIFTY 50"

    def test_正常系_NIFTY_BANKの値が正しい(self) -> None:
        """NseIndex.NIFTY_BANK の値が 'NIFTY BANK' であること。"""
        assert NseIndex.NIFTY_BANK == "NIFTY BANK"

    def test_正常系_NIFTY_ITの値が正しい(self) -> None:
        """NseIndex.NIFTY_IT の値が 'NIFTY IT' であること。"""
        assert NseIndex.NIFTY_IT == "NIFTY IT"

    def test_正常系_strとして使用可能(self) -> None:
        """NseIndex メンバーが str として直接使用できること。"""
        index = NseIndex.NIFTY_50
        assert isinstance(index, str)
        assert index == "NIFTY 50"

    def test_正常系_メンバー数が15(self) -> None:
        """NseIndex が15メンバーを持つこと。"""
        assert len(NseIndex) == 15

    def test_正常系_値からメンバーを取得可能(self) -> None:
        """文字列値から NseIndex メンバーを取得できること。"""
        assert NseIndex("NIFTY 50") == NseIndex.NIFTY_50
        assert NseIndex("NIFTY BANK") == NseIndex.NIFTY_BANK

    def test_正常系_repr表示が正しい(self) -> None:
        """NseIndex の repr が正しく表示されること。"""
        assert repr(NseIndex.NIFTY_50) == "<NseIndex.NIFTY_50: 'NIFTY 50'>"

    def test_正常系_主要指数が全て含まれている(self) -> None:
        """主要NSE指数が全て含まれていること。"""
        expected_values = {
            "NIFTY 50",
            "NIFTY BANK",
            "NIFTY IT",
            "NIFTY PHARMA",
            "NIFTY AUTO",
        }
        actual_values = {m.value for m in NseIndex}
        assert expected_values.issubset(actual_values)


# =============================================================================
# NseConfig Dataclass
# =============================================================================


class TestNseConfig:
    """NseConfig frozen dataclass のテスト。"""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """NseConfig がデフォルト値で初期化されること。"""
        config = NseConfig()

        assert config.polite_delay == DEFAULT_POLITE_DELAY
        assert config.delay_jitter == DEFAULT_DELAY_JITTER
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.user_agents == ()
        assert config.cookie_refresh_interval == 300.0

    def test_正常系_カスタム値で初期化できる(self) -> None:
        """NseConfig がカスタム値で初期化されること。"""
        config = NseConfig(
            polite_delay=1.0, timeout=60.0, cookie_refresh_interval=600.0
        )

        assert config.polite_delay == 1.0
        assert config.timeout == 60.0
        assert config.cookie_refresh_interval == 600.0

    def test_正常系_frozenである(self) -> None:
        """NseConfig が frozen dataclass であること。"""
        config = NseConfig()

        with pytest.raises(FrozenInstanceError):
            config.polite_delay = 1.0  # type: ignore[misc]

    def test_正常系_user_agentsのデフォルトが空タプル(self) -> None:
        """user_agents のデフォルトが空タプルであること。"""
        config = NseConfig()

        assert config.user_agents == ()
        assert isinstance(config.user_agents, tuple)

    def test_正常系_user_agentsにカスタム値を設定可能(self) -> None:
        """user_agents にカスタム文字列タプルを設定できること。"""
        agents = ("Mozilla/5.0 Test Agent",)
        config = NseConfig(user_agents=agents)

        assert config.user_agents == agents

    def test_異常系_timeoutが範囲下限未満でValueError(self) -> None:
        """timeout が 1.0 未満のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="timeout"):
            NseConfig(timeout=0.5)

    def test_異常系_timeoutが範囲上限超でValueError(self) -> None:
        """timeout が 300.0 超のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="timeout"):
            NseConfig(timeout=301.0)

    def test_異常系_polite_delayが負数でValueError(self) -> None:
        """polite_delay が負のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="polite_delay"):
            NseConfig(polite_delay=-0.1)

    def test_異常系_polite_delayが上限超でValueError(self) -> None:
        """polite_delay が 60.0 超のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="polite_delay"):
            NseConfig(polite_delay=60.1)

    def test_異常系_delay_jitterが負数でValueError(self) -> None:
        """delay_jitter が負のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="delay_jitter"):
            NseConfig(delay_jitter=-0.1)

    def test_異常系_delay_jitterが上限超でValueError(self) -> None:
        """delay_jitter が 30.0 超のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="delay_jitter"):
            NseConfig(delay_jitter=30.1)

    def test_異常系_cookie_refresh_intervalが下限未満でValueError(self) -> None:
        """cookie_refresh_interval が 10.0 未満のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="cookie_refresh_interval"):
            NseConfig(cookie_refresh_interval=9.9)

    def test_異常系_cookie_refresh_intervalが上限超でValueError(self) -> None:
        """cookie_refresh_interval が 3600.0 超のとき ValueError を送出すること。"""
        with pytest.raises(ValueError, match="cookie_refresh_interval"):
            NseConfig(cookie_refresh_interval=3601.0)

    def test_正常系_エッジケース_timeout境界値が有効(self) -> None:
        """timeout の境界値 (1.0, 300.0) が有効であること。"""
        config_min = NseConfig(timeout=1.0)
        assert config_min.timeout == 1.0

        config_max = NseConfig(timeout=300.0)
        assert config_max.timeout == 300.0

    def test_正常系_エッジケース_polite_delay境界値が有効(self) -> None:
        """polite_delay の境界値 (0.0, 60.0) が有効であること。"""
        config_min = NseConfig(polite_delay=0.0)
        assert config_min.polite_delay == 0.0

        config_max = NseConfig(polite_delay=60.0)
        assert config_max.polite_delay == 60.0

    def test_正常系_エッジケース_cookie_refresh_interval境界値が有効(self) -> None:
        """cookie_refresh_interval の境界値 (10.0, 3600.0) が有効であること。"""
        config_min = NseConfig(cookie_refresh_interval=10.0)
        assert config_min.cookie_refresh_interval == 10.0

        config_max = NseConfig(cookie_refresh_interval=3600.0)
        assert config_max.cookie_refresh_interval == 3600.0


# =============================================================================
# RetryConfig re-export
# =============================================================================


class TestRetryConfigReexport:
    """market.retry.RetryConfig の再エクスポートテスト。"""

    def test_正常系_RetryConfigがmarket_retryから再エクスポートされている(self) -> None:
        """RetryConfig が market.retry から再エクスポートされていること。"""
        from market.retry import RetryConfig as RetryConfigOriginal

        assert RetryConfig is RetryConfigOriginal

    def test_正常系_RetryConfigのデフォルト値が正しい(self) -> None:
        """RetryConfig のデフォルト値が正しいこと。"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_正常系_RetryConfigがfrozenである(self) -> None:
        """RetryConfig が frozen dataclass であること。"""
        config = RetryConfig()

        with pytest.raises(FrozenInstanceError):
            config.max_attempts = 5  # type: ignore[misc]


# =============================================================================
# StockQuote Dataclass
# =============================================================================


class TestStockQuote:
    """StockQuote frozen dataclass のテスト。"""

    def _make_quote(self) -> StockQuote:
        """テスト用 StockQuote を生成する。"""
        return StockQuote(
            symbol="RELIANCE",
            company_name="Reliance Industries Limited",
            series="EQ",
            open="2450.00",
            high="2480.50",
            low="2440.00",
            last_price="2470.25",
            prev_close="2445.00",
            change="25.25",
            pct_change="1.03",
            total_traded_volume="5000000",
            total_traded_value="12345678900.00",
        )

    def test_正常系_全フィールドで初期化できる(self) -> None:
        """StockQuote が全フィールドで初期化されること。"""
        quote = self._make_quote()

        assert quote.symbol == "RELIANCE"
        assert quote.company_name == "Reliance Industries Limited"
        assert quote.series == "EQ"
        assert quote.open == "2450.00"
        assert quote.high == "2480.50"
        assert quote.low == "2440.00"
        assert quote.last_price == "2470.25"
        assert quote.prev_close == "2445.00"
        assert quote.change == "25.25"
        assert quote.pct_change == "1.03"
        assert quote.total_traded_volume == "5000000"
        assert quote.total_traded_value == "12345678900.00"

    def test_正常系_frozenである(self) -> None:
        """StockQuote が frozen dataclass であること。"""
        quote = self._make_quote()

        with pytest.raises(FrozenInstanceError):
            quote.symbol = "TATAMOTORS"  # type: ignore[misc]

    def test_正常系_全フィールドがstr型(self) -> None:
        """StockQuote の全フィールドが str 型であること。"""
        quote = self._make_quote()

        assert isinstance(quote.symbol, str)
        assert isinstance(quote.last_price, str)
        assert isinstance(quote.total_traded_volume, str)


# =============================================================================
# IndexConstituent Dataclass
# =============================================================================


class TestIndexConstituent:
    """IndexConstituent frozen dataclass のテスト。"""

    def _make_constituent(self) -> IndexConstituent:
        """テスト用 IndexConstituent を生成する。"""
        return IndexConstituent(
            symbol="RELIANCE",
            series="EQ",
            open="2450.00",
            day_high="2480.50",
            day_low="2440.00",
            last_price="2470.25",
            prev_close="2445.00",
            change="25.25",
            pct_change="1.03",
            total_traded_volume="5000000",
            total_traded_value="12345678900.00",
            year_high="2900.00",
            year_low="2100.00",
        )

    def test_正常系_全フィールドで初期化できる(self) -> None:
        """IndexConstituent が全フィールドで初期化されること。"""
        constituent = self._make_constituent()

        assert constituent.symbol == "RELIANCE"
        assert constituent.series == "EQ"
        assert constituent.open == "2450.00"
        assert constituent.day_high == "2480.50"
        assert constituent.day_low == "2440.00"
        assert constituent.last_price == "2470.25"
        assert constituent.prev_close == "2445.00"
        assert constituent.change == "25.25"
        assert constituent.pct_change == "1.03"
        assert constituent.total_traded_volume == "5000000"
        assert constituent.total_traded_value == "12345678900.00"
        assert constituent.year_high == "2900.00"
        assert constituent.year_low == "2100.00"

    def test_正常系_frozenである(self) -> None:
        """IndexConstituent が frozen dataclass であること。"""
        constituent = self._make_constituent()

        with pytest.raises(FrozenInstanceError):
            constituent.symbol = "TATAMOTORS"  # type: ignore[misc]

    def test_正常系_全フィールドがstr型(self) -> None:
        """IndexConstituent の全フィールドが str 型であること。"""
        constituent = self._make_constituent()

        assert isinstance(constituent.symbol, str)
        assert isinstance(constituent.last_price, str)
        assert isinstance(constituent.year_high, str)
        assert isinstance(constituent.year_low, str)


# =============================================================================
# FinancialResult Dataclass
# =============================================================================


class TestFinancialResult:
    """FinancialResult frozen dataclass のテスト。"""

    def _make_result(self) -> FinancialResult:
        """テスト用 FinancialResult を生成する。"""
        return FinancialResult(
            symbol="RELIANCE",
            from_date="01-Jan-2025",
            to_date="31-Mar-2025",
            income="250000",
            profit_after_tax="18500",
            eps="27.35",
            result_type="Consolidated",
            broadcast_date="30-Apr-2025",
        )

    def test_正常系_全フィールドで初期化できる(self) -> None:
        """FinancialResult が全フィールドで初期化されること。"""
        result = self._make_result()

        assert result.symbol == "RELIANCE"
        assert result.from_date == "01-Jan-2025"
        assert result.to_date == "31-Mar-2025"
        assert result.income == "250000"
        assert result.profit_after_tax == "18500"
        assert result.eps == "27.35"
        assert result.result_type == "Consolidated"
        assert result.broadcast_date == "30-Apr-2025"

    def test_正常系_frozenである(self) -> None:
        """FinancialResult が frozen dataclass であること。"""
        result = self._make_result()

        with pytest.raises(FrozenInstanceError):
            result.symbol = "TATAMOTORS"  # type: ignore[misc]

    def test_正常系_全フィールドがstr型(self) -> None:
        """FinancialResult の全フィールドが str 型であること。"""
        result = self._make_result()

        assert isinstance(result.symbol, str)
        assert isinstance(result.income, str)
        assert isinstance(result.eps, str)
        assert isinstance(result.result_type, str)

    def test_正常系_Standaloneタイプで初期化可能(self) -> None:
        """result_type が 'Standalone' でも初期化できること。"""
        result = FinancialResult(
            symbol="INFY",
            from_date="01-Jan-2025",
            to_date="31-Mar-2025",
            income="45000",
            profit_after_tax="8200",
            eps="19.75",
            result_type="Standalone",
            broadcast_date="15-Apr-2025",
        )

        assert result.result_type == "Standalone"
