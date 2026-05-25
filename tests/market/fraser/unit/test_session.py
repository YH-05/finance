"""Tests for ``market.fraser.session`` module.

Tests cover the :class:`FraserSession` class including:

- Initialization and context manager protocol.
- X-API-Key header injection (no query-parameter authentication).
- SSRF prevention via ``ALLOWED_HOSTS`` whitelist.
- HTTPS enforcement.
- Polite delay between consecutive requests.
- HTTP status code error mapping (401/403/404/429/4xx/5xx).
- 429 ``Retry-After`` header parsing and exception attribute population.
- Exponential backoff retry logic in :meth:`get_with_retry`.
- Rate limiter integration.

See Also
--------
tests.market.alphavantage.unit.test_session : Reference test patterns
    that were adapted for FRASER (MagicMock(spec=httpx.Response) +
    patch('FraserSession._client.get')).
market.fraser.session : Implementation under test.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from market.fraser.errors import (
    FraserAPIError,
    FraserAuthError,
    FraserNotFoundError,
    FraserRateLimitError,
    FraserValidationError,
)
from market.fraser.session import FraserSession
from market.fraser.types import FraserConfig, RetryConfig

# =============================================================================
# Fixtures
# =============================================================================

_FRASER_PATH = "/items"
_FRASER_FULL_URL = "https://fraser.stlouisfed.org/api/items"


@pytest.fixture
def fast_retry_config() -> RetryConfig:
    """Retry config with fast iteration for tests."""
    return RetryConfig(max_attempts=3, base_wait=0.0, max_wait=0.0)


@pytest.fixture
def single_attempt_retry_config() -> RetryConfig:
    """Single-attempt retry config (effectively disables retries)."""
    return RetryConfig(max_attempts=1, base_wait=0.0, max_wait=0.0)


def _make_mock_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    text: str = "",
    headers: dict[str, str] | None = None,
) -> MagicMock:
    """Build a :class:`MagicMock` configured as an ``httpx.Response``."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text or (str(json_data) if json_data else "")
    resp.headers = headers or {"Content-Type": "application/json"}
    return resp


# =============================================================================
# TestFraserSessionInit
# =============================================================================


