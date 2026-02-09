"""Unit tests for HistoricalFundFlowsCollector file cache and fetch_multiple parallelization.

HistoricalFundFlowsCollector のファイルキャッシュ（TTL 付き）と
fetch_multiple の asyncio.Semaphore 並列化を検証するテストスイート。

Test TODO List:
- [x] _load_ticker_cache(): キャッシュファイルが存在しない場合は空 dict を返す
- [x] _load_ticker_cache(): 有効なキャッシュファイルを正しく読み込む
- [x] _save_ticker_cache(): キャッシュファイルを JSON で保存する
- [x] _save_ticker_cache(): ディレクトリが存在しない場合は作成する
- [x] _is_cache_valid(): TTL 内のキャッシュは有効
- [x] _is_cache_valid(): TTL 超過のキャッシュは無効
- [x] _is_cache_valid(): cached_at が存在しない場合は無効
- [x] _resolve_fund_id(): ファイルキャッシュ→インメモリ→API の3段階で解決
- [x] _resolve_fund_id(): ファイルキャッシュヒット時に API を呼ばない
- [x] fetch_multiple(): 並列度制限付きで動作する
- [x] fetch_multiple(): max_concurrency パラメータで並列度を制御できる
- [x] fetch_multiple(): 公開 IF が同期である
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pandas as pd
import pytest

from market.etfcom.constants import DEFAULT_TICKER_CACHE_TTL_HOURS
from market.etfcom.types import ScrapingConfig

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Sample data
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
    ],
}


# =============================================================================
# Helper to build mock session
# =============================================================================


def _make_mock_session(
    *,
    tickers_response: list[dict[str, object]] | None = None,
    fund_flows_response: dict[str, object] | None = None,
) -> MagicMock:
    """Build a MagicMock simulating ETFComSession."""
    session = MagicMock()

    get_resp = MagicMock()
    get_resp.status_code = 200
    tickers = tickers_response or SAMPLE_TICKERS_RESPONSE
    get_resp.json.return_value = tickers
    get_resp.text = json.dumps(tickers)
    session.get.return_value = get_resp
    session.get_with_retry.return_value = get_resp

    post_resp = MagicMock()
    post_resp.status_code = 200
    flows = fund_flows_response or SAMPLE_FUND_FLOWS_RESPONSE
    post_resp.json.return_value = flows
    post_resp.text = json.dumps(flows)
    session.post.return_value = post_resp
    session.post_with_retry.return_value = post_resp

    session.close.return_value = None
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)

    return session


# =============================================================================
# _load_ticker_cache() tests
# =============================================================================


class TestLoadTickerCache:
    """_load_ticker_cache() のテスト。"""

    def test_正常系_キャッシュファイルが存在しない場合は空dictを返す(
        self, tmp_path: Path
    ) -> None:
        """キャッシュファイルが存在しない場合、空 dict を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector(
            cache_dir=str(tmp_path),
        )

        cache = collector._load_ticker_cache()

        assert cache == {}

    def test_正常系_有効なキャッシュファイルを正しく読み込む(
        self, tmp_path: Path
    ) -> None:
        """有効な JSON キャッシュファイルを読み込んで dict を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        # Write a valid cache file
        cache_file = tmp_path / "tickers.json"
        cache_data = {
            "cached_at": datetime.now(tz=timezone.utc).isoformat(),
            "tickers": {"SPY": 1, "VOO": 2},
        }
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        collector = HistoricalFundFlowsCollector(
            cache_dir=str(tmp_path),
        )

        cache = collector._load_ticker_cache()

        assert cache == cache_data


# =============================================================================
# _save_ticker_cache() tests
# =============================================================================


class TestSaveTickerCache:
    """_save_ticker_cache() のテスト。"""

    def test_正常系_キャッシュファイルをJSONで保存する(self, tmp_path: Path) -> None:
        """インメモリキャッシュを JSON ファイルに永続化すること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector(
            cache_dir=str(tmp_path),
        )
        collector._fund_id_cache = {"SPY": 1, "VOO": 2}

        collector._save_ticker_cache()

        cache_file = tmp_path / "tickers.json"
        assert cache_file.exists()

        saved_data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert saved_data["tickers"] == {"SPY": 1, "VOO": 2}
        assert "cached_at" in saved_data

    def test_正常系_ディレクトリが存在しない場合は作成する(
        self, tmp_path: Path
    ) -> None:
        """キャッシュディレクトリが存在しない場合、自動作成すること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        nested_dir = tmp_path / "sub" / "dir"
        collector = HistoricalFundFlowsCollector(
            cache_dir=str(nested_dir),
        )
        collector._fund_id_cache = {"SPY": 1}

        collector._save_ticker_cache()

        assert nested_dir.exists()
        assert (nested_dir / "tickers.json").exists()


# =============================================================================
# _is_cache_valid() tests
# =============================================================================


class TestIsCacheValid:
    """_is_cache_valid() のテスト。"""

    def test_正常系_TTL内のキャッシュは有効(self) -> None:
        """TTL 内のキャッシュデータで True を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()

        cache_data = {
            "cached_at": datetime.now(tz=timezone.utc).isoformat(),
            "tickers": {"SPY": 1},
        }

        assert collector._is_cache_valid(cache_data) is True

    def test_正常系_TTL超過のキャッシュは無効(self) -> None:
        """TTL を超過したキャッシュデータで False を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()

        # Create a cache timestamp older than TTL
        old_time = datetime.now(tz=timezone.utc).timestamp() - (
            DEFAULT_TICKER_CACHE_TTL_HOURS * 3600 + 1
        )
        old_dt = datetime.fromtimestamp(old_time, tz=timezone.utc)
        cache_data = {
            "cached_at": old_dt.isoformat(),
            "tickers": {"SPY": 1},
        }

        assert collector._is_cache_valid(cache_data) is False

    def test_異常系_cached_atが存在しない場合は無効(self) -> None:
        """cached_at キーが存在しないキャッシュデータで False を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()

        cache_data: dict[str, Any] = {
            "tickers": {"SPY": 1},
        }

        assert collector._is_cache_valid(cache_data) is False


