"""Unit tests for market.nse.collectors.share_holding module.

ShareholdingCollector の動作を検証するユニットテストスイート。
test_corporate_collector.py + test_shareholding.py のパターンを踏襲し、
2 メソッド + 初期化の全経路を網羅する。

Test TODO List:
- [x] ShareholdingCollector: デフォルト初期化（session なし）
- [x] ShareholdingCollector: DI パターンで session 注入
- [x] ShareholdingCollector: ABC 非継承確認
- [x] fetch_shareholding(): CorporateShareHolding リストを正常取得
- [x] fetch_shareholding(): 正しいエンドポイント呼び出し
- [x] fetch_shareholding(): symbol バリデーション - 空文字
- [x] fetch_shareholding(): symbol バリデーション - 20 文字超
- [x] fetch_shareholding(): symbol バリデーション - regex 不一致
- [x] fetch_shareholding(): 空レスポンスで空リスト
- [x] fetch_shareholding(): 注入セッションは close しない
- [x] fetch_xbrl_detail(): 正常系 ParseResult 返却
- [x] fetch_xbrl_detail(): URL ダウンロード失敗時 NseAPIError 伝播
- [x] fetch_xbrl_detail(): パース失敗時 NseParseError 伝播
- [x] fetch_xbrl_detail(): 注入セッションは close しない
"""

from unittest.mock import MagicMock, patch

import pytest

from market.nse.collectors.share_holding import ShareholdingCollector
from market.nse.errors import NseAPIError, NseParseError
from market.nse.session import NseSession
from market.nse.types import CorporateShareHolding
from market.nse.xbrl import ParseResult

# =============================================================================
# Helper: session and response factory
# =============================================================================


def _make_corporate_shareholding_json(*, symbol: str = "RELIANCE") -> list[dict]:
    """Create a minimal NSE /api/corporate-share-holdings-master JSON response."""
    return [
        {
            "symbol": symbol,
            "date": "31-Dec-2025",
            "pr_and_prgrp": "50.01",
            "public_val": "49.99",
            "employeeTrusts": "",
            "submissionDate": "15-Jan-2026",
            "broadcastDate": "16-Jan-2026",
            "xbrl": f"https://nsearchives.nseindia.com/corporate/xbrl/{symbol}.xml",
        }
    ]


