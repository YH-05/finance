"""Unit tests for NSE shareholding pattern feature.

ShareholdingPattern dataclass、parse_shareholding_pattern() パーサー、
CorporateCollector.get_shareholding_pattern() メソッドの動作を検証。

Test TODO List:
- [x] ShareholdingPattern: 全フィールドで初期化（fii/dii なし）
- [x] ShareholdingPattern: frozen=True で不変
- [x] parse_shareholding_pattern(): 正常な dict を解析できる
- [x] parse_shareholding_pattern(): 空 dict で空リストを返す
- [x] parse_shareholding_pattern(): dict でない入力で NseParseError
- [x] parse_shareholding_pattern(): promoter_group 欠損（HDFCBANK型）で空文字列フォールバック
- [x] parse_shareholding_pattern(): symbol 引数が各レコードに設定される
- [x] CorporateCollector.get_shareholding_pattern(): list[ShareholdingPattern] を返す
- [x] CorporateCollector.get_shareholding_pattern(): 正しいエンドポイント（NextApi）にリクエスト
- [x] CorporateCollector.get_shareholding_pattern(): functionName=getShareholdingPattern パラメータ
- [x] CorporateCollector.get_shareholding_pattern(): 注入セッションはクローズしない
- [x] SHAREHOLDING_FIELD_MAP: constants.py に存在する
- [x] エクスポート: __init__.py から import できる
"""

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock

import pytest

from market.nse.errors import NseParseError
from market.nse.parsers import parse_shareholding_pattern
from market.nse.session import NseSession
from market.nse.types import ShareholdingPattern

# =============================================================================
# Helper: create mock session and responses
# =============================================================================


def _make_shareholding_json() -> dict:
    """Create a mock NSE NextApi getShareholdingPattern JSON response (RELIANCE)."""
    return {
        "31-Dec-2025": {
            "ndsid": "207095",
            "series": "equity",
            "Total": "100.00",
            "public": {"name": "Public", "value": "49.99"},
            "promoter_group": {
                "name": "Promoter & Promoter Group",
                "value": "50.01",
            },
        },
        "30-Sep-2025": {
            "ndsid": "203594",
            "series": "equity",
            "promoter_group": {
                "name": "Promoter & Promoter Group",
                "value": "50.01",
            },
            "Total": "100.00",
            "public": {"name": "Public", "value": "49.99"},
        },
    }


def _make_hdfcbank_json() -> dict:
    """Create a mock response for HDFCBANK (no promoter_group key)."""
    return {
        "31-Mar-2026": {
            "ndsid": "207379",
            "series": "equity",
            "Total": "100.00",
            "public": {"name": "Public", "value": "100.00"},
        },
    }


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
        """fii/dii なしの新しいフィールド構成で初期化できることを確認。"""
        pattern = ShareholdingPattern(
            symbol="RELIANCE",
            date="31-Dec-2025",
            ndsid="207095",
            series="equity",
            total="100.00",
            promoter_group="50.01",
            public="49.99",
        )
        assert pattern.symbol == "RELIANCE"
        assert pattern.date == "31-Dec-2025"
        assert pattern.ndsid == "207095"
        assert pattern.series == "equity"
        assert pattern.total == "100.00"
        assert pattern.promoter_group == "50.01"
        assert pattern.public == "49.99"

    def test_正常系_frozenで不変(self) -> None:
        pattern = ShareholdingPattern(
            symbol="RELIANCE",
            date="31-Dec-2025",
            ndsid="207095",
        )
        with pytest.raises(FrozenInstanceError):
            pattern.symbol = "TCS"

    def test_正常系_デフォルト値が適用される(self) -> None:
        """series, total, promoter_group, public にデフォルト値がある。"""
        pattern = ShareholdingPattern(
            symbol="HDFCBANK",
            date="31-Mar-2026",
            ndsid="207379",
        )
        assert pattern.series == "equity"
        assert pattern.total == "100.00"
        assert pattern.promoter_group == ""
        assert pattern.public == ""


# =============================================================================
# Tests: parse_shareholding_pattern()
# =============================================================================