class TestFraserSessionInit:
    """Tests for :class:`FraserSession` initialisation."""

    def test_正常系_デフォルト設定で初期化(self) -> None:
        """Session initialises with default config (api_key from env)."""
        session = FraserSession()
        assert isinstance(session, FraserSession)
        session.close()

    def test_正常系_カスタム設定で初期化(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """Session initialises with custom config."""
        session = FraserSession(config=sample_fraser_config)
        assert isinstance(session, FraserSession)
        session.close()

    def test_正常系_リトライ設定で初期化(
        self,
        sample_fraser_config: FraserConfig,
        fast_retry_config: RetryConfig,
    ) -> None:
        """Session initialises with explicit retry config override."""
        session = FraserSession(
            config=sample_fraser_config,
            retry_config=fast_retry_config,
        )
        assert isinstance(session, FraserSession)
        session.close()


# =============================================================================
# TestFraserSessionContextManager
# =============================================================================


class TestFraserSessionContextManager:
    """Tests for context manager protocol."""

    def test_正常系_context_manager_close呼出(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """``with FraserSession(...)`` calls ``close()`` on exit."""
        session = FraserSession(config=sample_fraser_config)
        with patch.object(session._client, "close") as mock_close:
            with session as s:
                assert s is session
            mock_close.assert_called_once()


# =============================================================================
# TestXAPIKeyHeaderInjection
# =============================================================================


class TestXAPIKeyHeaderInjection:
    """Tests for X-API-Key header injection (no query-param auth)."""

    def test_正常系_X_API_Key_ヘッダ_injection(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """``X-API-Key`` header is injected on every request."""
        mock_response = _make_mock_response(json_data={"items": []})

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(
                session._client, "get", return_value=mock_response
            ) as mock_get,
        ):
            session.get(_FRASER_PATH)

            call_kwargs = mock_get.call_args
            actual_headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get(
                "headers"
            )
            assert actual_headers == {"X-API-Key": "dummy_test_key"}

    def test_正常系_apikey_クエリパラメータには注入されない(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """API key is NOT injected into query params (FRASER uses headers)."""
        mock_response = _make_mock_response(json_data={"items": []})

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(
                session._client, "get", return_value=mock_response
            ) as mock_get,
        ):
            session.get(_FRASER_PATH, params={"titleId": 677})

            call_kwargs = mock_get.call_args
            actual_params = call_kwargs.kwargs.get("params") or call_kwargs[1].get(
                "params"
            )
            assert actual_params == {"titleId": 677}
            assert "apikey" not in (actual_params or {})

    def test_正常系_環境変数からAPIキー取得(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """API key falls back to ``FRASER_API_KEY`` env var when config is empty."""
        monkeypatch.setenv("FRASER_API_KEY", "env-fraser-key")
        config = FraserConfig(api_key="", timeout=5.0)
        mock_response = _make_mock_response(json_data={"items": []})

        with (
            FraserSession(config=config) as session,
            patch.object(
                session._client, "get", return_value=mock_response
            ) as mock_get,
        ):
            session.get(_FRASER_PATH)

            call_kwargs = mock_get.call_args
            actual_headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get(
                "headers"
            )
            assert actual_headers == {"X-API-Key": "env-fraser-key"}

    def test_異常系_APIキー未設定でFraserAuthError(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``FraserAuthError`` is raised when no API key is configured."""
        monkeypatch.delenv("FRASER_API_KEY", raising=False)
        config = FraserConfig(api_key="", timeout=5.0)

        with (
            FraserSession(config=config) as session,
            pytest.raises(FraserAuthError, match="API key"),
        ):
            session.get(_FRASER_PATH)


# =============================================================================
# TestSSRFGuard
# =============================================================================


class TestSSRFGuard:
    """Tests for SSRF prevention via ``ALLOWED_HOSTS`` whitelist."""

    def test_異常系_SSRF_guard_ALLOWED_HOSTS_外で例外(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """Hosts outside ``ALLOWED_HOSTS`` raise ``FraserValidationError``."""
        with (
            FraserSession(config=sample_fraser_config) as session,
            pytest.raises(FraserValidationError, match="not in allowed hosts"),
        ):
            session.get("https://evil.com/api/items")

    def test_異常系_HTTPS_強制_httpスキームで例外(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """``http://`` scheme raises ``FraserValidationError``."""
        with (
            FraserSession(config=sample_fraser_config) as session,
            pytest.raises(FraserValidationError, match="must be 'https'"),
        ):
            session.get("http://fraser.stlouisfed.org/api/items")

    def test_異常系_不正なスキームでFraserValidationError(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """Non-http(s) schemes raise ``FraserValidationError``."""
        with (
            FraserSession(config=sample_fraser_config) as session,
            pytest.raises(FraserValidationError, match="scheme"),
        ):
            session.get("ftp://fraser.stlouisfed.org/api/items")

    def test_正常系_許可されたホストでリクエスト成功(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """Whitelisted host requests proceed without error."""
        mock_response = _make_mock_response(json_data={"items": []})

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            # Should not raise.
            session.get(_FRASER_FULL_URL)


# =============================================================================
# TestPoliteDelay
# =============================================================================


class TestPoliteDelay:
    """Tests for polite-delay timing between consecutive requests."""

    def test_正常系_polite_delay_最小間隔保証(
        self,
        sample_fraser_config: FraserConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``time.sleep`` is invoked when calls happen faster than the delay."""
        mock_response = _make_mock_response(json_data={"items": []})

        # Patch ``time.monotonic`` and ``time.sleep`` only inside the session
        # module so the rate-limiter's own ``time.monotonic()`` calls (in
        # market.alphavantage.rate_limiter) are unaffected.
        time_values: list[float] = [100.0, 100.01]
        call_idx = {"i": 0}

        def _fake_monotonic() -> float:
            idx = call_idx["i"]
            value = time_values[min(idx, len(time_values) - 1)]
            call_idx["i"] += 1
            return value

        sleep_calls: list[float] = []

        def _fake_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monkeypatch.setattr("market.fraser.session.time.monotonic", _fake_monotonic)
        monkeypatch.setattr("market.fraser.session.time.sleep", _fake_sleep)
        # Eliminate jitter randomness for deterministic asserts.
        monkeypatch.setattr(
            "market.fraser.session.random.uniform",
            lambda _a, _b: 0.0,
        )

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            session.get(_FRASER_PATH)
            session.get(_FRASER_PATH)

        # At least one positive sleep should have been recorded on the second
        # request (polite-delay enforcement).
        assert any(s > 0 for s in sleep_calls)


# =============================================================================
# TestRateLimiterIntegration
# =============================================================================


class TestRateLimiterIntegration:
    """Tests for ``DualWindowRateLimiter`` integration."""

    def test_正常系_レートリミッターacquireが呼ばれる(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """``rate_limiter.acquire()`` is called once per ``get()``."""
        mock_response = _make_mock_response(json_data={"items": []})

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._rate_limiter, "acquire") as mock_acquire,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            mock_acquire.return_value = 0.0
            session.get(_FRASER_PATH)
            mock_acquire.assert_called_once()

    def test_正常系_30req_per_min_デフォルト(self) -> None:
        """Default ``requests_per_minute`` is 30 (FRASER documented limit)."""
        config = FraserConfig(api_key="x")
        assert config.requests_per_minute == 30


# =============================================================================
# TestHTTPStatusErrorMapping
# =============================================================================


class TestHTTPStatusErrorMapping:
    """Tests for HTTP status code → FRASER exception mapping."""

    def test_異常系_401_でFraserAuthError(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """HTTP 401 raises :class:`FraserAuthError`."""
        mock_response = _make_mock_response(status_code=401, text="Unauthorized")

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
            pytest.raises(FraserAuthError, match="401"),
        ):
            session.get(_FRASER_PATH)

    def test_異常系_403_でFraserAuthError(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """HTTP 403 raises :class:`FraserAuthError`."""
        mock_response = _make_mock_response(status_code=403, text="Forbidden")

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
            pytest.raises(FraserAuthError, match="403"),
        ):
            session.get(_FRASER_PATH)

    def test_異常系_404_でFraserNotFoundError(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """HTTP 404 raises :class:`FraserNotFoundError`."""
        mock_response = _make_mock_response(status_code=404, text="Not Found")

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
            pytest.raises(FraserNotFoundError, match="404"),
        ):
            session.get(_FRASER_PATH)

    def test_異常系_429_Retry_After_尊重(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """HTTP 429 with ``Retry-After`` populates ``retry_after`` (float seconds)."""
        mock_response = _make_mock_response(
            status_code=429,
            text="Rate limited",
            headers={"Retry-After": "5"},
        )

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            with pytest.raises(FraserRateLimitError) as exc_info:
                session.get(_FRASER_PATH)
            assert exc_info.value.retry_after == 5.0

    def test_異常系_429_Retry_After_欠落でNone(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """HTTP 429 without ``Retry-After`` yields ``retry_after=None``."""
        mock_response = _make_mock_response(
            status_code=429,
            text="Rate limited",
            headers={},
        )

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            with pytest.raises(FraserRateLimitError) as exc_info:
                session.get(_FRASER_PATH)
            assert exc_info.value.retry_after is None

    def test_異常系_429_Retry_After_非数値はNone(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """Non-numeric ``Retry-After`` (e.g. HTTP-date) parses as ``None``."""
        mock_response = _make_mock_response(
            status_code=429,
            text="Rate limited",
            headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"},
        )

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            with pytest.raises(FraserRateLimitError) as exc_info:
                session.get(_FRASER_PATH)
            assert exc_info.value.retry_after is None

    def test_異常系_500_でFraserAPIError_status_code(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """HTTP 500 raises ``FraserAPIError`` with ``status_code=500``."""
        mock_response = _make_mock_response(
            status_code=500,
            text="Internal Server Error",
        )

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            with pytest.raises(FraserAPIError) as exc_info:
                session.get(_FRASER_PATH)
            assert exc_info.value.status_code == 500

    def test_異常系_400_でFraserAPIError(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """HTTP 400 (generic client error) raises ``FraserAPIError``."""
        mock_response = _make_mock_response(
            status_code=400,
            text="Bad Request",
        )

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(session._client, "get", return_value=mock_response),
        ):
            with pytest.raises(FraserAPIError) as exc_info:
                session.get(_FRASER_PATH)
            assert exc_info.value.status_code == 400


# =============================================================================
# TestExponentialBackoffRetry
# =============================================================================


class TestExponentialBackoffRetry:
    """Tests for :meth:`FraserSession.get_with_retry` exponential backoff."""

    def test_正常系_初回成功でリトライなし(
        self,
        sample_fraser_config: FraserConfig,
        fast_retry_config: RetryConfig,
    ) -> None:
        """First successful response returns immediately (no retries)."""
        mock_response = _make_mock_response(json_data={"items": []})

        with (
            FraserSession(
                config=sample_fraser_config, retry_config=fast_retry_config
            ) as session,
            patch.object(
                session._client, "get", return_value=mock_response
            ) as mock_get,
        ):
            response = session.get_with_retry(_FRASER_PATH)
            assert response.status_code == 200
            assert mock_get.call_count == 1

    def test_正常系_get_with_retry_tenacity_exponential_backoff(
        self,
        sample_fraser_config: FraserConfig,
        fast_retry_config: RetryConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """500 → 500 → 200 succeeds on the third attempt."""
        err_500 = _make_mock_response(status_code=500, text="Server Error")
        err_500_b = _make_mock_response(status_code=500, text="Server Error")
        ok = _make_mock_response(json_data={"items": []})

        # Avoid actual sleeps in tests.
        monkeypatch.setattr("market.fraser.session.time.sleep", lambda _s: None)

        with (
            FraserSession(
                config=sample_fraser_config, retry_config=fast_retry_config
            ) as session,
            patch.object(
                session._client,
                "get",
                side_effect=[err_500, err_500_b, ok],
            ) as mock_get,
        ):
            response = session.get_with_retry(_FRASER_PATH)
            assert response.status_code == 200
            assert mock_get.call_count == 3

    def test_異常系_全リトライ失敗で最後のエラー再raise(
        self,
        sample_fraser_config: FraserConfig,
        fast_retry_config: RetryConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When all attempts return 500, the final exception is raised."""
        err_500 = _make_mock_response(status_code=500, text="Server Error")

        monkeypatch.setattr("market.fraser.session.time.sleep", lambda _s: None)

        with (
            FraserSession(
                config=sample_fraser_config, retry_config=fast_retry_config
            ) as session,
            patch.object(session._client, "get", return_value=err_500),
            pytest.raises(FraserAPIError),
        ):
            session.get_with_retry(_FRASER_PATH)

    def test_異常系_4xxエラーはリトライしない(
        self,
        sample_fraser_config: FraserConfig,
        fast_retry_config: RetryConfig,
    ) -> None:
        """Client errors (4xx other than 429) are *not* retried."""
        err_400 = _make_mock_response(status_code=400, text="Bad Request")

        with (
            FraserSession(
                config=sample_fraser_config, retry_config=fast_retry_config
            ) as session,
            patch.object(session._client, "get", return_value=err_400) as mock_get,
        ):
            with pytest.raises(FraserAPIError):
                session.get_with_retry(_FRASER_PATH)
            assert mock_get.call_count == 1

    def test_正常系_429はリトライ対象(
        self,
        sample_fraser_config: FraserConfig,
        fast_retry_config: RetryConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HTTP 429 triggers retry and succeeds on next attempt."""
        err_429 = _make_mock_response(
            status_code=429,
            text="Rate limit",
            headers={"Retry-After": "0"},
        )
        ok = _make_mock_response(json_data={"items": []})

        monkeypatch.setattr("market.fraser.session.time.sleep", lambda _s: None)

        with (
            FraserSession(
                config=sample_fraser_config, retry_config=fast_retry_config
            ) as session,
            patch.object(session._client, "get", side_effect=[err_429, ok]),
        ):
            response = session.get_with_retry(_FRASER_PATH)
            assert response.status_code == 200

    def test_正常系_429_Retry_Afterに従い_sleep(
        self,
        sample_fraser_config: FraserConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Retry uses ``Retry-After`` value when present (preferred over backoff).

        The session caps ``retry_after`` by ``RetryConfig.max_wait`` (CWE-400
        guard), so this test uses ``max_wait=10.0`` to leave headroom above the
        ``Retry-After: 3`` value while still keeping the backoff bounded.
        """
        # Use a retry config whose ``max_wait`` is greater than the Retry-After
        # value so the ``min(retry_after, max_wait)`` cap does not zero out the
        # observed sleep argument. ``fast_retry_config`` uses ``max_wait=0.0``
        # and therefore cannot exercise this code path.
        retry_config = RetryConfig(max_attempts=3, base_wait=0.0, max_wait=10.0)

        err_429 = _make_mock_response(
            status_code=429,
            text="Rate limit",
            headers={"Retry-After": "3"},
        )
        ok = _make_mock_response(json_data={"items": []})

        sleep_calls: list[float] = []

        def _record_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monkeypatch.setattr("market.fraser.session.time.sleep", _record_sleep)

        with (
            FraserSession(
                config=sample_fraser_config, retry_config=retry_config
            ) as session,
            patch.object(session._client, "get", side_effect=[err_429, ok]),
        ):
            session.get_with_retry(_FRASER_PATH)

        # Among recorded sleeps, the Retry-After value (3.0) must appear; we
        # only assert membership because polite-delay may also call sleep.
        assert 3.0 in sleep_calls


# =============================================================================
# TestURLBuilding
# =============================================================================


class TestURLBuilding:
    """Tests for relative-path ↔ absolute-URL handling."""

    def test_正常系_相対パスはbase_urlに結合される(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """Relative paths are prefixed with ``base_url``."""
        mock_response = _make_mock_response(json_data={"items": []})

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(
                session._client, "get", return_value=mock_response
            ) as mock_get,
        ):
            session.get("/items")
            called_url = mock_get.call_args.args[0]
            assert called_url == _FRASER_FULL_URL

    def test_正常系_絶対URLはそのまま使用される(
        self,
        sample_fraser_config: FraserConfig,
    ) -> None:
        """Absolute URLs are passed through unchanged."""
        mock_response = _make_mock_response(json_data={"items": []})
        absolute = "https://fraser.stlouisfed.org/api/title/677"

        with (
            FraserSession(config=sample_fraser_config) as session,
            patch.object(
                session._client, "get", return_value=mock_response
            ) as mock_get,
        ):
            session.get(absolute)
            called_url = mock_get.call_args.args[0]
            assert called_url == absolute


# =============================================================================
# Diagnostic helper — keep at end so module load is fast.
# =============================================================================


class TestModuleStructure:
    """Smoke tests for module-level invariants of ``market.fraser.session``."""

    def test_正常系_sessionモジュールがFraserSessionを公開する(self) -> None:
        from market.fraser.session import FraserSession as _S

        assert _S is FraserSession

    def test_正常系_timeモジュールがimport可能(self) -> None:
        # Avoid flake8/ruff F401 noise without affecting runtime behaviour.
        assert callable(time.monotonic)