def _make_mock_session(
    *,
    response_json: dict | list | None = None,
    response_content: bytes | None = None,
) -> MagicMock:
    """Create a mock NseSession with pre-configured get_with_retry response."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    mock_response.status_code = 200
    if response_content is not None:
        mock_response.content = response_content
        mock_response.json.return_value = None
    else:
        mock_response.json.return_value = (
            response_json
            if response_json is not None
            else _make_corporate_shareholding_json()
        )
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


# =============================================================================
# TestShareholdingCollectorInit
# =============================================================================


class TestShareholdingCollectorInit:
    """Phase 0: 初期化パス（3 tests）."""

    def test_正常系_デフォルト初期化でsession_instanceはNone(self) -> None:
        collector = ShareholdingCollector()
        assert collector._session_instance is None

    def test_正常系_session注入で_session_instanceが設定される(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = ShareholdingCollector(session=mock_session)
        assert collector._session_instance is mock_session

    def test_正常系_DataCollector_ABCを継承していない(self) -> None:
        """ShareholdingCollector は DataCollector ABC の外にあること。"""
        try:
            from market.base_collector import DataCollector

            assert not issubclass(ShareholdingCollector, DataCollector)
        except ImportError:
            pass  # DataCollector 未存在環境ではスキップ


# =============================================================================
# TestFetchShareholding
# =============================================================================


class TestFetchShareholding:
    """fetch_shareholding() の正常系・バリデーション・エッジケース（6 tests）."""

    # --- 正常系 ---

    def test_正常系_CorporateShareHoldingリストを返す(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json(symbol="RELIANCE")
        )
        collector = ShareholdingCollector(session=mock_session)
        result = collector.fetch_shareholding("RELIANCE")
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], CorporateShareHolding)
        assert result[0].symbol == "RELIANCE"

    def test_正常系_正しいエンドポイントにリクエストされる(self) -> None:
        from market.nse.constants import CORPORATE_SHARE_HOLDINGS_ENDPOINT

        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        collector = ShareholdingCollector(session=mock_session)
        collector.fetch_shareholding("RELIANCE")
        call_args = mock_session.get_with_retry.call_args
        called_url = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
        assert called_url == CORPORATE_SHARE_HOLDINGS_ENDPOINT

    def test_正常系_注入sessionはcloseされない(self) -> None:
        mock_session = _make_mock_session(
            response_json=_make_corporate_shareholding_json()
        )
        collector = ShareholdingCollector(session=mock_session)
        collector.fetch_shareholding("RELIANCE")
        mock_session.close.assert_not_called()

    def test_正常系_空レスポンスで空リストを返す(self) -> None:
        mock_session = _make_mock_session(response_json=[])
        collector = ShareholdingCollector(session=mock_session)
        result = collector.fetch_shareholding("RELIANCE")
        assert result == []

    # --- バリデーション 3 段階 ---

    def test_異常系_空文字列でValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="empty"):
            collector.fetch_shareholding("")

    def test_異常系_20文字超でValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="20"):
            collector.fetch_shareholding("A" * 21)

    def test_異常系_regex不一致でValueError(self) -> None:
        collector = ShareholdingCollector()
        with pytest.raises(ValueError, match="invalid"):
            collector.fetch_shareholding("reliance")  # 小文字は不正


# =============================================================================
# TestFetchXbrlDetail
# =============================================================================


class TestFetchXbrlDetail:
    """fetch_xbrl_detail() の正常系・例外伝播（4 tests）."""

    _XBRL_URL = "https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"

    def test_正常系_ParseResultを返す(self) -> None:
        mock_session = _make_mock_session(
            response_content=b'<?xml version="1.0"?><xbrl/>'
        )
        collector = ShareholdingCollector(session=mock_session)

        expected = ParseResult()
        with patch(
            "market.nse.collectors.share_holding.parse_xbrl",
            return_value=expected,
        ) as mock_parse:
            result = collector.fetch_xbrl_detail(self._XBRL_URL)

        assert result is expected
        mock_parse.assert_called_once()

    def test_正常系_注入sessionはcloseされない(self) -> None:
        mock_session = _make_mock_session(
            response_content=b'<?xml version="1.0"?><xbrl/>'
        )
        collector = ShareholdingCollector(session=mock_session)

        with patch(
            "market.nse.collectors.share_holding.parse_xbrl",
            return_value=ParseResult(),
        ):
            collector.fetch_xbrl_detail(self._XBRL_URL)

        mock_session.close.assert_not_called()

    def test_異常系_ダウンロード失敗でNseAPIErrorが伝播する(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        mock_session.get_with_retry.side_effect = NseAPIError(
            "HTTP 500",
            url=self._XBRL_URL,
            status_code=500,
            response_body="Internal Server Error",
        )
        collector = ShareholdingCollector(session=mock_session)

        with pytest.raises(NseAPIError):
            collector.fetch_xbrl_detail(self._XBRL_URL)

    def test_異常系_パース失敗でNseParseErrorが伝播する(self) -> None:
        mock_session = _make_mock_session(response_content=b"<invalid/>")
        collector = ShareholdingCollector(session=mock_session)

        with (
            patch(
                "market.nse.collectors.share_holding.parse_xbrl",
                side_effect=NseParseError(
                    "namespace mismatch", raw_data=None, field="namespace"
                ),
            ),
            pytest.raises(NseParseError),
        ):
            collector.fetch_xbrl_detail(self._XBRL_URL)
