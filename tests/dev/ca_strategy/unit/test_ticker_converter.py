"""Tests for ca_strategy ticker_converter module.

TickerConverter converts Bloomberg format tickers (e.g. ``AAPL UW Equity``)
to yfinance format (e.g. ``AAPL``) using exchange-code suffix mapping and
an optional override dictionary.

Key behaviors:
- US equities (UW/UN) are converted by stripping the exchange code
- International equities receive the appropriate suffix (e.g. .L, .PA)
- Override dictionary takes precedence over automatic conversion
- Invalid formats and unknown exchange codes return the input unchanged
- Empty/whitespace strings return the input unchanged
- Batch conversion processes a list of tickers and returns a dict
"""

from __future__ import annotations

import pytest

from dev.ca_strategy.ticker_converter import TickerConverter


# ===========================================================================
# Single ticker conversion — US equities
# ===========================================================================
class TestConvertUSEquities:
    """Bloomberg UW/UN (US) tickers → yfinance (no suffix)."""

    def test_正常系_NASDAQ_UWティッカーをサフィックスなしに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("AAPL UW Equity") == "AAPL"

    def test_正常系_NYSE_UNティッカーをサフィックスなしに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("JPM UN Equity") == "JPM"

    def test_正常系_NYSE_Arca_URティッカーをサフィックスなしに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("SPY UR Equity") == "SPY"

    def test_正常系_NYSE_American_UAティッカーをサフィックスなしに変換できる(
        self,
    ) -> None:
        converter = TickerConverter()
        assert converter.convert("TEST UA Equity") == "TEST"


# ===========================================================================
# Single ticker conversion — International equities
# ===========================================================================
class TestConvertInternationalEquities:
    """Bloomberg international tickers → yfinance with correct suffix."""

    def test_正常系_LN_ロンドン取引所を_Lサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("BARC LN Equity") == "BARC.L"

    def test_正常系_FP_パリ取引所を_PAサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("AIR FP Equity") == "AIR.PA"

    def test_正常系_GY_ドイツ取引所を_DEサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("SAP GY Equity") == "SAP.DE"

    def test_正常系_JT_東京証券取引所を_Tサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("7203 JT Equity") == "7203.T"

    def test_正常系_HK_香港取引所を_HKサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("700 HK Equity") == "700.HK"

    def test_正常系_CN_トロント取引所を_TOサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("TD CN Equity") == "TD.TO"

    def test_正常系_SW_スイス取引所を_SWサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("NESN SW Equity") == "NESN.SW"

    def test_正常系_NA_アムステルダム取引所を_ASサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("ASML NA Equity") == "ASML.AS"

    def test_正常系_IM_ミラノ取引所を_MIサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("ENI IM Equity") == "ENI.MI"

    def test_正常系_SM_マドリード取引所を_MCサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("SAN SM Equity") == "SAN.MC"

    def test_正常系_AT_オーストラリア取引所を_AXサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("BHP AT Equity") == "BHP.AX"

    def test_正常系_SS_ストックホルム取引所を_STサフィックスに変換できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("ERIC SS Equity") == "ERIC.ST"


# ===========================================================================
# Override dictionary
# ===========================================================================
class TestOverrideDictionary:
    """Override dictionary takes precedence over automatic conversion."""

    def test_正常系_オーバーライド辞書が自動変換より優先される(self) -> None:
        overrides = {"BRK/B UN Equity": "BRK-B"}
        converter = TickerConverter(overrides=overrides)
        assert converter.convert("BRK/B UN Equity") == "BRK-B"

    def test_正常系_オーバーライド辞書にないティッカーは自動変換される(self) -> None:
        overrides = {"BRK/B UN Equity": "BRK-B"}
        converter = TickerConverter(overrides=overrides)
        assert converter.convert("AAPL UW Equity") == "AAPL"

    def test_正常系_複数オーバーライドが全て適用される(self) -> None:
        overrides = {
            "BRK/B UN Equity": "BRK-B",
            "GOOGL UW Equity": "GOOGL",
        }
        converter = TickerConverter(overrides=overrides)
        assert converter.convert("BRK/B UN Equity") == "BRK-B"
        assert converter.convert("GOOGL UW Equity") == "GOOGL"

    def test_正常系_オーバーライドなしで初期化できる(self) -> None:
        converter = TickerConverter()
        assert converter.convert("AAPL UW Equity") == "AAPL"

    def test_正常系_空オーバーライド辞書で初期化できる(self) -> None:
        converter = TickerConverter(overrides={})
        assert converter.convert("AAPL UW Equity") == "AAPL"


