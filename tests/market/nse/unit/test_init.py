"""Tests for market.nse.__init__ public API exports and market integration.

Validates:
- All public symbols are importable from market.nse
- __all__ is complete and consistent
- DataSource enum contains NSE = 'nse'
- market.__init__ exports NSE symbols without name collision with BSE
"""

import pytest


class TestNseInitPublicApi:
    """Tests for market.nse public API exports."""

    def test_正常系_NseSessionがインポートできること(self) -> None:
        from market.nse import NseSession

        assert NseSession is not None

    def test_正常系_NseConfigがインポートできること(self) -> None:
        from market.nse import NseConfig

        assert NseConfig is not None

    def test_正常系_RetryConfigがインポートできること(self) -> None:
        from market.nse import RetryConfig

        assert RetryConfig is not None

    def test_正常系_4コレクタがインポートできること(self) -> None:
        from market.nse import (
            CorporateCollector,
            IndicesCollector,
            QuoteCollector,
            StockListCollector,
        )

        assert CorporateCollector is not None
        assert IndicesCollector is not None
        assert QuoteCollector is not None
        assert StockListCollector is not None

    def test_正常系_6例外クラスがインポートできること(self) -> None:
        from market.nse import (
            NseAPIError,
            NseCookieError,
            NseError,
            NseParseError,
            NseRateLimitError,
            NseValidationError,
        )

        assert NseError is not None
        assert NseAPIError is not None
        assert NseRateLimitError is not None
        assert NseCookieError is not None
        assert NseParseError is not None
        assert NseValidationError is not None

    def test_正常系_パーサー関数がインポートできること(self) -> None:
        from market.nse import (
            clean_indian_number,
            clean_price,
            clean_volume,
            parse_all_indices,
            parse_event_calendar,
            parse_financial_results,
            parse_index_constituents,
            parse_market_status,
            parse_preopen_data,
            parse_quote_response,
            parse_stock_list_csv,
        )

        assert clean_price is not None
        assert clean_volume is not None
        assert clean_indian_number is not None
        assert parse_quote_response is not None
        assert parse_index_constituents is not None
        assert parse_financial_results is not None
        assert parse_event_calendar is not None
        assert parse_stock_list_csv is not None
        assert parse_preopen_data is not None
        assert parse_all_indices is not None
        assert parse_market_status is not None

    def test_正常系_データレコードがインポートできること(self) -> None:
        from market.nse import (
            CorporateEvent,
            FinancialResult,
            IndexConstituent,
            MarketStatus,
            NseIndex,
            StockQuote,
        )

        assert NseIndex is not None
        assert StockQuote is not None
        assert IndexConstituent is not None
        assert CorporateEvent is not None
        assert MarketStatus is not None
        assert FinancialResult is not None


class TestNseInitAll:
    """Tests for __all__ completeness."""

    def test_正常系_dunder_allが定義されていること(self) -> None:
        import market.nse as nse_mod

        assert hasattr(nse_mod, "__all__")
        assert isinstance(nse_mod.__all__, list)

    def test_正常系_dunder_allが空でないこと(self) -> None:
        import market.nse as nse_mod

        assert len(nse_mod.__all__) > 0

    def test_正常系_dunder_allのエントリがアルファベット順であること(self) -> None:
        import market.nse as nse_mod

        all_entries = nse_mod.__all__
        assert all_entries == sorted(all_entries), (
            f"__all__ is not sorted alphabetically. "
            f"Expected: {sorted(all_entries)}, Got: {all_entries}"
        )

    def test_正常系_dunder_allの全エントリがモジュールに存在すること(self) -> None:
        import market.nse as nse_mod

        for name in nse_mod.__all__:
            assert hasattr(nse_mod, name), (
                f"'{name}' is listed in __all__ but not defined in market.nse"
            )

    def test_正常系_公開APIシンボルがdunder_allに含まれていること(self) -> None:
        import market.nse as nse_mod

        required = [
            # Session and config
            "NseSession",
            "NseConfig",
            "RetryConfig",
            # Collectors
            "CorporateCollector",
            "IndicesCollector",
            "QuoteCollector",
            "StockListCollector",
            # Exceptions
            "NseAPIError",
            "NseCookieError",
            "NseError",
            "NseParseError",
            "NseRateLimitError",
            "NseValidationError",
            # Parsers
            "clean_indian_number",
            "clean_price",
            "clean_volume",
            "parse_all_indices",
            "parse_event_calendar",
            "parse_financial_results",
            "parse_index_constituents",
            "parse_market_status",
            "parse_preopen_data",
            "parse_quote_response",
            "parse_stock_list_csv",
            # Data records and enums
            "CorporateEvent",
            "FinancialResult",
            "IndexConstituent",
            "MarketStatus",
            "NseIndex",
            "StockQuote",
        ]
        for name in required:
            assert name in nse_mod.__all__, (
                f"'{name}' is missing from market.nse.__all__"
            )


