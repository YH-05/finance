"""Unit tests for market.pipeline.ticker_normalizer.normalize_ticker().

Tests verify correct normalisation for all supported targets and proper
error handling for unknown targets.
"""

from __future__ import annotations

import pytest

from market.pipeline.errors import TickerNormalizationError
from market.pipeline.ticker_normalizer import normalize_ticker


class TestNormalizeTickerNasdaq:
    """Tests for the 'nasdaq' normalisation target (identity transform)."""

    def test_正常系_単純シンボルは変換なし(self) -> None:
        assert normalize_ticker("AAPL", "nasdaq") == "AAPL"

    def test_正常系_ドット付きシンボルはそのまま(self) -> None:
        assert normalize_ticker("GEF.B", "nasdaq") == "GEF.B"

    def test_正常系_小文字も変換なし(self) -> None:
        assert normalize_ticker("msft", "nasdaq") == "msft"

    def test_正常系_BRKBはそのまま(self) -> None:
        assert normalize_ticker("BRK.B", "nasdaq") == "BRK.B"


class TestNormalizeTickerSecEdgar:
    """Tests for the 'sec_edgar' normalisation target (identity transform)."""

    def test_正常系_単純シンボルは変換なし(self) -> None:
        assert normalize_ticker("AAPL", "sec_edgar") == "AAPL"

    def test_正常系_ドット付きシンボルはそのまま(self) -> None:
        assert normalize_ticker("GEF.B", "sec_edgar") == "GEF.B"

    def test_正常系_BRKBはそのまま(self) -> None:
        assert normalize_ticker("BRK.B", "sec_edgar") == "BRK.B"


class TestNormalizeTickerAlphaVantage:
    """Tests for the 'alphavantage' normalisation target (split on '.')."""

    def test_正常系_ドット付きシンボルはプレフィックスのみ(self) -> None:
        assert normalize_ticker("GEF.B", "alphavantage") == "GEF"

    def test_正常系_BRKBはBRKになる(self) -> None:
        assert normalize_ticker("BRK.B", "alphavantage") == "BRK"

    def test_正常系_ドットなし単純シンボルは変換なし(self) -> None:
        assert normalize_ticker("AAPL", "alphavantage") == "AAPL"

    def test_正常系_MSFTはそのまま(self) -> None:
        assert normalize_ticker("MSFT", "alphavantage") == "MSFT"

    def test_正常系_複数ドットの場合は最初のセグメントのみ(self) -> None:
        # e.g. "A.B.C" → "A"
        assert normalize_ticker("A.B.C", "alphavantage") == "A"


class TestNormalizeTickerYFinance:
    """Tests for the 'yfinance' normalisation target (replace '.' with '-')."""

    def test_正常系_ドット付きシンボルはハイフンに変換(self) -> None:
        assert normalize_ticker("GEF.B", "yfinance") == "GEF-B"

    def test_正常系_BRKBはBRKハイフンBになる(self) -> None:
        assert normalize_ticker("BRK.B", "yfinance") == "BRK-B"

    def test_正常系_ドットなし単純シンボルは変換なし(self) -> None:
        assert normalize_ticker("AAPL", "yfinance") == "AAPL"

    def test_正常系_複数ドットはすべてハイフンに変換(self) -> None:
        assert normalize_ticker("A.B.C", "yfinance") == "A-B-C"


class TestNormalizeTickerUnknownTarget:
    """Tests for unknown/invalid normalisation targets."""

    def test_異常系_不明なターゲットでTickerNormalizationError(self) -> None:
        with pytest.raises(TickerNormalizationError):
            normalize_ticker("AAPL", "unknown_exchange")  # type: ignore[arg-type]

    def test_異常系_空文字列ターゲットでTickerNormalizationError(self) -> None:
        with pytest.raises(TickerNormalizationError):
            normalize_ticker("AAPL", "")  # type: ignore[arg-type]

    def test_異常系_エラーにはシンボルとターゲットのコンテキストが含まれる(self) -> None:
        with pytest.raises(TickerNormalizationError) as exc_info:
            normalize_ticker("AAPL", "bad_target")  # type: ignore[arg-type]
        assert exc_info.value.context["symbol"] == "AAPL"
        assert exc_info.value.context["target"] == "bad_target"


class TestNormalizeTickerEdgeCases:
    """Edge case tests for normalize_ticker."""

    def test_エッジケース_空シンボルnasdaqはそのまま(self) -> None:
        assert normalize_ticker("", "nasdaq") == ""

    def test_エッジケース_空シンボルalphavantageはそのまま(self) -> None:
        # split("")[0] == ""
        assert normalize_ticker("", "alphavantage") == ""

    def test_エッジケース_空シンボルyfinanceはそのまま(self) -> None:
        assert normalize_ticker("", "yfinance") == ""

    def test_エッジケース_ドットのみのシンボルalphavantage(self) -> None:
        # ".".split(".") == ["", ""]  → first part is ""
        assert normalize_ticker(".", "alphavantage") == ""

    def test_エッジケース_ドットのみのシンボルyfinance(self) -> None:
        # "." replaced by "-" → "-"
        assert normalize_ticker(".", "yfinance") == "-"
