"""Unit tests for market.nse.collectors.share_holding module.

ShareholdingCollector の動作を検証するテストスイート。
NseCollectorMixin を継承した ShareholdingCollector のテスト。

Test TODO List:
- [x] ShareholdingCollector: デフォルト値で初期化（session なし）
- [x] ShareholdingCollector: DI パターンで session 注入
- [x] ShareholdingCollector: DataCollector ABC を継承していないことを確認
- [x] fetch_shareholding(): CorporateShareHolding リストを返す
- [x] fetch_shareholding(): 正しいエンドポイントにリクエスト
- [x] fetch_shareholding(): 注入 session は close() されない
- [x] fetch_shareholding(): 空文字列で ValueError
- [x] fetch_shareholding(): 長さ超過で ValueError
- [x] fetch_shareholding(): 無効文字で ValueError
- [x] fetch_xbrl_detail(): XBRL バイトを parse_xbrl に渡し ParseResult を返す
- [x] fetch_xbrl_detail(): 注入 session は close() されない
- [x] fetch_xbrl_detail(): API エラー時に NseAPIError が伝播する
- [x] fetch_xbrl_detail(): パース失敗時に NseParseError が伝播する
- [x] Module exports: collectors/__init__.py に ShareholdingCollector が含まれる
"""

from unittest.mock import MagicMock, patch

import pytest

from market.nse.collectors import ShareholdingCollector
from market.nse.collectors.share_holding import ShareholdingCollector as _ShareholdingCollectorDirect
from market.nse.errors import NseAPIError, NseParseError
from market.nse.session import NseSession
from market.nse.types import CorporateShareHolding
from market.nse.xbrl import ParseResult, ShareholderRow

# =============================================================================
# Helper: create mock session and responses
# =============================================================================


def _make_corporate_shareholding_json(
    *,
    symbol: str = "RELIANCE",
) -> list[dict]:
    """Create a mock NSE /api/corporate-share-holdings-master JSON response."""
    return [
        {
            "symbol": symbol,
            "date": "31-Dec-2025",
            "pr_and_prgrp": "50.01",
            "public_val": "49.99",
            "employeeTrusts": "",
            "submissionDate": "15-Jan-2026",
            "broadcastDate": "16-Jan-2026",
            "xbrl": "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml",
        }
    ]


