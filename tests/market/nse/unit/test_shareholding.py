"""Unit tests for NSE shareholding pattern feature.

ShareholdingPattern dataclass、parse_shareholding_pattern() パーサー、
CorporateCollector.get_shareholding_pattern() メソッドの動作を検証。

Test TODO List:
- [x] ShareholdingPattern: 全フィールドで初期化できる
- [x] ShareholdingPattern: frozen=True で不変
- [x] parse_shareholding_pattern(): 正常なリストを解析できる
- [x] parse_shareholding_pattern(): 空リストで空リストを返す
- [x] parse_shareholding_pattern(): リストでない入力で NseParseError
- [x] parse_shareholding_pattern(): 欠損フィールドは空文字列にフォールバック
- [x] CorporateCollector.get_shareholding_pattern(): list[ShareholdingPattern] を返す
- [x] CorporateCollector.get_shareholding_pattern(): 正しいエンドポイントにリクエスト
- [x] CorporateCollector.get_shareholding_pattern(): 注入セッションはクローズしない
- [x] SHAREHOLDING_FIELD_MAP: constants.py に存在する
- [x] ShareholdingPattern: __init__.py から import できる
- [x] parse_shareholding_pattern: __init__.py から import できる
"""

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

from market.nse.errors import NseParseError
from market.nse.parsers import parse_shareholding_pattern
from market.nse.session import NseSession
from market.nse.types import ShareholdingPattern


# =============================================================================
# Helper: create mock session and responses
# =============================================================================


def _make_shareholding_json() -> list:
    """Create a mock NSE /api/corporates-shareholding JSON response."""
    return [
        {
            "symbol": "RELIANCE",
            "date": "31-Dec-2024",
            "promoterGroup": "50.30",
            "fii": "23.45",
            "dii": "12.10",
            "public": "14.15",
        }
    ]


