"""Unit tests for market.etfcom.collectors.HistoricalFundFlowsCollector.

HistoricalFundFlowsCollector の動作を検証するテストスイート。
REST API ベースのヒストリカルファンドフロー取得機能を対象とする。

Test TODO List:
- [x] HistoricalFundFlowsCollector: デフォルト値で初期化
- [x] HistoricalFundFlowsCollector: カスタム config で初期化
- [x] HistoricalFundFlowsCollector: session を注入できる
- [x] HistoricalFundFlowsCollector: DataCollector を継承していること
- [x] HistoricalFundFlowsCollector: name プロパティ
- [x] HistoricalFundFlowsCollector: browser パラメータなし
- [x] fetch(): ticker 指定で DataFrame を返すこと
- [x] fetch(): DataFrame に必須カラムが含まれること
- [x] fetch(): ticker 未指定で空 DataFrame
- [x] fetch_tickers(): DataFrame を返すこと
- [x] fetch_tickers(): DataFrame に必須カラムが含まれること
- [x] _resolve_fund_id(): ticker からfund_id を解決すること
- [x] _resolve_fund_id(): インメモリキャッシュが機能すること
- [x] _resolve_fund_id(): 不明ティッカーで ETFComAPIError
- [x] _fetch_fund_flows(): fund_id と ticker で raw records を取得すること
- [x] _fetch_fund_flows(): API エラー時に ETFComAPIError
- [x] _parse_response(): camelCase を snake_case に変換すること
- [x] _parse_response(): 日付フィルタリングが機能すること
- [x] _parse_response(): 日付ソート（昇順）が機能すること
- [x] _parse_response(): 空レコードで空 DataFrame
- [x] validate(): 必須カラム存在で True
- [x] validate(): 空 DataFrame で False
- [x] validate(): 必須カラムなしで False
- [x] fetch_multiple(): 複数ティッカーを逐次取得すること
- [x] __all__ に HistoricalFundFlowsCollector がエクスポート
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest

from market.base_collector import DataCollector
from market.etfcom.errors import ETFComAPIError
from market.etfcom.types import RetryConfig, ScrapingConfig

# =============================================================================
# Sample API response data
# =============================================================================

SAMPLE_TICKERS_RESPONSE: list[dict[str, object]] = [
    {
        "fundId": 1,
        "ticker": "SPY",
        "fundName": "SPDR S&P 500 ETF Trust",
        "issuer": "State Street",
        "assetClass": "Equity",
        "inceptionDate": "1993-01-22",
    },
    {
        "fundId": 2,
        "ticker": "VOO",
        "fundName": "Vanguard S&P 500 ETF",
        "issuer": "Vanguard",
        "assetClass": "Equity",
        "inceptionDate": "2010-09-07",
    },
    {
        "fundId": 3,
        "ticker": "QQQ",
        "fundName": "Invesco QQQ Trust",
        "issuer": "Invesco",
        "assetClass": "Equity",
        "inceptionDate": "1999-03-10",
    },
]

SAMPLE_FUND_FLOWS_RESPONSE: dict[str, object] = {
    "results": [
        {
            "navDate": "2025-09-10",
            "nav": 450.25,
            "navChange": 2.15,
            "navChangePercent": 0.48,
            "premiumDiscount": -0.02,
            "fundFlows": 2787590000.0,
            "sharesOutstanding": 920000000.0,
            "aum": 414230000000.0,
        },
        {
            "navDate": "2025-09-09",
            "nav": 448.10,
            "navChange": -1.30,
            "navChangePercent": -0.29,
            "premiumDiscount": 0.01,
            "fundFlows": -1234560000.0,
            "sharesOutstanding": 919500000.0,
            "aum": 411950000000.0,
        },
        {
            "navDate": "2025-09-08",
            "nav": 449.40,
            "navChange": 0.50,
            "navChangePercent": 0.11,
            "premiumDiscount": 0.00,
            "fundFlows": 500000000.0,
            "sharesOutstanding": 919000000.0,
            "aum": 412800000000.0,
        },
    ],
}


# =============================================================================
# Helper to build mock session
# =============================================================================


def _make_mock_session(
    *,
    tickers_response: list[dict[str, object]] | None = None,
    fund_flows_response: dict[str, object] | None = None,
    get_status: int = 200,
    post_status: int = 200,
) -> MagicMock:
    """Build a MagicMock simulating ETFComSession for HistoricalFundFlowsCollector.

    Parameters
    ----------
    tickers_response : list[dict[str, object]] | None
        JSON body for GET /tickers endpoint.
    fund_flows_response : dict[str, object] | None
        JSON body for POST /fund-flows-query endpoint.
    get_status : int
        HTTP status code for GET responses.
    post_status : int
        HTTP status code for POST responses.

    Returns
    -------
    MagicMock
        A mock session with get_with_retry and post_with_retry configured.
    """
    session = MagicMock()

    # GET response (tickers endpoint)
    get_resp = MagicMock()
    get_resp.status_code = get_status
    if tickers_response is not None:
        get_resp.json.return_value = tickers_response
        get_resp.text = json.dumps(tickers_response)
    else:
        get_resp.json.return_value = SAMPLE_TICKERS_RESPONSE
        get_resp.text = json.dumps(SAMPLE_TICKERS_RESPONSE)
    session.get.return_value = get_resp
    session.get_with_retry.return_value = get_resp

    # POST response (fund-flows-query endpoint)
    post_resp = MagicMock()
    post_resp.status_code = post_status
    if fund_flows_response is not None:
        post_resp.json.return_value = fund_flows_response
        post_resp.text = json.dumps(fund_flows_response)
    else:
        post_resp.json.return_value = SAMPLE_FUND_FLOWS_RESPONSE
        post_resp.text = json.dumps(SAMPLE_FUND_FLOWS_RESPONSE)
    session.post.return_value = post_resp
    session.post_with_retry.return_value = post_resp

    session.close.return_value = None
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)

    return session


# =============================================================================
# Initialization tests
# =============================================================================


class TestHistoricalFundFlowsCollectorInit:
    """HistoricalFundFlowsCollector 初期化のテスト。"""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """デフォルトの config で初期化されること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        assert collector._config is not None
        assert isinstance(collector._config, ScrapingConfig)
        assert collector._retry_config is not None
        assert isinstance(collector._retry_config, RetryConfig)

    def test_正常系_カスタムconfigで初期化できる(self) -> None:
        """カスタム ScrapingConfig と RetryConfig で初期化されること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        config = ScrapingConfig(polite_delay=5.0)
        retry_config = RetryConfig(max_attempts=5)
        collector = HistoricalFundFlowsCollector(
            config=config, retry_config=retry_config
        )

        assert collector._config.polite_delay == 5.0
        assert collector._retry_config.max_attempts == 5

    def test_正常系_sessionを注入できる(self) -> None:
        """外部から session を注入できること（DI パターン）。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = MagicMock()
        collector = HistoricalFundFlowsCollector(session=mock_session)

        assert collector._session_instance is mock_session

    def test_正常系_DataCollectorを継承している(self) -> None:
        """HistoricalFundFlowsCollector が DataCollector を継承していること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        assert isinstance(collector, DataCollector)

    def test_正常系_nameプロパティが正しい値を返す(self) -> None:
        """name プロパティが 'HistoricalFundFlowsCollector' を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        assert collector.name == "HistoricalFundFlowsCollector"

    def test_正常系_browserパラメータなし(self) -> None:
        """REST API ベースのため browser パラメータを持たないこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        assert not hasattr(collector, "_browser_instance")


# =============================================================================
# fetch() tests
# =============================================================================


class TestHistoricalFundFlowsFetch:
    """HistoricalFundFlowsCollector.fetch() のテスト。"""

    def test_正常系_ticker指定でDataFrameを返す(self) -> None:
        """fetch(ticker='SPY') が DataFrame を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch(ticker="SPY")

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_正常系_DataFrameに必須カラムが含まれること(self) -> None:
        """返却 DataFrame に 9 つの必須カラムが含まれること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch(ticker="SPY")

        expected_columns = {
            "ticker",
            "nav_date",
            "nav",
            "nav_change",
            "nav_change_percent",
            "premium_discount",
            "fund_flows",
            "shares_outstanding",
            "aum",
        }
        assert expected_columns.issubset(set(df.columns))

    def test_正常系_ticker列に指定したtickerが含まれること(self) -> None:
        """全行の ticker 列に指定したティッカーが入っていること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch(ticker="SPY")

        assert all(df["ticker"] == "SPY")

    def test_正常系_ticker未指定で空DataFrame(self) -> None:
        """ticker を指定しない場合、空 DataFrame を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()

        df = collector.fetch()

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_正常系_start_dateでフィルタリングされること(self) -> None:
        """start_date を指定すると、それ以降のデータのみ返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch(ticker="SPY", start_date="2025-09-09")

        # Should include 2025-09-09 and 2025-09-10, exclude 2025-09-08
        assert len(df) == 2
        dates = df["nav_date"].tolist()
        assert date(2025, 9, 8) not in dates

    def test_正常系_end_dateでフィルタリングされること(self) -> None:
        """end_date を指定すると、それ以前のデータのみ返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch(ticker="SPY", end_date="2025-09-09")

        # Should include 2025-09-08 and 2025-09-09, exclude 2025-09-10
        assert len(df) == 2
        dates = df["nav_date"].tolist()
        assert date(2025, 9, 10) not in dates


# =============================================================================
# fetch_tickers() tests
# =============================================================================


class TestHistoricalFundFlowsFetchTickers:
    """HistoricalFundFlowsCollector.fetch_tickers() のテスト。"""

    def test_正常系_DataFrameを返すこと(self) -> None:
        """fetch_tickers() が DataFrame を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch_tickers()

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_正常系_必須カラムが含まれること(self) -> None:
        """返却 DataFrame に ticker, fund_id, name 等のカラムが含まれること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch_tickers()

        expected_columns = {"ticker", "fund_id", "name"}
        assert expected_columns.issubset(set(df.columns))

    def test_正常系_3件のティッカーを返すこと(self) -> None:
        """サンプルデータの3件分が返ること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch_tickers()

        assert len(df) == 3
        assert set(df["ticker"].tolist()) == {"SPY", "VOO", "QQQ"}