class TestDataSourceNse:
    """Tests for DataSource enum NSE entry."""

    def test_正常系_DataSourceにNSEが追加されていること(self) -> None:
        from market.types import DataSource

        assert hasattr(DataSource, "NSE")

    def test_正常系_DataSourceNSEの値がnseであること(self) -> None:
        from market.types import DataSource

        assert DataSource.NSE == "nse"
        assert DataSource.NSE.value == "nse"

    def test_正常系_DataSourceNSEが文字列として使用できること(self) -> None:
        from market.types import DataSource

        assert str(DataSource.NSE) == "DataSource.NSE"
        assert DataSource.NSE == "nse"  # str(Enum) comparison via __eq__


class TestMarketPackageNseExports:
    """Tests for market.__init__ NSE exports and name collision avoidance."""

    def test_正常系_market_NseSessionがインポートできること(self) -> None:
        from market import NseSession

        assert NseSession is not None

    def test_正常系_market_NseConfigがインポートできること(self) -> None:
        from market import NseConfig

        assert NseConfig is not None

    def test_正常系_market_NseRetryConfigがインポートできること(self) -> None:
        from market import NseRetryConfig

        assert NseRetryConfig is not None

    def test_正常系_市場パッケージからNSEコレクタがインポートできること(self) -> None:
        from market import (
            NseCorporateCollector,
            NseIndicesCollector,
            NseQuoteCollector,
            NseStockListCollector,
        )

        assert NseCorporateCollector is not None
        assert NseIndicesCollector is not None
        assert NseQuoteCollector is not None
        assert NseStockListCollector is not None

    def test_正常系_NSE例外クラスがmarketからインポートできること(self) -> None:
        from market import (
            NseAPIError,
            NseCookieError,
            NseError,
            NseParseError,
            NseRateLimitError,
            NseValidationError,
        )

        assert NseError is not None
        assert NseAPIError is not None
        assert NseCookieError is not None
        assert NseParseError is not None
        assert NseRateLimitError is not None
        assert NseValidationError is not None

    def test_正常系_BSEとNSEのRetryConfigが衝突しないこと(self) -> None:
        """BSEとNSEのRetryConfigが別名でエクスポートされ、名前衝突がないことを確認。"""
        from market import BseRetryConfig, NseRetryConfig

        # Both should be importable and distinct aliases
        assert BseRetryConfig is not None
        assert NseRetryConfig is not None

    def test_正常系_DataSourceがmarketからインポートできること(self) -> None:
        from market import DataSource

        assert hasattr(DataSource, "NSE")
        assert DataSource.NSE.value == "nse"

    def test_正常系_NSEエントリがmarket_dunder_allに含まれていること(self) -> None:
        import market as market_mod

        nse_entries = [name for name in market_mod.__all__ if "Nse" in name]
        assert len(nse_entries) > 0, (
            "No NSE entries found in market.__all__. "
            "Expected entries with 'Nse' prefix."
        )
