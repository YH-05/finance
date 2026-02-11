"""Unit tests for market.industry.api_clients.bls module.

Tests cover BLSClient initialization, request validation,
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

from market.industry.api_clients.bls import (
    BLS_API_BASE_URL,
    BLS_API_KEY_ENV,
    DEFAULT_CACHE_TTL_SECONDS,
    MAX_SERIES_PER_REQUEST,
    MAX_YEARS_PER_REQUEST,
    BLSClient,
    BLSObservation,
    BLSResponse,
    BLSSeriesResult,
    _build_cache_key,
    _parse_bls_response,
    _read_cache,
    _write_cache,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def sample_bls_api_response() -> dict:
    """Return a sample BLS API v2.0 response payload."""
    return {
        "status": "REQUEST_SUCCEEDED",
        "responseTime": 100,
        "message": [],
        "Results": {
            "series": [
                {
                    "seriesID": "CES3133440001",
                    "data": [
                        {
                            "year": "2025",
                            "period": "M06",
                            "periodName": "June",
                            "latest": "true",
                            "value": "152300",
                            "footnotes": [{"code": "", "text": ""}],
                        },
                        {
                            "year": "2025",
                            "period": "M05",
                            "periodName": "May",
                            "value": "151800",
                            "footnotes": [],
                        },
                        {
                            "year": "2025",
                            "period": "M04",
                            "periodName": "April",
                            "value": "151200",
                            "footnotes": [],
                        },
                    ],
                }
            ]
        },
    }


@pytest.fixture()
def cache_dir(tmp_path: Path) -> Path:
    """Return a temporary cache directory."""
    d = tmp_path / "bls_cache"
    d.mkdir()
    return d


# =============================================================================
# BLSObservation Tests
# =============================================================================


class TestBLSObservation:
    """Tests for BLSObservation Pydantic model."""

    def test_正常系_観測値を作成できる(self) -> None:
        obs = BLSObservation(
            year="2025",
            period="M01",
            period_name="January",
            value="152300",
            footnotes=[],
        )
        assert obs.year == "2025"
        assert obs.period == "M01"
        assert obs.period_name == "January"
        assert obs.value == "152300"

    def test_正常系_数値変換が成功する(self) -> None:
        obs = BLSObservation(
            year="2025",
            period="M01",
            period_name="January",
            value="152300.5",
            footnotes=[],
        )
        assert obs.numeric_value == 152300.5

    def test_異常系_数値変換が失敗するとNone(self) -> None:
        obs = BLSObservation(
            year="2025",
            period="M01",
            period_name="January",
            value="-",
            footnotes=[],
        )
        assert obs.numeric_value is None

    def test_正常系_日付変換が成功する(self) -> None:
        obs = BLSObservation(
            year="2025",
            period="M06",
            period_name="June",
            value="100",
            footnotes=[],
        )
        expected = datetime(2025, 6, 1, tzinfo=timezone.utc)
        assert obs.date == expected

    def test_エッジケース_M13は年次平均でNone(self) -> None:
        obs = BLSObservation(
            year="2025",
            period="M13",
            period_name="Annual",
            value="100",
            footnotes=[],
        )
        assert obs.date is None

    def test_エッジケース_Qピリオドは変換不可でNone(self) -> None:
        obs = BLSObservation(
            year="2025",
            period="Q01",
            period_name="1st Quarter",
            value="100",
            footnotes=[],
        )
        assert obs.date is None

    def test_正常系_デフォルトのfootnotes(self) -> None:
        obs = BLSObservation(
            year="2025",
            period="M01",
            period_name="January",
            value="100",
        )
        assert obs.footnotes == []


# =============================================================================
# BLSSeriesResult Tests
# =============================================================================


class TestBLSSeriesResult:
    """Tests for BLSSeriesResult Pydantic model."""

    def test_正常系_シリーズ結果を作成できる(self) -> None:
        result = BLSSeriesResult(
            series_id="CES3133440001",
            data=[
                BLSObservation(
                    year="2025",
                    period="M01",
                    period_name="January",
                    value="152300",
                    footnotes=[],
                ),
            ],
        )
        assert result.series_id == "CES3133440001"
        assert len(result.data) == 1

    def test_正常系_空のデータリスト(self) -> None:
        result = BLSSeriesResult(series_id="TEST001")
        assert result.data == []


# =============================================================================
# BLSResponse Tests
# =============================================================================


class TestBLSResponse:
    """Tests for BLSResponse Pydantic model."""

    def test_正常系_成功レスポンス(self) -> None:
        response = BLSResponse(
            status="REQUEST_SUCCEEDED",
            message=[],
            series=[],
        )
        assert response.is_success is True

    def test_正常系_エラーレスポンス(self) -> None:
        response = BLSResponse(
            status="REQUEST_FAILED",
            message=["Invalid Series ID"],
            series=[],
        )
        assert response.is_success is False

    def test_正常系_デフォルト値(self) -> None:
        response = BLSResponse(status="REQUEST_SUCCEEDED")
        assert response.message == []
        assert response.series == []


# =============================================================================
# Response Parser Tests
# =============================================================================


class TestParseBLSResponse:
    """Tests for _parse_bls_response function."""

    def test_正常系_APIレスポンスをパースできる(
        self, sample_bls_api_response: dict
    ) -> None:
        result = _parse_bls_response(sample_bls_api_response)
        assert result.is_success
        assert len(result.series) == 1
        assert result.series[0].series_id == "CES3133440001"
        assert len(result.series[0].data) == 3

    def test_正常系_観測値が正しくパースされる(
        self, sample_bls_api_response: dict
    ) -> None:
        result = _parse_bls_response(sample_bls_api_response)
        first_obs = result.series[0].data[0]
        assert first_obs.year == "2025"
        assert first_obs.period == "M06"
        assert first_obs.period_name == "June"
        assert first_obs.value == "152300"

    def test_エッジケース_空のレスポンス(self) -> None:
        result = _parse_bls_response({})
        assert result.status == "UNKNOWN"
        assert result.series == []

    def test_エッジケース_Resultsなしのレスポンス(self) -> None:
        result = _parse_bls_response({"status": "REQUEST_SUCCEEDED"})
        assert result.is_success
        assert result.series == []


# =============================================================================
# Cache Tests
# =============================================================================


class TestBLSCache:
    """Tests for BLS cache utility functions."""

    def test_正常系_キャッシュキーが決定論的(self) -> None:
        key1 = _build_cache_key(["CES001", "CES002"], 2020, 2025)
        key2 = _build_cache_key(["CES001", "CES002"], 2020, 2025)
        assert key1 == key2

    def test_正常系_異なるパラメータで異なるキー(self) -> None:
        key1 = _build_cache_key(["CES001"], 2020, 2025)
        key2 = _build_cache_key(["CES001"], 2021, 2025)
        assert key1 != key2

    def test_正常系_ソート済みのシリーズIDで同じキー(self) -> None:
        key1 = _build_cache_key(["B", "A"], 2020, 2025)
        key2 = _build_cache_key(["A", "B"], 2020, 2025)
        assert key1 == key2

    def test_正常系_キャッシュの書き込みと読み取り(self, cache_dir: Path) -> None:
        data = {"status": "REQUEST_SUCCEEDED", "Results": {"series": []}}
        _write_cache(cache_dir, "test_key", data)
        result = _read_cache(cache_dir, "test_key", DEFAULT_CACHE_TTL_SECONDS)
        assert result == data

    def test_正常系_存在しないキャッシュはNone(self, cache_dir: Path) -> None:
        result = _read_cache(cache_dir, "nonexistent", DEFAULT_CACHE_TTL_SECONDS)
        assert result is None

    def test_正常系_期限切れキャッシュはNone(self, cache_dir: Path) -> None:
        data = {"status": "OK"}
        # Write cache manually with expired timestamp
        cache_file = cache_dir / "expired_key.json"
        cache_payload = {
            "cached_at": time.time() - 999999,
            "response": data,
        }
        cache_file.write_text(json.dumps(cache_payload), encoding="utf-8")

        result = _read_cache(cache_dir, "expired_key", 1)
        assert result is None

    def test_正常系_不正なJSONキャッシュはNone(self, cache_dir: Path) -> None:
        cache_file = cache_dir / "bad_json.json"
        cache_file.write_text("not json", encoding="utf-8")
        result = _read_cache(cache_dir, "bad_json", DEFAULT_CACHE_TTL_SECONDS)
        assert result is None


# =============================================================================
# BLSClient Initialization Tests
# =============================================================================


class TestBLSClientInit:
    """Tests for BLSClient initialization."""

    def test_正常系_APIキーを直接渡せる(self) -> None:
        client = BLSClient(api_key="test-key-123")
        assert client._api_key == "test-key-123"

    def test_正常系_環境変数からAPIキーを読み取れる(self) -> None:
        with patch.dict("os.environ", {BLS_API_KEY_ENV: "env-key-456"}):
            client = BLSClient()
            assert client._api_key == "env-key-456"

    def test_異常系_APIキーなしでValueError(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="BLS API key not provided"),
        ):
            BLSClient()

    def test_正常系_カスタムキャッシュ設定(self, cache_dir: Path) -> None:
        client = BLSClient(
            api_key="key",
            cache_dir=cache_dir,
            cache_ttl_seconds=3600,
            timeout=60.0,
        )
        assert client._cache_dir == cache_dir
        assert client._cache_ttl_seconds == 3600
        assert client._timeout == 60.0


# =============================================================================
# BLSClient.get_series Validation Tests
# =============================================================================


class TestBLSClientValidation:
    """Tests for BLSClient input validation."""

    @pytest.fixture()
    def client(self) -> BLSClient:
        return BLSClient(api_key="test-key")

    @pytest.mark.anyio()
    async def test_異常系_空のシリーズIDでValueError(self, client: BLSClient) -> None:
        async with client:
            with pytest.raises(ValueError, match="series_ids must not be empty"):
                await client.get_series([])

    @pytest.mark.anyio()
    async def test_異常系_50件超のシリーズIDでValueError(
        self, client: BLSClient
    ) -> None:
        series_ids = [f"CES{i:010d}" for i in range(51)]
        async with client:
            with pytest.raises(ValueError, match="Maximum 50 series"):
                await client.get_series(series_ids)

    @pytest.mark.anyio()
    async def test_異常系_20年超の範囲でValueError(self, client: BLSClient) -> None:
        async with client:
            with pytest.raises(ValueError, match="Maximum 20 year range"):
                await client.get_series(["CES001"], start_year=2000, end_year=2025)


# =============================================================================
# BLSClient.get_series Tests (with mocked HTTP)
# =============================================================================


class TestBLSClientGetSeries:
    """Tests for BLSClient.get_series with mocked HTTP."""

    @pytest.fixture()
    def client(self, cache_dir: Path) -> BLSClient:
        return BLSClient(
            api_key="test-key",
            cache_dir=cache_dir,
        )

    @pytest.mark.anyio()
    async def test_正常系_シリーズデータを取得できる(
        self,
        client: BLSClient,
        sample_bls_api_response: dict,
    ) -> None:
        mock_response = httpx.Response(
            200,
            json=sample_bls_api_response,
            request=httpx.Request("POST", BLS_API_BASE_URL),
        )

        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.post = AsyncMock(return_value=mock_response)

            result = await client.get_series(
                ["CES3133440001"],
                start_year=2020,
                end_year=2025,
                use_cache=False,
            )

        assert result.is_success
        assert len(result.series) == 1
        assert result.series[0].series_id == "CES3133440001"
        assert len(result.series[0].data) == 3

    @pytest.mark.anyio()
    async def test_正常系_キャッシュからデータを返す(
        self,
        client: BLSClient,
        sample_bls_api_response: dict,
        cache_dir: Path,
    ) -> None:
        # Pre-populate cache
        cache_key = _build_cache_key(["CES001"], 2020, 2025)
        _write_cache(cache_dir, cache_key, sample_bls_api_response)

        async with client:
            mock_http_client = AsyncMock()
            client._client = mock_http_client  # type: ignore[assignment]

            result = await client.get_series(
                ["CES001"],
                start_year=2020,
                end_year=2025,
                use_cache=True,
            )

            # HTTP client should not have been called (check before close)
            mock_http_client.post.assert_not_called()

        assert result.is_success

    @pytest.mark.anyio()
    async def test_異常系_APIエラーでRuntimeError(
        self,
        client: BLSClient,
    ) -> None:
        error_response = {
            "status": "REQUEST_FAILED",
            "message": ["Invalid Series ID"],
            "Results": {"series": []},
        }
        mock_response = httpx.Response(
            200,
            json=error_response,
            request=httpx.Request("POST", BLS_API_BASE_URL),
        )

        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(RuntimeError, match="BLS API error"):
                await client.get_series(
                    ["INVALID"],
                    start_year=2020,
                    end_year=2025,
                    use_cache=False,
                )

    @pytest.mark.anyio()
    async def test_異常系_コンテキストマネージャ外でRuntimeError(
        self,
        client: BLSClient,
    ) -> None:
        with pytest.raises(RuntimeError, match="async context manager"):
            await client.get_series(["CES001"])


# =============================================================================
# BLSClient.get_series_as_reports Tests
# =============================================================================


class TestBLSClientGetSeriesAsReports:
    """Tests for BLSClient.get_series_as_reports."""

    @pytest.mark.anyio()
    async def test_正常系_IndustryReportに変換できる(
        self,
        sample_bls_api_response: dict,
        cache_dir: Path,
    ) -> None:
        client = BLSClient(api_key="test-key", cache_dir=cache_dir)
        mock_response = httpx.Response(
            200,
            json=sample_bls_api_response,
            request=httpx.Request("POST", BLS_API_BASE_URL),
        )

        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.post = AsyncMock(return_value=mock_response)

            reports = await client.get_series_as_reports(
                series_ids=["CES3133440001"],
                sector="Technology",
                start_year=2020,
                end_year=2025,
            )

        assert len(reports) == 1
        assert reports[0].source == "BLS"
        assert reports[0].sector == "Technology"
        assert "CES3133440001" in reports[0].title
        assert reports[0].tier.value == "api"