# =============================================================================
# _resolve_fund_id() tests
# =============================================================================


class TestResolveFundId:
    """HistoricalFundFlowsCollector._resolve_fund_id() のテスト。"""

    def test_正常系_tickerからfund_idを解決する(self) -> None:
        """既知の ticker から fund_id を解決できること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        fund_id = collector._resolve_fund_id("SPY")

        assert fund_id == 1

    def test_正常系_インメモリキャッシュが機能すること(self) -> None:
        """2回目の呼び出しでキャッシュを使用し、API を再呼び出ししないこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        # 1st call: should hit API
        fund_id_1 = collector._resolve_fund_id("SPY")
        # 2nd call: should use cache
        fund_id_2 = collector._resolve_fund_id("SPY")

        assert fund_id_1 == fund_id_2 == 1
        # API should only be called once (for the first _resolve_fund_id call)
        assert mock_session.get_with_retry.call_count == 1

    def test_異常系_不明ティッカーでETFComAPIError(self) -> None:
        """存在しないティッカーで ETFComAPIError が送出されること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        with pytest.raises(ETFComAPIError, match="UNKNOWN"):
            collector._resolve_fund_id("UNKNOWN")


# =============================================================================
# _fetch_fund_flows() tests
# =============================================================================


class TestFetchFundFlows:
    """HistoricalFundFlowsCollector._fetch_fund_flows() のテスト。"""

    def test_正常系_rawレコードを取得する(self) -> None:
        """fund_id と ticker で raw records を取得すること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        records = collector._fetch_fund_flows(fund_id=1, ticker="SPY")

        assert isinstance(records, list)
        assert len(records) == 3

    def test_正常系_POSTリクエストにfundIdが含まれること(self) -> None:
        """POST リクエストのボディに fundId が含まれること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        collector._fetch_fund_flows(fund_id=1, ticker="SPY")

        # Verify POST was called with correct payload
        mock_session.post_with_retry.assert_called_once()
        call_kwargs = mock_session.post_with_retry.call_args
        assert call_kwargs is not None

    def test_異常系_APIエラー時にETFComAPIError(self) -> None:
        """POST が非 200 ステータスを返した場合、ETFComAPIError が送出されること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        post_resp = MagicMock()
        post_resp.status_code = 500
        post_resp.text = '{"error": "Internal Server Error"}'
        post_resp.json.return_value = {"error": "Internal Server Error"}
        mock_session.post_with_retry.return_value = post_resp

        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        with pytest.raises(ETFComAPIError):
            collector._fetch_fund_flows(fund_id=1, ticker="SPY")