# ===========================================================================
# Error / edge cases — convert()
# ===========================================================================
class TestConvertEdgeCases:
    """Edge cases: invalid format, unknown exchange, empty input."""

    def test_異常系_不正形式でエラーにならず入力をそのまま返す(self) -> None:
        converter = TickerConverter()
        result = converter.convert("INVALIDFORMAT")
        assert result == "INVALIDFORMAT"

    def test_異常系_未知の取引所コードでエラーにならず入力をそのまま返す(self) -> None:
        converter = TickerConverter()
        result = converter.convert("TEST ZZ Equity")
        assert result == "TEST ZZ Equity"

    def test_エッジケース_空文字列でエラーにならず入力をそのまま返す(self) -> None:
        converter = TickerConverter()
        result = converter.convert("")
        assert result == ""

    def test_エッジケース_スペースのみでエラーにならず入力をそのまま返す(self) -> None:
        converter = TickerConverter()
        result = converter.convert("   ")
        assert result == "   "

    def test_エッジケース_取引所コードの前後スペースを無視できる(self) -> None:
        converter = TickerConverter()
        result = converter.convert("  AAPL UW Equity  ")
        assert result == "AAPL"

    def test_エッジケース_取引所コードが小文字でも変換できる(self) -> None:
        converter = TickerConverter()
        result = converter.convert("AAPL uw Equity")
        assert result == "AAPL"


# ===========================================================================
# Batch conversion
# ===========================================================================
class TestConvertBatch:
    """Batch conversion of multiple tickers."""

    def test_正常系_複数ティッカーを一括変換できる(self) -> None:
        converter = TickerConverter()
        tickers = ["AAPL UW Equity", "7203 JT Equity", "BARC LN Equity"]
        result = converter.convert_batch(tickers)

        assert result["AAPL UW Equity"] == "AAPL"
        assert result["7203 JT Equity"] == "7203.T"
        assert result["BARC LN Equity"] == "BARC.L"

    def test_正常系_バッチ変換の結果が入力と同じ長さを持つ(self) -> None:
        converter = TickerConverter()
        tickers = ["AAPL UW Equity", "MSFT UW Equity", "JPM UN Equity"]
        result = converter.convert_batch(tickers)
        assert len(result) == len(tickers)

    def test_エッジケース_空リストでバッチ変換が空dictを返す(self) -> None:
        converter = TickerConverter()
        result = converter.convert_batch([])
        assert result == {}

    def test_正常系_バッチ変換でオーバーライドが適用される(self) -> None:
        overrides = {"BRK/B UN Equity": "BRK-B"}
        converter = TickerConverter(overrides=overrides)
        tickers = ["BRK/B UN Equity", "AAPL UW Equity"]
        result = converter.convert_batch(tickers)
        assert result["BRK/B UN Equity"] == "BRK-B"
        assert result["AAPL UW Equity"] == "AAPL"

    def test_正常系_バッチ変換でキーはBloomberg形式である(self) -> None:
        converter = TickerConverter()
        tickers = ["AAPL UW Equity"]
        result = converter.convert_batch(tickers)
        assert "AAPL UW Equity" in result

    def test_異常系_バッチ変換で不正なティッカーはそのまま値として保持される(
        self,
    ) -> None:
        converter = TickerConverter()
        tickers = ["VALID UW Equity", "BADFORMAT", "UNKNOWN ZZ Equity"]
        result = converter.convert_batch(tickers)
        assert result["VALID UW Equity"] == "VALID"
        assert result["BADFORMAT"] == "BADFORMAT"
        assert result["UNKNOWN ZZ Equity"] == "UNKNOWN ZZ Equity"
