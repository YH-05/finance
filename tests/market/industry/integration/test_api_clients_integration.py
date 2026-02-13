"""Integration tests for market.industry.api_clients module.

These tests verify the full request-response cycle including
caching, response parsing, and IndustryReport conversion using
mocked HTTP transport (no real API calls).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

if TYPE_CHECKING:
    from pathlib import Path

import httpx
import pytest

from market.industry.api_clients.bls import (
    BLS_API_BASE_URL,
    BLSClient,
)
from market.industry.api_clients.bls import (
    _build_cache_key as bls_build_cache_key,
)
from market.industry.api_clients.census import (
    CENSUS_API_BASE_URL,
    CensusClient,
)
from market.industry.api_clients.census import (
    _build_cache_key as census_build_cache_key,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def cache_dir(tmp_path: Path) -> Path:
    """Return a temporary cache directory for integration tests."""
    d = tmp_path / "integration_cache"
    d.mkdir()
    return d


@pytest.fixture()
def bls_response_payload() -> dict:
    """Return a realistic BLS API response with multiple series."""
    return {
        "status": "REQUEST_SUCCEEDED",
        "responseTime": 150,
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
                    ],
                },
                {
                    "seriesID": "LNS14000000",
                    "data": [
                        {
                            "year": "2025",
                            "period": "M06",
                            "periodName": "June",
                            "value": "3.8",
                            "footnotes": [],
                        },
                    ],
                },
            ]
        },
    }


@pytest.fixture()
def census_response_payload() -> list[list[str]]:
    """Return a realistic Census Bureau API response."""
    return [
        ["CTY_CODE", "CTY_NAME", "ALL_VAL_MO", "ALL_VAL_YR", "time"],
        ["0000", "WORLD", "150000000000", "900000000000", "2025-06"],
        ["1220", "CANADA", "30000000000", "180000000000", "2025-06"],
        ["5700", "CHINA", "12000000000", "72000000000", "2025-06"],
    ]


# =============================================================================
# BLS Integration Tests
# =============================================================================


class TestBLSClientIntegration:
    """Integration tests for BLSClient full request-cache-parse cycle."""

    @pytest.mark.anyio()
    async def test_正常系_フルサイクル_取得_キャッシュ_再取得(
        self,
        bls_response_payload: dict,
        cache_dir: Path,
    ) -> None:
        """Verify: fetch -> cache write -> fetch from cache -> same result."""
        client = BLSClient(
            api_key="integration-key",
            cache_dir=cache_dir,
            cache_ttl_seconds=3600,
        )

        mock_response = httpx.Response(
            200,
            json=bls_response_payload,
            request=httpx.Request("POST", BLS_API_BASE_URL),
        )

        # First call: fetches from API and writes cache
        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.post = AsyncMock(return_value=mock_response)

            result1 = await client.get_series(
                ["CES3133440001", "LNS14000000"],
                start_year=2020,
                end_year=2025,
                use_cache=True,
            )

        assert result1.is_success
        assert len(result1.series) == 2

        # Verify cache file was written
        cache_key = bls_build_cache_key(["CES3133440001", "LNS14000000"], 2020, 2025)
        cache_file = cache_dir / f"{cache_key}.json"
        assert cache_file.exists()

        # Second call: should return from cache (no HTTP call)
        client2 = BLSClient(
            api_key="integration-key",
            cache_dir=cache_dir,
            cache_ttl_seconds=3600,
        )

        async with client2:
            mock_http_client2 = AsyncMock()
            client2._client = mock_http_client2  # type: ignore[assignment]

            result2 = await client2.get_series(
                ["CES3133440001", "LNS14000000"],
                start_year=2020,
                end_year=2025,
                use_cache=True,
            )

            # HTTP client should not have been called (check before close)
            mock_http_client2.post.assert_not_called()

        assert result2.is_success
        assert len(result2.series) == 2

    @pytest.mark.anyio()
    async def test_正常系_複数シリーズからIndustryReport変換(
        self,
        bls_response_payload: dict,
        cache_dir: Path,
    ) -> None:
        """Verify BLS data converts correctly to IndustryReport format."""
        client = BLSClient(
            api_key="integration-key",
            cache_dir=cache_dir,
        )

        mock_response = httpx.Response(
            200,
            json=bls_response_payload,
            request=httpx.Request("POST", BLS_API_BASE_URL),
        )

        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.post = AsyncMock(return_value=mock_response)

            reports = await client.get_series_as_reports(
                series_ids=["CES3133440001", "LNS14000000"],
                sector="Technology",
                start_year=2020,
                end_year=2025,
            )

        assert len(reports) == 2
        for report in reports:
            assert report.source == "BLS"
            assert report.sector == "Technology"
            assert report.tier.value == "api"
            assert report.summary is not None


# =============================================================================
# Census Integration Tests
# =============================================================================


class TestCensusClientIntegration:
    """Integration tests for CensusClient full request-cache-parse cycle."""

    @pytest.mark.anyio()
    async def test_正常系_フルサイクル_取得_キャッシュ_再取得(
        self,
        census_response_payload: list[list[str]],
        cache_dir: Path,
    ) -> None:
        """Verify: fetch -> cache write -> fetch from cache -> same result."""
        client = CensusClient(
            api_key="integration-key",
            cache_dir=cache_dir,
            cache_ttl_seconds=3600,
        )

        url = f"{CENSUS_API_BASE_URL}/exports/hs"
        mock_response = httpx.Response(
            200,
            json=census_response_payload,
            request=httpx.Request("GET", url),
        )

        # First call: fetches from API and writes cache
        async with client:
            client._client = AsyncMock()  # type: ignore[assignment]
            client._client.get = AsyncMock(return_value=mock_response)

            result1 = await client.get_trade_data(
                flow="exports",
                classification="hs",
                year=2025,
                month=6,
                use_cache=True,
            )

        assert len(result1.data) == 3
        assert result1.total_value > 0

        # Verify cache file was written
        cache_key = census_build_cache_key("exports", "hs", 2025, 6)
        cache_file = cache_dir / f"{cache_key}.json"
        assert cache_file.exists()

        # Second call: should return from cache
        client2 = CensusClient(
            api_key="integration-key",
            cache_dir=cache_dir,
            cache_ttl_seconds=3600,
        )

        async with client2:
            mock_http_client2 = AsyncMock()
            client2._client = mock_http_client2  # type: ignore[assignment]

            result2 = await client2.get_trade_data(
                flow="exports",
                classification="hs",
                year=2025,
                month=6,
                use_cache=True,
            )

            # HTTP client should not have been called (check before close)
            mock_http_client2.get.assert_not_called()

        assert len(result2.data) == 3

    @pytest.mark.anyio()
    async def test_正常系_貿易データからIndustryReport変換(
        self,
        census_response_payload: list[list[str]],
        cache_dir: Path,
    ) -> None:
        """Verify Census data converts correctly to IndustryReport format."""
        client = CensusClient(
            api_key="integration-key",
            cache_dir=cache_dir,
        )

        url = f"{CENSUS_API_BASE_URL}/exports/hs"
        mock_response = httpx.Response(
            200,
            json=census_response_payload,
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
                sector="Consumer_Discretionary",
            )

        assert len(reports) == 1
        report = reports[0]
        assert report.source == "Census Bureau"
        assert report.sector == "Consumer_Discretionary"
        assert report.tier.value == "api"
        assert "Exports" in report.title
        assert "HS" in report.title


# =============================================================================
# Cross-Client Integration Tests
# =============================================================================


class TestCrossClientIntegration:
    """Tests verifying BLS and Census clients produce compatible output."""

    @pytest.mark.anyio()
    async def test_正常系_両クライアントのレポートが互換性ある(
        self,
        bls_response_payload: dict,
        census_response_payload: list[list[str]],
        cache_dir: Path,
    ) -> None:
        """Both clients produce IndustryReport with consistent tier=API."""
        bls_client = BLSClient(
            api_key="key",
            cache_dir=cache_dir / "bls",
        )
        census_client = CensusClient(
            api_key="key",
            cache_dir=cache_dir / "census",
        )

        bls_mock = httpx.Response(
            200,
            json=bls_response_payload,
            request=httpx.Request("POST", BLS_API_BASE_URL),
        )
        census_url = f"{CENSUS_API_BASE_URL}/exports/hs"
        census_mock = httpx.Response(
            200,
            json=census_response_payload,
            request=httpx.Request("GET", census_url),
        )

        async with bls_client:
            bls_client._client = AsyncMock()  # type: ignore[assignment]
            bls_client._client.post = AsyncMock(return_value=bls_mock)
            bls_reports = await bls_client.get_series_as_reports(
                series_ids=["CES3133440001"],
                sector="Technology",
            )

        async with census_client:
            census_client._client = AsyncMock()  # type: ignore[assignment]
            census_client._client.get = AsyncMock(return_value=census_mock)
            census_reports = await census_client.get_trade_as_reports(
                flow="exports",
                classification="hs",
                year=2025,
                month=6,
                sector="Technology",
            )

        all_reports = bls_reports + census_reports

        # BLS returns 2 series (CES + LNS), Census returns 1 aggregate
        assert len(bls_reports) == 2
        assert len(census_reports) == 1
        assert len(all_reports) == 3

        # All reports should have API tier
        for report in all_reports:
            assert report.tier.value == "api"
            assert report.sector == "Technology"
            assert report.url.startswith("https://")