# =============================================================================
# _parse_response() tests
# =============================================================================


class TestParseResponse:
    """HistoricalFundFlowsCollector._parse_response() のテスト。"""

    def test_正常系_camelCaseをsnake_caseに変換する(self) -> None:
        """camelCase キーが snake_case に変換されること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        records: list[dict[str, Any]] = [
            {
                "navDate": "2025-09-10",
                "nav": 450.25,
                "navChange": 2.15,
                "navChangePercent": 0.48,
                "premiumDiscount": -0.02,
                "fundFlows": 2787590000.0,
                "sharesOutstanding": 920000000.0,
                "aum": 414230000000.0,
            },
        ]

        df = collector._parse_response(records, ticker="SPY")

        assert "nav_date" in df.columns
        assert "nav_change" in df.columns
        assert "nav_change_percent" in df.columns
        assert "premium_discount" in df.columns
        assert "fund_flows" in df.columns
        assert "shares_outstanding" in df.columns
        # Original camelCase keys should NOT be present
        assert "navDate" not in df.columns
        assert "navChange" not in df.columns
        assert "fundFlows" not in df.columns

    def test_正常系_日付フィルタリングが機能する(self) -> None:
        """start_date / end_date でレコードがフィルタリングされること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        records: list[dict[str, Any]] = [
            {
                "navDate": "2025-09-10",
                "nav": 450.25,
                "navChange": 2.15,
                "navChangePercent": 0.48,
                "premiumDiscount": -0.02,
                "fundFlows": 2787590000.0,
                "sharesOutstanding": 920000000.0,
                "aum": 414230000000.0,
            },
            {
                "navDate": "2025-09-09",
                "nav": 448.10,
                "navChange": -1.30,
                "navChangePercent": -0.29,
                "premiumDiscount": 0.01,
                "fundFlows": -1234560000.0,
                "sharesOutstanding": 919500000.0,
                "aum": 411950000000.0,
            },
            {
                "navDate": "2025-09-08",
                "nav": 449.40,
                "navChange": 0.50,
                "navChangePercent": 0.11,
                "premiumDiscount": 0.00,
                "fundFlows": 500000000.0,
                "sharesOutstanding": 919000000.0,
                "aum": 412800000000.0,
            },
        ]

        df = collector._parse_response(
            records,
            ticker="SPY",
            start_date="2025-09-09",
            end_date="2025-09-10",
        )

        assert len(df) == 2
        dates = df["nav_date"].tolist()
        assert date(2025, 9, 8) not in dates

    def test_正常系_日付ソート昇順が機能する(self) -> None:
        """レコードが nav_date の昇順でソートされること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        records: list[dict[str, Any]] = [
            {
                "navDate": "2025-09-10",
                "nav": 450.25,
                "navChange": 2.15,
                "navChangePercent": 0.48,
                "premiumDiscount": -0.02,
                "fundFlows": 2787590000.0,
                "sharesOutstanding": 920000000.0,
                "aum": 414230000000.0,
            },
            {
                "navDate": "2025-09-08",
                "nav": 449.40,
                "navChange": 0.50,
                "navChangePercent": 0.11,
                "premiumDiscount": 0.00,
                "fundFlows": 500000000.0,
                "sharesOutstanding": 919000000.0,
                "aum": 412800000000.0,
            },
            {
                "navDate": "2025-09-09",
                "nav": 448.10,
                "navChange": -1.30,
                "navChangePercent": -0.29,
                "premiumDiscount": 0.01,
                "fundFlows": -1234560000.0,
                "sharesOutstanding": 919500000.0,
                "aum": 411950000000.0,
            },
        ]

        df = collector._parse_response(records, ticker="SPY")

        dates = df["nav_date"].tolist()
        assert dates == [date(2025, 9, 8), date(2025, 9, 9), date(2025, 9, 10)]

    def test_正常系_空レコードで空DataFrame(self) -> None:
        """空のレコードリストで空 DataFrame を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()

        df = collector._parse_response([], ticker="SPY")

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_正常系_ticker列が追加されること(self) -> None:
        """パース結果に ticker 列が追加されること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        records: list[dict[str, Any]] = [
            {
                "navDate": "2025-09-10",
                "nav": 450.25,
                "navChange": 2.15,
                "navChangePercent": 0.48,
                "premiumDiscount": -0.02,
                "fundFlows": 2787590000.0,
                "sharesOutstanding": 920000000.0,
                "aum": 414230000000.0,
            },
        ]

        df = collector._parse_response(records, ticker="SPY")

        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "SPY"

    def test_正常系_null値がNoneに変換されること(self) -> None:
        """API の null 値が None / NaN に変換されること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        records: list[dict[str, Any]] = [
            {
                "navDate": "2025-09-10",
                "nav": None,
                "navChange": None,
                "navChangePercent": None,
                "premiumDiscount": None,
                "fundFlows": None,
                "sharesOutstanding": None,
                "aum": None,
            },
        ]

        df = collector._parse_response(records, ticker="SPY")

        assert len(df) == 1
        assert pd.isna(df["nav"].iloc[0])
        assert pd.isna(df["fund_flows"].iloc[0])