def _make_mock_session(
    *,
    response_json: dict | list | None = None,
    response_content: bytes | None = None,
) -> MagicMock:
    """Create a mock NseSession with pre-configured responses."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    if response_json is not None:
        mock_response.json.return_value = response_json
    elif response_content is not None:
        mock_response.content = response_content
    else:
        mock_response.json.return_value = _make_corporate_shareholding_json()
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


def _make_minimal_xbrl_bytes() -> bytes:
    """Return minimal XBRL bytes for ParseResult mocking."""
    return b'<?xml version="1.0"?><xbrl xmlns="http://www.bseindia.com/xbrl/shp/2022-09-30/in-bse-shp"></xbrl>'


# =============================================================================
# Tests: initialization
# =============================================================================


class TestShareholdingCollectorInit:
    def test_正常系_デフォルト値で初期化できる(self) -> None:
        collector = ShareholdingCollector()
        assert collector._session_instance is None

    def test_正常系_session_注入で初期化できる(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = ShareholdingCollector(session=mock_session)
        assert collector._session_instance is mock_session

    def test_正常系_DataCollector_ABCを継承していない(self) -> None:
        try:
            from market.base_collector import DataCollector
            assert not issubclass(ShareholdingCollector, DataCollector)
        except ImportError:
            pass  # DataCollector が存在しない場合はスキップ

    def test_正常系_NseCollectorMixinを継承している(self) -> None:
        from market.nse.collectors._base import NseCollectorMixin
        assert issubclass(ShareholdingCollector, NseCollectorMixin)


# =============================================================================
# Tests: fetch_shareholding - input validation
# =============================================================================


class TestFetchShareholdingValidation:
    def test_異常系_空文字列でValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="empty"):
            collector.fetch_shareholding("")

    def test_異常系_空白のみでValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="empty"):
            collector.fetch_shareholding("   ")

    def test_異常系_20文字超過でValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="20"):
            collector.fetch_shareholding("A" * 21)

    def test_異常系_無効文字でValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="invalid"):
            collector.fetch_shareholding("reliance")  # 小文字は不正

    def test_異常系_特殊文字でValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="invalid"):
            collector.fetch_shareholding("RELI@NCE")

    def test_正常系_ちょうど20文字でエラーなし(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json(symbol="A" * 20)
        )
        collector = ShareholdingCollector(session=mock_session)
        # 20文字大文字英字はバリデーション通過（APIコールが起きる）
        result = collector.fetch_shareholding("A" * 20)
        assert isinstance(result, list)

    def test_正常系_ハイフンとアンパサンドを含むシンボルでエラーなし(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json(symbol="M&M")
        )
        collector = ShareholdingCollector(session=mock_session)
        result = collector.fetch_shareholding("M&M")
        assert isinstance(result, list)


# =============================================================================
# Tests: fetch_shareholding - normal operation
# =============================================================================


class TestFetchShareholdingNormal:
    def test_正常系_CorporateShareHoldingリストを返す(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        collector = ShareholdingCollector(session=mock_session)
        result = collector.fetch_shareholding("RELIANCE")
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], CorporateShareHolding)

    def test_正常系_symbolが正しく設定される(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json(symbol="INFOSYS")
        )
        collector = ShareholdingCollector(session=mock_session)
        result = collector.fetch_shareholding("INFOSYS")
        assert result[0].symbol == "INFOSYS"

    def test_正常系_xbrl_urlが正しく設定される(self) -> None:
        expected_url = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        collector = ShareholdingCollector(session=mock_session)
        result = collector.fetch_shareholding("RELIANCE")
        assert result[0].xbrl_url == expected_url

    def test_正常系_正しいエンドポイントにリクエストされる(self) -> None:
        from market.nse.constants import CORPORATE_SHARE_HOLDINGS_ENDPOINT
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        collector = ShareholdingCollector(session=mock_session)
        collector.fetch_shareholding("RELIANCE")
        call_args = mock_session.get_with_retry.call_args
        assert CORPORATE_SHARE_HOLDINGS_ENDPOINT in call_args[0] or \
               CORPORATE_SHARE_HOLDINGS_ENDPOINT == call_args[0][0]

    def test_正常系_symbolパラメータがリクエストに含まれる(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        collector = ShareholdingCollector(session=mock_session)
        collector.fetch_shareholding("RELIANCE")
        call_kwargs = mock_session.get_with_retry.call_args[1]
        assert "params" in call_kwargs
        assert call_kwargs["params"].get("symbol") == "RELIANCE"

    def test_正常系_注入session_は_close_されない(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        collector = ShareholdingCollector(session=mock_session)
        collector.fetch_shareholding("RELIANCE")
        mock_session.close.assert_not_called()

    def test_正常系_内部生成sessionは_close_される(self) -> None:
        mock_new_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        with patch("market.nse.collectors._base.NseSession", return_value=mock_new_session):
            collector = ShareholdingCollector()
            collector.fetch_shareholding("RELIANCE")
            mock_new_session.close.assert_called_once()

    def test_正常系_空リストのレスポンスで空リストを返す(self) -> None:
        mock_session = _make_mock_session(response_json=[])
        collector = ShareholdingCollector(session=mock_session)
        result = collector.fetch_shareholding("RELIANCE")
        assert result == []


# =============================================================================
# Tests: fetch_xbrl_detail
# =============================================================================


class TestFetchXbrlDetail:
    def test_正常系_ParseResultを返す(self) -> None:
        xbrl_url = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"
        mock_session = _make_mock_session(response_content=_make_minimal_xbrl_bytes())
        collector = ShareholdingCollector(session=mock_session)

        expected_result = ParseResult(
            symbol="RELIANCE",
            as_on_date="2025-12-31",
            rows=(
                ShareholderRow(
                    symbol="RELIANCE",
                    company_name="Reliance Industries Limited",
                    report_date="2025-12-31",
                    category="PromoterAndPromoterGroup",
                    sub_category="",
                    is_category_total="true",
                ),
            ),
        )

        with patch("market.nse.collectors.share_holding.parse_xbrl", return_value=expected_result) as mock_parse:
            result = collector.fetch_xbrl_detail(xbrl_url)

        assert result is expected_result
        mock_parse.assert_called_once()

    def test_正常系_get_with_retryにxbrl_urlを渡す(self) -> None:
        xbrl_url = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"
        mock_session = _make_mock_session(response_content=_make_minimal_xbrl_bytes())
        collector = ShareholdingCollector(session=mock_session)

        mock_result = ParseResult()
        with patch("market.nse.collectors.share_holding.parse_xbrl", return_value=mock_result):
            collector.fetch_xbrl_detail(xbrl_url)

        call_args = mock_session.get_with_retry.call_args
        called_url = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
        assert called_url == xbrl_url

    def test_正常系_注入session_は_close_されない(self) -> None:
        xbrl_url = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"
        mock_session = _make_mock_session(response_content=_make_minimal_xbrl_bytes())
        collector = ShareholdingCollector(session=mock_session)

        with patch("market.nse.collectors.share_holding.parse_xbrl", return_value=ParseResult()):
            collector.fetch_xbrl_detail(xbrl_url)

        mock_session.close.assert_not_called()

    def test_正常系_内部生成sessionは_close_される(self) -> None:
        xbrl_url = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"
        mock_new_session = _make_mock_session(response_content=_make_minimal_xbrl_bytes())

        with patch("market.nse.collectors._base.NseSession", return_value=mock_new_session):
            with patch("market.nse.collectors.share_holding.parse_xbrl", return_value=ParseResult()):
                collector = ShareholdingCollector()
                collector.fetch_xbrl_detail(xbrl_url)
                mock_new_session.close.assert_called_once()

    def test_異常系_NseAPIError_が伝播する(self) -> None:
        xbrl_url = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"
        mock_session = MagicMock(spec=NseSession)
        mock_session.get_with_retry.side_effect = NseAPIError(
            "HTTP 500",
            url=xbrl_url,
            status_code=500,
            response_body="Internal Server Error",
        )
        collector = ShareholdingCollector(session=mock_session)

        with pytest.raises(NseAPIError):
            collector.fetch_xbrl_detail(xbrl_url)

    def test_異常系_NseParseError_が伝播する(self) -> None:
        xbrl_url = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"
        mock_session = _make_mock_session(response_content=b"<invalid>xml</invalid>")
        collector = ShareholdingCollector(session=mock_session)

        with patch(
            "market.nse.collectors.share_holding.parse_xbrl",
            side_effect=NseParseError("namespace mismatch", raw_data=None, field="namespace"),
        ):
            with pytest.raises(NseParseError):
                collector.fetch_xbrl_detail(xbrl_url)


# =============================================================================
# Tests: module exports
# =============================================================================


class TestModuleExports:
    def test_正常系_collectors_initにShareholdingCollectorが含まれる(self) -> None:
        from market.nse import collectors
        assert hasattr(collectors, "ShareholdingCollector")
        assert "ShareholdingCollector" in collectors.__all__

    def test_正常系_market_nse_initからインポートできる(self) -> None:
        from market.nse import (
            CorporateShareHolding,
            ShareholdingCollector,
        )
        assert ShareholdingCollector is not None
        assert CorporateShareHolding is not None

    def test_正常系_xbrl型をmarket_nse_initからインポートできる(self) -> None:
        from market.nse import (
            ContextInfo,
            ParseResult,
            ShareholderRow,
            parse_xbrl,
        )
        assert parse_xbrl is not None
        assert ParseResult is not None
        assert ShareholderRow is not None
        assert ContextInfo is not None

    def test_正常系_parse_corporate_shareholdingをmarket_nse_initからインポートできる(self) -> None:
        from market.nse import parse_corporate_shareholding
        assert parse_corporate_shareholding is not None
