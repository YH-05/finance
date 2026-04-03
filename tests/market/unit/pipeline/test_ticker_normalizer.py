"""Unit tests for market.pipeline.ticker_normalizer."""

import pytest

from market.pipeline.errors import TickerNormalizationError
from market.pipeline.ticker_normalizer import normalize_ticker


class TestNormalizeTickerAlphavantage:
    def test_正常系_ドット付きシンボルの最初のコンポーネントを返す(self) -> None:
        assert normalize_ticker("GEF.B", "alphavantage") == "GEF"

    def test_正常系_ドットなしシンボルはそのまま返す(self) -> None:
        assert normalize_ticker("AAPL", "alphavantage") == "AAPL"

    def test_正常系_BRK_Bが正しく変換される(self) -> None:
        assert normalize_ticker("BRK.B", "alphavantage") == "BRK"

    def test_エッジケース_複数ドットのシンボルは最初のコンポーネントのみ返す(
        self,
    ) -> None:
        assert normalize_ticker("A.B.C", "alphavantage") == "A"


class TestNormalizeTickerYfinance:
    def test_正常系_ドットをハイフンに変換する(self) -> None:
        assert normalize_ticker("GEF.B", "yfinance") == "GEF-B"

    def test_正常系_ドットなしシンボルはそのまま返す(self) -> None:
        assert normalize_ticker("AAPL", "yfinance") == "AAPL"

    def test_正常系_BRK_Bが正しく変換される(self) -> None:
        assert normalize_ticker("BRK.B", "yfinance") == "BRK-B"

    def test_エッジケース_複数ドットは全てハイフンに変換される(self) -> None:
        assert normalize_ticker("A.B.C", "yfinance") == "A-B-C"


class TestNormalizeTickerNasdaq:
    def test_正常系_シンボルをそのまま返す(self) -> None:
        assert normalize_ticker("AAPL", "nasdaq") == "AAPL"

    def test_正常系_ドット付きシンボルをそのまま返す(self) -> None:
        assert normalize_ticker("GEF.B", "nasdaq") == "GEF.B"


class TestNormalizeTickerSecEdgar:
    def test_正常系_シンボルをそのまま返す(self) -> None:
        assert normalize_ticker("AAPL", "sec_edgar") == "AAPL"

    def test_正常系_ドット付きシンボルをそのまま返す(self) -> None:
        assert normalize_ticker("GEF.B", "sec_edgar") == "GEF.B"


class TestNormalizeTickerInvalidTarget:
    def test_異常系_不明なターゲットでTickerNormalizationErrorを送出する(self) -> None:
        with pytest.raises(
            TickerNormalizationError, match="Unknown normalisation target"
        ):
            normalize_ticker("AAPL", "unknown_exchange")  # type: ignore[arg-type]

    def test_異常系_エラーのコンテキストにシンボルとターゲットが含まれる(self) -> None:
        with pytest.raises(TickerNormalizationError) as exc_info:
            normalize_ticker("AAPL", "bad_target")  # type: ignore[arg-type]
        assert exc_info.value.context["symbol"] == "AAPL"
        assert exc_info.value.context["target"] == "bad_target"


class TestAcceptanceCriteria:
    """受け入れ条件を直接テスト。"""

    def test_受け入れ条件_GEF_B_alphavantageが_GEFを返す(self) -> None:
        assert normalize_ticker("GEF.B", "alphavantage") == "GEF"

    def test_受け入れ条件_GEF_B_yfinanceが_GEF_Bを返す(self) -> None:
        assert normalize_ticker("GEF.B", "yfinance") == "GEF-B"
