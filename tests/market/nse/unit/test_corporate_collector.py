"""Unit tests for market.nse.collectors.corporate module.

CorporateCollector の動作を検証するテストスイート。
Mixin のみ継承した NSE CorporateCollector のテスト。

Test TODO List:
- [x] CorporateCollector: デフォルト値で初期化（session なし）
- [x] CorporateCollector: DI パターンで session 注入
- [x] get_financial_results(): 財務結果リストを取得
- [x] get_financial_results(): 正しいエンドポイントにリクエスト
- [x] get_financial_results(): セッションを正しくクローズ
- [x] get_event_calendar(): イベントカレンダーリストを取得
- [x] get_event_calendar(): 正しいエンドポイントにリクエスト
- [x] search(): クエリでシンボル検索
- [x] search(): 空クエリで ValueError
- [x] search(): 100 文字超クエリで ValueError
- [x] DataCollector ABC を継承していないことを確認
- [x] Module exports: __all__ completeness
"""

from unittest.mock import MagicMock, patch

import pytest

from market.base_collector import DataCollector
from market.nse.collectors.corporate import CorporateCollector
from market.nse.session import NseSession
from market.nse.types import CorporateEvent, FinancialResult

# =============================================================================
# Helper: create mock session and responses
# =============================================================================


def _make_financial_results_json(
    *,
    symbol: str = "RELIANCE",
) -> dict:
    """Create a mock NSE /api/results-comparision JSON response."""
    return {
        "bankNonBnking": "N",
        "resCmpData": [
            {
                "symbol": symbol,
                "re_from_dt": "01-JAN-2025",
                "re_to_dt": "31-MAR-2025",
                "re_res_type": "Q",
                "re_net_sale": "2341000",
                "re_oth_inc_new": "50000",
                "re_total_inc": "2391000",
                "re_net_profit": "185000",
                "re_basic_eps_for_cont_dic_opr": "27.35",
                "re_create_dt": "30-Apr-2025",
            }
        ],
    }


def _make_event_calendar_json() -> list:
    """Create a mock NSE /api/event-calendar JSON response."""
    return [
        {
            "symbol": "RELIANCE",
            "company": "Reliance Industries Limited",
            "purpose": "Dividend",
            "bm_desc": "Board Meeting to consider dividend.",
            "date": "03-Apr-2026",
        }
    ]


def _make_search_json() -> dict:
    """Create a mock NSE search autocomplete JSON response."""
    return {
        "symbols": [
            {
                "symbol": "RELIANCE",
                "companyName": "Reliance Industries Limited",
                "series": "EQ",
            }
        ]
    }


def _make_mock_session(
    *,
    response_json: dict | list | None = None,
) -> MagicMock:
    """Create a mock NseSession with pre-configured responses."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    if response_json is None:
        mock_response.json.return_value = _make_financial_results_json()
    else:
        mock_response.json.return_value = response_json
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


# =============================================================================
# Tests: Initialization
# =============================================================================


class TestCorporateCollectorInit:
    def test_正常系_デフォルト値で初期化(self) -> None:
        collector = CorporateCollector()
        assert collector._session_instance is None

    def test_正常系_session注入で初期化(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = CorporateCollector(session=mock_session)
        assert collector._session_instance is mock_session

    def test_正常系_DataCollectorABCを継承していない(self) -> None:
        assert not issubclass(CorporateCollector, DataCollector)


# =============================================================================
# Tests: get_financial_results()
# =============================================================================


class TestGetFinancialResults:
    def test_正常系_財務結果リストを取得(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_financial_results_json(symbol="RELIANCE")
        )
        collector = CorporateCollector(session=mock_session)
        results = collector.get_financial_results("RELIANCE")
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], FinancialResult)
        assert results[0].symbol == "RELIANCE"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_financial_results_json()
        )
        collector = CorporateCollector(session=mock_session)
        collector.get_financial_results("RELIANCE")
        call_args = mock_session.get_with_retry.call_args
        assert "results-comparision" in call_args[0][0]
        assert call_args[1]["params"]["symbol"] == "RELIANCE"

    def test_正常系_注入セッションはクローズしない(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_financial_results_json()
        )
        collector = CorporateCollector(session=mock_session)
        collector.get_financial_results("RELIANCE")
        mock_session.close.assert_not_called()

    def test_正常系_非注入セッションはクローズする(self) -> None:
        mock_new_session = _make_mock_session(
            response_json=_make_financial_results_json()
        )
        with patch(
            "market.nse.collectors._base.NseSession", return_value=mock_new_session
        ):
            collector = CorporateCollector()
            collector.get_financial_results("RELIANCE")
        mock_new_session.close.assert_called_once()


# =============================================================================
# Tests: get_event_calendar()
# =============================================================================


class TestGetEventCalendar:
    def test_正常系_イベントカレンダーリストを取得(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_event_calendar_json()
        )
        collector = CorporateCollector(session=mock_session)
        events = collector.get_event_calendar()
        assert isinstance(events, list)
        assert len(events) == 1
        assert isinstance(events[0], CorporateEvent)
        assert events[0].symbol == "RELIANCE"
        assert events[0].purpose == "Dividend"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_event_calendar_json()
        )
        collector = CorporateCollector(session=mock_session)
        collector.get_event_calendar()
        call_args = mock_session.get_with_retry.call_args
        assert "event-calendar" in call_args[0][0]

    def test_正常系_dict形式レスポンスも処理できる(self) -> None:
        """NSE sometimes wraps the list in a dict with 'data' key."""
        mock_session = _make_mock_session(
            response_json={"data": _make_event_calendar_json()}
        )
        collector = CorporateCollector(session=mock_session)
        events = collector.get_event_calendar()
        assert isinstance(events, list)
        assert len(events) == 1


# =============================================================================
# Tests: search()
# =============================================================================


class TestSearch:
    def test_正常系_クエリでシンボル検索(self) -> None:
        mock_session = _make_mock_session(response_json=_make_search_json())
        collector = CorporateCollector(session=mock_session)
        results = collector.search("RELIANCE")
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["symbol"] == "RELIANCE"

    def test_異常系_空クエリでValueError(self) -> None:
        collector = CorporateCollector(session=MagicMock(spec=NseSession))
        with pytest.raises(ValueError, match="query must not be empty"):
            collector.search("")

    def test_異常系_スペースのみクエリでValueError(self) -> None:
        collector = CorporateCollector(session=MagicMock(spec=NseSession))
        with pytest.raises(ValueError, match="query must not be empty"):
            collector.search("   ")

    def test_異常系_100文字超クエリでValueError(self) -> None:
        collector = CorporateCollector(session=MagicMock(spec=NseSession))
        with pytest.raises(ValueError, match="must not exceed 100 characters"):
            collector.search("A" * 101)

    def test_正常系_空リストレスポンスを処理(self) -> None:
        mock_session = _make_mock_session(response_json={"symbols": []})
        collector = CorporateCollector(session=mock_session)
        results = collector.search("XYZ")
        assert results == []


# =============================================================================
# Tests: Module exports
# =============================================================================


class TestModuleExports:
    def test_正常系_all完全性(self) -> None:
        from market.nse.collectors import corporate as module

        assert "CorporateCollector" in module.__all__