class TestParseShareholdingPattern:
    def test_正常系_正常なdictを解析できる(self) -> None:
        data = _make_shareholding_json()
        results = parse_shareholding_pattern(data, symbol="RELIANCE")
        assert isinstance(results, list)
        assert len(results) == 2
        assert isinstance(results[0], ShareholdingPattern)

        # First record: 31-Dec-2025
        assert results[0].symbol == "RELIANCE"
        assert results[0].date == "31-Dec-2025"
        assert results[0].ndsid == "207095"
        assert results[0].series == "equity"
        assert results[0].total == "100.00"
        assert results[0].promoter_group == "50.01"
        assert results[0].public == "49.99"

        # Second record: 30-Sep-2025
        assert results[1].date == "30-Sep-2025"
        assert results[1].ndsid == "203594"

    def test_正常系_空dictで空リストを返す(self) -> None:
        results = parse_shareholding_pattern({})
        assert results == []

    def test_異常系_dictでない入力でNseParseError(self) -> None:
        with pytest.raises(NseParseError):
            parse_shareholding_pattern([{"not": "a dict"}])  # type: ignore[arg-type]

    def test_正常系_promoter_group欠損で空文字列フォールバック(self) -> None:
        """HDFCBANK のように promoter_group キーが存在しないケース。"""
        data = _make_hdfcbank_json()
        results = parse_shareholding_pattern(data, symbol="HDFCBANK")
        assert len(results) == 1
        assert results[0].symbol == "HDFCBANK"
        assert results[0].promoter_group == ""
        assert results[0].public == "100.00"
        assert results[0].ndsid == "207379"

    def test_正常系_symbol引数が各レコードに設定される(self) -> None:
        data = _make_shareholding_json()
        results = parse_shareholding_pattern(data, symbol="RELIANCE")
        for r in results:
            assert r.symbol == "RELIANCE"

    def test_正常系_symbolデフォルトは空文字列(self) -> None:
        data = _make_shareholding_json()
        results = parse_shareholding_pattern(data)
        for r in results:
            assert r.symbol == ""

    def test_正常系_dict以外のrecord値はスキップ(self) -> None:
        """日付キーの値が dict でない場合はスキップする。"""
        data: dict = {
            "31-Dec-2025": {
                "ndsid": "207095",
                "series": "equity",
                "Total": "100.00",
                "public": {"name": "Public", "value": "49.99"},
                "promoter_group": {
                    "name": "Promoter & Promoter Group",
                    "value": "50.01",
                },
            },
            "invalid": "not a dict",
        }
        results = parse_shareholding_pattern(data, symbol="RELIANCE")
        assert len(results) == 1
        assert results[0].date == "31-Dec-2025"

    def test_異常系_文字列入力でNseParseError(self) -> None:
        with pytest.raises(NseParseError):
            parse_shareholding_pattern("not a dict")  # type: ignore[arg-type]


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
        assert len(results) == 2
        assert isinstance(results[0], ShareholdingPattern)
        assert results[0].symbol == "RELIANCE"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json=_make_shareholding_json())
        collector = CorporateCollector(session=mock_session)
        collector.get_shareholding_pattern("RELIANCE")
        call_args = mock_session.get_with_retry.call_args
        # Endpoint should be NextApi
        assert "NextApi/apiClient/GetQuoteApi" in call_args[0][0]

    def test_正常系_functionNameパラメータが含まれる(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json=_make_shareholding_json())
        collector = CorporateCollector(session=mock_session)
        collector.get_shareholding_pattern("RELIANCE")
        call_args = mock_session.get_with_retry.call_args
        params = call_args[1]["params"]
        assert params["functionName"] == "getShareholdingPattern"
        assert params["symbol"] == "RELIANCE"
        assert params["noOfRecords"] == "5"

    def test_正常系_注入セッションはクローズしない(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json=_make_shareholding_json())
        collector = CorporateCollector(session=mock_session)
        collector.get_shareholding_pattern("RELIANCE")
        mock_session.close.assert_not_called()

    def test_正常系_空dictレスポンスで空リストを返す(self) -> None:
        from market.nse.collectors.corporate import CorporateCollector

        mock_session = _make_mock_session(response_json={})
        collector = CorporateCollector(session=mock_session)
        results = collector.get_shareholding_pattern("RELIANCE")
        assert results == []

    def test_正常系_非dictレスポンスで空リストを返す(self) -> None:
        """API が list や null を返した場合のフォールバック。"""
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

    def test_正常系_SHAREHOLDING_FIELD_MAPにfii_diiが含まれない(self) -> None:
        from market.nse import constants

        field_map = constants.SHAREHOLDING_FIELD_MAP
        assert "fii" not in field_map
        assert "dii" not in field_map


class TestModuleExports:
    def test_正常系_ShareholdingPatternをinitからimportできる(self) -> None:
        from market.nse import ShareholdingPattern as SP

        assert SP is ShareholdingPattern

    def test_正常系_parse_shareholding_patternをinitからimportできる(self) -> None:
        from market.nse import parse_shareholding_pattern as psp

        assert psp is parse_shareholding_pattern