# =============================================================================
# validate() tests
# =============================================================================


class TestHistoricalFundFlowsValidate:
    """HistoricalFundFlowsCollector.validate() のテスト。"""

    def test_正常系_必須カラム存在でTrue(self) -> None:
        """必須カラムが全て存在する DataFrame で True を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        df = pd.DataFrame(
            {
                "ticker": ["SPY"],
                "nav_date": [date(2025, 9, 10)],
                "nav": [450.25],
                "nav_change": [2.15],
                "nav_change_percent": [0.48],
                "premium_discount": [-0.02],
                "fund_flows": [2787590000.0],
                "shares_outstanding": [920000000.0],
                "aum": [414230000000.0],
            }
        )

        assert collector.validate(df) is True

    def test_異常系_空DataFrameでFalse(self) -> None:
        """空 DataFrame で False を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        df = pd.DataFrame()

        assert collector.validate(df) is False

    def test_異常系_必須カラムなしでFalse(self) -> None:
        """必須カラムがない DataFrame で False を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()
        df = pd.DataFrame({"some_column": [1, 2, 3]})

        assert collector.validate(df) is False


# =============================================================================
# fetch_multiple() tests
# =============================================================================


class TestHistoricalFundFlowsFetchMultiple:
    """HistoricalFundFlowsCollector.fetch_multiple() のテスト。"""

    def test_正常系_複数ティッカーを逐次取得する(self) -> None:
        """fetch_multiple() が複数ティッカーのデータを結合して返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch_multiple(tickers=["SPY", "VOO"])

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        # Should have data for both tickers
        assert set(df["ticker"].unique()) == {"SPY", "VOO"}

    def test_正常系_空のtickersリストで空DataFrame(self) -> None:
        """空のティッカーリストで空 DataFrame を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()

        df = collector.fetch_multiple(tickers=[])

        assert isinstance(df, pd.DataFrame)
        assert df.empty


# =============================================================================
# __all__ export tests
# =============================================================================


class TestHistoricalFundFlowsExports:
    """__all__ エクスポートのテスト。"""

    def test_正常系_HistoricalFundFlowsCollectorがエクスポートされている(self) -> None:
        """__all__ に HistoricalFundFlowsCollector が含まれていること。"""
        from market.etfcom.collectors import __all__

        assert "HistoricalFundFlowsCollector" in __all__