def _make_mock_session(
    *,
    response_json: dict | list | None = None,
) -> MagicMock:
    """Create a mock NseSession with pre-configured responses."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    if response_json is None:
        mock_response.json.return_value = _make_shareholding_json()
    else:
        mock_response.json.return_value = response_json
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


# =============================================================================
# Tests: ShareholdingPattern dataclass
# =============================================================================


class TestShareholdingPattern:
    def test_正常系_全フィールドで初期化できる(self) -> None:
        pattern = ShareholdingPattern(
            symbol="RELIANCE",
            date="31-Dec-2024",
            promoter_group="50.30",
            fii="23.45",
            dii="12.10",
            public="14.15",
        )
        assert pattern.symbol == "RELIANCE"
        assert pattern.date == "31-Dec-2024"
        assert pattern.promoter_group == "50.30"
        assert pattern.fii == "23.45"
        assert pattern.dii == "12.10"
        assert pattern.public == "14.15"

    def test_正常系_frozenで不変(self) -> None:
        pattern = ShareholdingPattern(
            symbol="RELIANCE",
            date="31-Dec-2024",
            promoter_group="50.30",
            fii="23.45",
            dii="12.10",
            public="14.15",
        )
        with pytest.raises(FrozenInstanceError):
            pattern.symbol = "TCS"  # type: ignore[misc]


# =============================================================================
# Tests: parse_shareholding_pattern()
# =============================================================================


class TestParseShareholdingPattern:
    def test_正常系_正常なリストを解析できる(self) -> None:
        data = _make_shareholding_json()
        results = parse_shareholding_pattern(data)
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], ShareholdingPattern)
        assert results[0].symbol == "RELIANCE"
        assert results[0].promoter_group == "50.30"

    def test_正常系_空リストで空リストを返す(self) -> None:
        results = parse_shareholding_pattern([])
        assert results == []

    def test_異常系_リストでない入力でNseParseError(self) -> None:
        with pytest.raises(NseParseError):
            parse_shareholding_pattern({"not": "a list"})  # type: ignore[arg-type]

    def test_正常系_欠損フィールドは空文字列にフォールバック(self) -> None:
        """必須フィールドが欠損していても空文字列でフォールバックする。"""
        data = [{"symbol": "TCS"}]  # fii, dii, public, promoterGroup, date が欠損
        results = parse_shareholding_pattern(data)
        assert len(results) == 1
        assert results[0].symbol == "TCS"
        assert results[0].promoter_group == ""
        assert results[0].fii == ""
        assert results[0].dii == ""
        assert results[0].public == ""
        assert results[0].date == ""

    def test_正常系_dict以外のアイテムはスキップ(self) -> None:
        """リスト内に dict 以外のアイテムが含まれてもスキップする。"""
        data = [{"symbol": "RELIANCE", "promoterGroup": "50.30"}, "invalid", None]
        results = parse_shareholding_pattern(data)  # type: ignore[arg-type]
        assert len(results) == 1
        assert results[0].symbol == "RELIANCE"

    def test_正常系_複数レコードを解析できる(self) -> None:
        data = [
            {
                "symbol": "RELIANCE",
                "date": "31-Dec-2024",
                "promoterGroup": "50.30",
                "fii": "23.45",
                "dii": "12.10",
                "public": "14.15",
            },
            {
                "symbol": "RELIANCE",
                "date": "30-Sep-2024",
                "promoterGroup": "50.10",
                "fii": "22.80",
                "dii": "12.50",
                "public": "14.60",
            },
        ]
        results = parse_shareholding_pattern(data)
        assert len(results) == 2
        assert results[0].date == "31-Dec-2024"
        assert results[1].date == "30-Sep-2024"


# =============================================================================
# Tests: CorporateCollector.get_shareholding_pattern()
# =============================================================================


class TestGetShareholdingPattern:
    def test_正常系_shareholdingパターンリストを取得(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json=_make_shareholding_json())
        collector = CorporateCollector(session=mock_session)
        results = collector.get_shareholding_pattern("RELIANCE")
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], ShareholdingPattern)
        assert results[0].symbol == "RELIANCE"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json=_make_shareholding_json())
        collector = CorporateCollector(session=mock_session)
        collector.get_shareholding_pattern("RELIANCE")
        call_args = mock_session.get_with_retry.call_args
        assert "corporates-shareholding" in call_args[0][0]
        assert call_args[1]["params"]["symbol"] == "RELIANCE"

    def test_正常系_注入セッションはクローズしない(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json=_make_shareholding_json())
        collector = CorporateCollector(session=mock_session)
        collector.get_shareholding_pattern("RELIANCE")
        mock_session.close.assert_not_called()

    def test_正常系_非注入セッションはクローズする(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_new_session = _make_mock_session(response_json=_make_shareholding_json())
        with patch(
            "market.nse.collectors._base.NseSession", return_value=mock_new_session
        ):
            collector = CorporateCollector()
            collector.get_shareholding_pattern("RELIANCE")
        mock_new_session.close.assert_called_once()

    def test_正常系_空レスポンスで空リストを返す(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json=[])
        collector = CorporateCollector(session=mock_session)
        results = collector.get_shareholding_pattern("RELIANCE")
        assert results == []


# =============================================================================
# Tests: Constants and module exports
# =============================================================================


class TestConstants:
    def test_正常系_SHAREHOLDING_FIELD_MAPがconstantsに存在する(self) -> None:
        from market.nse import constants

        assert hasattr(constants, "SHAREHOLDING_FIELD_MAP")
        assert isinstance(constants.SHAREHOLDING_FIELD_MAP, dict)


class TestModuleExports:
    def test_正常系_ShareholdingPatternをinitから_importできる(self) -> None:
        from market.nse import ShareholdingPattern as SP

        assert SP is ShareholdingPattern

    def test_正常系_parse_shareholding_patternをinitから_importできる(self) -> None:
        from market.nse import parse_shareholding_pattern as psp

        assert psp is parse_shareholding_pattern