# =============================================================================
# _resolve_fund_id() with file cache tests
# =============================================================================


class TestResolveFundIdWithFileCache:
    """_resolve_fund_id() ファイルキャッシュ連携のテスト。"""

    def test_正常系_ファイルキャッシュヒット時にAPIを呼ばない(
        self, tmp_path: Path
    ) -> None:
        """ファイルキャッシュが有効な場合、API を呼び出さないこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        # Write a valid cache file
        cache_file = tmp_path / "tickers.json"
        cache_data = {
            "cached_at": datetime.now(tz=timezone.utc).isoformat(),
            "tickers": {"SPY": 1, "VOO": 2},
        }
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        mock_session = _make_mock_session()
        collector = HistoricalFundFlowsCollector(
            session=mock_session,
            cache_dir=str(tmp_path),
            config=ScrapingConfig(polite_delay=0.0, delay_jitter=0.0),
        )

        fund_id = collector._resolve_fund_id("SPY")

        assert fund_id == 1
        # API should NOT be called because file cache hit
        mock_session.get_with_retry.assert_not_called()

    def test_正常系_3段階解決_ファイルキャッシュ_インメモリ_API(
        self, tmp_path: Path
    ) -> None:
        """ファイルキャッシュ→インメモリ→API の 3 段階で解決すること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        collector = HistoricalFundFlowsCollector(
            session=mock_session,
            cache_dir=str(tmp_path),
            config=ScrapingConfig(polite_delay=0.0, delay_jitter=0.0),
        )

        # 1st call: no file cache, no in-memory cache -> API call
        fund_id = collector._resolve_fund_id("SPY")
        assert fund_id == 1
        assert mock_session.get_with_retry.call_count == 1

        # 2nd call: in-memory cache hit -> no API call
        fund_id = collector._resolve_fund_id("SPY")
        assert fund_id == 1
        assert mock_session.get_with_retry.call_count == 1  # still 1

        # 3rd: create new collector with file cache from previous
        collector2 = HistoricalFundFlowsCollector(
            session=mock_session,
            cache_dir=str(tmp_path),
            config=ScrapingConfig(polite_delay=0.0, delay_jitter=0.0),
        )

        # File cache was saved by first collector, so no API call needed
        fund_id = collector2._resolve_fund_id("SPY")
        assert fund_id == 1
        # API call count should still be 1 (from original collector)
        assert mock_session.get_with_retry.call_count == 1


# =============================================================================
# fetch_multiple() parallel tests
# =============================================================================


class TestFetchMultipleParallel:
    """fetch_multiple() 並列化のテスト。"""

    def test_正常系_並列度制限付きで動作する(self) -> None:
        """fetch_multiple() が並列度制限付きで動作すること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch_multiple(tickers=["SPY", "VOO"])

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert set(df["ticker"].unique()) == {"SPY", "VOO"}

    def test_正常系_max_concurrencyパラメータで並列度を制御できる(self) -> None:
        """max_concurrency パラメータで並列度を制御できること。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        # Should work with max_concurrency=1 (effectively sequential)
        df = collector.fetch_multiple(tickers=["SPY", "VOO"], max_concurrency=1)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert set(df["ticker"].unique()) == {"SPY", "VOO"}

    def test_正常系_公開IFが同期である(self) -> None:
        """fetch_multiple() が同期 API であること（asyncio.run() を内部で使用）。"""
        import asyncio

        from market.etfcom.collectors import HistoricalFundFlowsCollector

        mock_session = _make_mock_session()
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        # fetch_multiple should be a sync function
        result = collector.fetch_multiple(tickers=["SPY"])

        # It should return a DataFrame directly (not a coroutine)
        assert not asyncio.iscoroutine(result)
        assert isinstance(result, pd.DataFrame)

    def test_正常系_空のtickersリストで空DataFrame(self) -> None:
        """空のティッカーリストで空 DataFrame を返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        collector = HistoricalFundFlowsCollector()

        df = collector.fetch_multiple(tickers=[])

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_正常系_エラーティッカーをスキップして残りを返す(self) -> None:
        """一部のティッカーがエラーでも残りのデータを返すこと。"""
        from market.etfcom.collectors import HistoricalFundFlowsCollector

        # Create mock session where SPY works but UNKNOWN fails
        mock_session = _make_mock_session(
            tickers_response=[
                {"fundId": 1, "ticker": "SPY", "fundName": "SPDR"},
            ]
        )
        config = ScrapingConfig(polite_delay=0.0, delay_jitter=0.0)
        collector = HistoricalFundFlowsCollector(session=mock_session, config=config)

        df = collector.fetch_multiple(tickers=["SPY", "UNKNOWN"])

        assert isinstance(df, pd.DataFrame)
        # SPY should succeed, UNKNOWN should be skipped
        assert "SPY" in df["ticker"].values
