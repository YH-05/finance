"""Unit tests for market.industry.api_clients.census module.

Tests cover CensusClient initialization, request validation,
response parsing, caching, and error handling.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import httpx
import pytest

from market.industry.api_clients.census import (
    CENSUS_API_BASE_URL,
    CENSUS_API_KEY_ENV,
    DEFAULT_CACHE_TTL_SECONDS,
    CensusClient,
    CensusTradeRecord,
    CensusTradeResponse,
    _build_cache_key,
    _find_column_index,
    _parse_census_response,
    _read_cache,
    _write_cache,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def sample_census_response() -> list[list[str]]:
    """Return a sample Census Bureau API response payload."""
    return [
        ["CTY_CODE", "CTY_NAME", "ALL_VAL_MO", "ALL_VAL_YR", "time"],
        ["0000", "WORLD", "150000000000", "900000000000", "2025-06"],
        ["1220", "CANADA", "30000000000", "180000000000", "2025-06"],
        ["5700", "CHINA", "12000000000", "72000000000", "2025-06"],
        ["2010", "MEXICO", "28000000000", "168000000000", "2025-06"],
    ]


@pytest.fixture()
def cache_dir(tmp_path: Path) -> Path:
    """Return a temporary cache directory."""
    d = tmp_path / "census_cache"
    d.mkdir()
    return d


# =============================================================================
# CensusTradeRecord Tests
# =============================================================================


class TestCensusTradeRecord:
    """Tests for CensusTradeRecord Pydantic model."""

    def test_正常系_貿易レコードを作成できる(self) -> None:
        record = CensusTradeRecord(
            commodity_code="27",
            commodity_description="Mineral fuels, oils",
            value=5_000_000_000,
            year=2025,
            month=6,
            flow="exports",
            classification="hs",
        )
        assert record.commodity_code == "27"
        assert record.value == 5_000_000_000
        assert record.year == 2025
        assert record.month == 6

    def test_正常系_月次データのdate変換(self) -> None:
        record = CensusTradeRecord(
            commodity_code="27",
            value=1000,
            year=2025,
            month=6,
            flow="exports",
            classification="hs",
        )
        expected = datetime(2025, 6, 1, tzinfo=timezone.utc)
        assert record.date == expected

    def test_正常系_年次データのdate変換(self) -> None:
        record = CensusTradeRecord(
            commodity_code="27",
            value=1000,
            year=2025,
            month=None,
            flow="exports",
            classification="hs",
        )
        expected = datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert record.date == expected

    def test_正常系_デフォルト値(self) -> None:
        record = CensusTradeRecord(commodity_code="00")
        assert record.commodity_description == ""
        assert record.value == 0.0
        assert record.month is None


# =============================================================================
# CensusTradeResponse Tests
# =============================================================================


class TestCensusTradeResponse:
    """Tests for CensusTradeResponse Pydantic model."""

    def test_正常系_合計値を計算できる(self) -> None:
        response = CensusTradeResponse(
            data=[
                CensusTradeRecord(commodity_code="A", value=100),
                CensusTradeRecord(commodity_code="B", value=200),
                CensusTradeRecord(commodity_code="C", value=300),
            ],
            flow="exports",
            classification="hs",
            year=2025,
            month=6,
        )
        assert response.total_value == 600

    def test_正常系_空データの合計値はゼロ(self) -> None:
        response = CensusTradeResponse(
            data=[],
            flow="exports",
            classification="hs",
            year=2025,
        )
        assert response.total_value == 0.0


# =============================================================================
# Response Parser Tests
# =============================================================================


class TestParseCensusResponse:
    """Tests for _parse_census_response function."""

    def test_正常系_APIレスポンスをパースできる(
        self, sample_census_response: list[list[str]]
    ) -> None:
        result = _parse_census_response(
            sample_census_response, "exports", "hs", 2025, 6
        )
        assert len(result.data) == 4
        assert result.flow == "exports"
        assert result.classification == "hs"
        assert result.year == 2025
        assert result.month == 6

    def test_正常系_レコードが正しくパースされる(
        self, sample_census_response: list[list[str]]
    ) -> None:
        result = _parse_census_response(
            sample_census_response, "exports", "hs", 2025, 6
        )
        first = result.data[0]
        assert first.commodity_code == "0000"
        assert first.commodity_description == "WORLD"
        assert first.value == 150_000_000_000

    def test_エッジケース_空のレスポンス(self) -> None:
        result = _parse_census_response([], "exports", "hs", 2025, 6)
        assert result.data == []

    def test_エッジケース_ヘッダーのみのレスポンス(self) -> None:
        result = _parse_census_response(
            [["CTY_CODE", "CTY_NAME"]], "exports", "hs", 2025, 6
        )
        assert result.data == []


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestFindColumnIndex:
    """Tests for _find_column_index helper function."""

    def test_正常系_カラムを見つけられる(self) -> None:
        headers = ["CTY_CODE", "CTY_NAME", "ALL_VAL_MO"]
        assert _find_column_index(headers, ["CTY_CODE"]) == 0
        assert _find_column_index(headers, ["ALL_VAL_MO"]) == 2

    def test_正常系_候補リストの優先順位(self) -> None:
        headers = ["E_COMMODITY", "CTY_CODE"]
        result = _find_column_index(headers, ["CTY_CODE", "E_COMMODITY"])
        assert result == 1  # CTY_CODE is first in candidates

    def test_エッジケース_見つからない場合None(self) -> None:
        headers = ["A", "B", "C"]
        assert _find_column_index(headers, ["X", "Y"]) is None


# =============================================================================
# Cache Tests
# =============================================================================


class TestCensusCache:
    """Tests for Census cache utility functions."""

    def test_正常系_キャッシュキーが決定論的(self) -> None:
        key1 = _build_cache_key("exports", "hs", 2025, 6)
        key2 = _build_cache_key("exports", "hs", 2025, 6)
        assert key1 == key2

    def test_正常系_異なるパラメータで異なるキー(self) -> None:
        key1 = _build_cache_key("exports", "hs", 2025, 6)
        key2 = _build_cache_key("imports", "hs", 2025, 6)
        assert key1 != key2

    def test_正常系_月ありなしで異なるキー(self) -> None:
        key1 = _build_cache_key("exports", "hs", 2025, 6)
        key2 = _build_cache_key("exports", "hs", 2025, None)
        assert key1 != key2

    def test_正常系_キャッシュの書き込みと読み取り(self, cache_dir: Path) -> None:
        data = [["H1", "H2"], ["A", "B"]]
        _write_cache(cache_dir, "test_key", data)
        result = _read_cache(cache_dir, "test_key", DEFAULT_CACHE_TTL_SECONDS)
        assert result == data

    def test_正常系_存在しないキャッシュはNone(self, cache_dir: Path) -> None:
        result = _read_cache(cache_dir, "nonexistent", DEFAULT_CACHE_TTL_SECONDS)
        assert result is None

    def test_正常系_期限切れキャッシュはNone(self, cache_dir: Path) -> None:
        data = [["H1"], ["V1"]]
        cache_file = cache_dir / "expired_key.json"
        cache_payload = {
            "cached_at": time.time() - 999999,
            "response": data,
        }
        cache_file.write_text(json.dumps(cache_payload), encoding="utf-8")

        result = _read_cache(cache_dir, "expired_key", 1)
        assert result is None


# =============================================================================
# CensusClient Initialization Tests
# =============================================================================


class TestCensusClientInit:
    """Tests for CensusClient initialization."""

    def test_正常系_APIキーを直接渡せる(self) -> None:
        client = CensusClient(api_key="test-key-123")
        assert client._api_key == "test-key-123"

    def test_正常系_環境変数からAPIキーを読み取れる(self) -> None:
        with patch.dict("os.environ", {CENSUS_API_KEY_ENV: "env-key-456"}):
            client = CensusClient()
            assert client._api_key == "env-key-456"

    def test_異常系_APIキーなしでValueError(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="Census API key not provided"),
        ):
            CensusClient()

    def test_正常系_カスタムキャッシュ設定(self, cache_dir: Path) -> None:
        client = CensusClient(
            api_key="key",
            cache_dir=cache_dir,
            cache_ttl_seconds=3600,
            timeout=60.0,
        )
        assert client._cache_dir == cache_dir
        assert client._cache_ttl_seconds == 3600
        assert client._timeout == 60.0


# =============================================================================
# CensusClient Validation Tests
# =============================================================================


class TestCensusClientValidation:
    """Tests for CensusClient input validation."""

    @pytest.fixture()
    def client(self) -> CensusClient:
        return CensusClient(api_key="test-key")

    @pytest.mark.anyio()
    async def test_異常系_不正なflowでValueError(self, client: CensusClient) -> None:
        async with client:
            with pytest.raises(ValueError, match="Invalid flow"):
                await client.get_trade_data(
                    flow="invalid", classification="hs", year=2025
                )

    @pytest.mark.anyio()
    async def test_異常系_不正なclassificationでValueError(
        self, client: CensusClient
    ) -> None:
        async with client:
            with pytest.raises(ValueError, match="Invalid classification"):
                await client.get_trade_data(
                    flow="exports", classification="invalid", year=2025
                )

    @pytest.mark.anyio()
    async def test_異常系_不正な月でValueError(self, client: CensusClient) -> None:
        async with client:
            with pytest.raises(ValueError, match="Month must be 1-12"):
                await client.get_trade_data(
                    flow="exports", classification="hs", year=2025, month=13
                )


# =============================================================================
# CensusClient.get_trade_data Tests (with mocked HTTP)
# =============================================================================


class TestCensusClientGetTradeData:
    """Tests for CensusClient.get_trade_data with mocked HTTP."""

    @pytest.fixture()
    def client(self, cache_dir: Path) -> CensusClient:
        return CensusClient(
            api_key="test-key",
            cache_dir=cache_dir,
        )

    @pytest.mark.anyio()
    async def test_正常系_貿易データを取得できる(
        self,
        client: CensusClient,
        sample_census_response: list[list[str]],
    ) -> None:
        url = f"{CENSUS_API_BASE_URL}/exports/hs"
        mock_response = httpx.Response(
            200,
            json=sample_census_response,
            request=httpx.Request("GET", url),
        )

        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.get = AsyncMock(return_value=mock_response)

            result = await client.get_trade_data(
                flow="exports",
                classification="hs",
                year=2025,
                month=6,
                use_cache=False,
            )

        assert len(result.data) == 4
        assert result.flow == "exports"
        assert result.total_value > 0

    @pytest.mark.anyio()
    async def test_正常系_キャッシュからデータを返す(
        self,
        client: CensusClient,
        sample_census_response: list[list[str]],
        cache_dir: Path,
    ) -> None:
        cache_key = _build_cache_key("exports", "hs", 2025, 6)
        _write_cache(cache_dir, cache_key, sample_census_response)

        async with client:
            mock_http_client = AsyncMock()
            client._client = mock_http_client  # type: ignore[assignment]

            result = await client.get_trade_data(
                flow="exports",
                classification="hs",
                year=2025,
                month=6,
                use_cache=True,
            )

            # HTTP client should not have been called (check before close)
            mock_http_client.get.assert_not_called()

        assert len(result.data) == 4

    @pytest.mark.anyio()
    async def test_異常系_コンテキストマネージャ外でRuntimeError(
        self,
        client: CensusClient,
    ) -> None:
        with pytest.raises(RuntimeError, match="async context manager"):
            await client.get_trade_data(flow="exports", classification="hs", year=2025)


# =============================================================================
# CensusClient.get_trade_as_reports Tests
# =============================================================================


class TestCensusClientGetTradeAsReports:
    """Tests for CensusClient.get_trade_as_reports."""

    @pytest.mark.anyio()
    async def test_正常系_IndustryReportに変換できる(
        self,
        sample_census_response: list[list[str]],
        cache_dir: Path,
    ) -> None:
        client = CensusClient(api_key="test-key", cache_dir=cache_dir)
        url = f"{CENSUS_API_BASE_URL}/exports/hs"
        mock_response = httpx.Response(
            200,
            json=sample_census_response,
            request=httpx.Request("GET", url),
        )

        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.get = AsyncMock(return_value=mock_response)

            reports = await client.get_trade_as_reports(
                flow="exports",
                classification="hs",
                year=2025,
                month=6,
                sector="Technology",
            )

        assert len(reports) == 1
        assert reports[0].source == "Census Bureau"
        assert reports[0].sector == "Technology"
        assert "Exports" in reports[0].title
        assert reports[0].tier.value == "api"
