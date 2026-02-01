"""Unit tests for HTTPClient."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from rss.core.http_client import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    HTTPClient,
)
from rss.exceptions import FeedFetchError
from rss.types import HTTPResponse


@pytest.fixture
def mock_httpx_client() -> Generator[tuple[MagicMock, AsyncMock], None, None]:
    """Create a mock httpx.AsyncClient with common setup.

    Yields
    ------
    tuple[MagicMock, AsyncMock]
        Tuple of (mock_client_class, mock_client_instance)
    """
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        yield mock_client_class, mock_client


def create_mock_response(
    status_code: int = 200,
    text: str = "content",
    headers: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock HTTP response.

    Parameters
    ----------
    status_code : int, default=200
        HTTP status code
    text : str, default="content"
        Response body text
    headers : dict[str, str] | None, default=None
        Response headers

    Returns
    -------
    MagicMock
        Mock response object
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text
    mock_response.headers = headers if headers is not None else {}
    return mock_response


class TestHTTPClientInit:
    """Test HTTPClient initialization."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        client = HTTPClient()
        assert client.user_agent == DEFAULT_USER_AGENT
        assert client.verify_ssl is True

    def test_init_custom_user_agent(self) -> None:
        """Test initialization with custom User-Agent."""
        custom_ua = "custom-agent/1.0"
        client = HTTPClient(user_agent=custom_ua)
        assert client.user_agent == custom_ua

    def test_init_verify_ssl_disabled(self) -> None:
        """Test initialization with SSL verification disabled."""
        client = HTTPClient(verify_ssl=False)
        assert client.verify_ssl is False


class TestHTTPClientFetch:
    """Test HTTPClient.fetch method."""

    @pytest.mark.asyncio
    async def test_fetch_success(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test successful fetch returns HTTPResponse."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response(
            status_code=200,
            text="<html>Test content</html>",
            headers={"content-type": "text/html"},
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        response = await client.fetch("https://example.com")

        assert isinstance(response, HTTPResponse)
        assert response.status_code == 200
        assert response.content == "<html>Test content</html>"
        assert response.headers["content-type"] == "text/html"

    @pytest.mark.asyncio
    async def test_fetch_with_custom_timeout(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test fetch with custom timeout setting."""
        mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response()
        mock_client.get = AsyncMock(return_value=mock_response)

        await client.fetch("https://example.com", timeout=30)

        # Verify timeout was passed to AsyncClient
        call_args = mock_client_class.call_args
        timeout_arg = call_args.kwargs.get("timeout")
        assert timeout_arg is not None

    @pytest.mark.asyncio
    async def test_fetch_404_raises_feed_fetch_error_no_retry(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test that 404 error raises FeedFetchError without retry."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response(status_code=404, text="Not Found")
        call_count = 0

        async def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            return mock_response

        mock_client.get = mock_get

        with pytest.raises(FeedFetchError) as exc_info:
            await client.fetch("https://example.com/notfound")

        assert "HTTP 404" in str(exc_info.value)
        assert call_count == 1  # No retry for 4xx errors

    @pytest.mark.asyncio
    async def test_fetch_5xx_retries_and_fails(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test that 5xx error triggers retries."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response(
            status_code=500, text="Internal Server Error"
        )
        call_count = 0

        async def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            return mock_response

        mock_client.get = mock_get

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(FeedFetchError) as exc_info,
        ):
            await client.fetch("https://example.com", max_retries=3)

        assert "HTTP 500" in str(exc_info.value)
        assert call_count == 4  # Initial + 3 retries

    @pytest.mark.asyncio
    async def test_fetch_5xx_succeeds_after_retry(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test that 5xx error followed by success works."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        call_count = 0

        async def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return create_mock_response(status_code=500, text="Server Error")
            return create_mock_response(status_code=200, text="Success")

        mock_client.get = mock_get

        with patch("asyncio.sleep", new_callable=AsyncMock):
            response = await client.fetch("https://example.com")

        assert response.status_code == 200
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_timeout_retries(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test that timeout error triggers retries."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        call_count = 0

        async def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("Connection timed out")

        mock_client.get = mock_get

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(FeedFetchError) as exc_info,
        ):
            await client.fetch("https://example.com", max_retries=2)

        assert "Connection timed out" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_fetch_connection_error_retries(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test that connection error triggers retries."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        call_count = 0

        async def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("Connection refused")

        mock_client.get = mock_get

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(FeedFetchError) as exc_info,
        ):
            await client.fetch("https://example.com", max_retries=2)

        assert "Connection refused" in str(exc_info.value)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_user_agent_header(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test that User-Agent header is set correctly."""
        mock_client_class, mock_client = mock_httpx_client
        custom_ua = "test-agent/2.0"
        client = HTTPClient(user_agent=custom_ua)

        mock_response = create_mock_response()
        mock_client.get = AsyncMock(return_value=mock_response)

        await client.fetch("https://example.com")

        call_args = mock_client_class.call_args
        headers = call_args.kwargs.get("headers", {})
        assert headers.get("User-Agent") == custom_ua

    @pytest.mark.asyncio
    async def test_fetch_ssl_verification(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test that SSL verification setting is passed."""
        mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient(verify_ssl=True)

        mock_response = create_mock_response()
        mock_client.get = AsyncMock(return_value=mock_response)

        await client.fetch("https://example.com")

        call_args = mock_client_class.call_args
        verify = call_args.kwargs.get("verify")
        assert verify is True


class TestHTTPClientValidateUrl:
    """Test HTTPClient.validate_url method."""

    @pytest.mark.asyncio
    async def test_validate_url_success(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test successful URL validation returns True."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response(status_code=200)
        mock_client.head = AsyncMock(return_value=mock_response)

        result = await client.validate_url("https://example.com")

        assert result is True
        mock_client.head.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_url_redirect_success(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test URL validation with redirect returns True."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response(status_code=301)
        mock_client.head = AsyncMock(return_value=mock_response)

        result = await client.validate_url("https://example.com")

        # 3xx redirect with follow_redirects=True should eventually return 200
        # But in this test, we mock 301 as final response which is < 400
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_url_not_found(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test URL validation for 404 returns False."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response(status_code=404)
        mock_client.head = AsyncMock(return_value=mock_response)

        result = await client.validate_url("https://example.com/notfound")

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_url_timeout(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test URL validation returns False on timeout."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_client.head = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        result = await client.validate_url("https://example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_url_connection_error(
        self, mock_httpx_client: tuple[MagicMock, AsyncMock]
    ) -> None:
        """Test URL validation returns False on connection error."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_client.head = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await client.validate_url("https://example.com")

        assert result is False


class TestHTTPClientBackoff:
    """Test exponential backoff calculation."""

    def test_calculate_backoff_delay_attempt_0(self) -> None:
        """Test backoff delay for first attempt (0)."""
        client = HTTPClient()
        delay = client._calculate_backoff_delay(0)
        assert delay == 1.0  # 1 * 2^0 = 1

    def test_calculate_backoff_delay_attempt_1(self) -> None:
        """Test backoff delay for second attempt (1)."""
        client = HTTPClient()
        delay = client._calculate_backoff_delay(1)
        assert delay == 2.0  # 1 * 2^1 = 2

    def test_calculate_backoff_delay_attempt_2(self) -> None:
        """Test backoff delay for third attempt (2)."""
        client = HTTPClient()
        delay = client._calculate_backoff_delay(2)
        assert delay == 4.0  # 1 * 2^2 = 4


class TestHTTPClientConstants:
    """Test HTTPClient constants."""

    def test_default_user_agent(self) -> None:
        """Test default User-Agent constant."""
        assert DEFAULT_USER_AGENT == "rss-feed-collector/0.1.0"

    def test_default_timeout(self) -> None:
        """Test default timeout constant."""
        assert DEFAULT_TIMEOUT == 10

    def test_default_max_retries(self) -> None:
        """Test default max retries constant."""
        assert DEFAULT_MAX_RETRIES == 3


class TestHTTPClientLogging:
    """Test HTTPClient logging behavior.

    Note: structlog logging behavior depends on global configuration which can
    vary based on test execution order. These tests verify correct execution
    rather than specific log output.
    """

    @pytest.mark.asyncio
    async def test_fetch_logs_on_success(
        self,
        mock_httpx_client: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test that fetch executes with logging enabled."""
        _mock_client_class, mock_client = mock_httpx_client
        client = HTTPClient()

        mock_response = create_mock_response()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Execute method - should not raise any exceptions
        # Logging is enabled internally, this verifies no errors occur
        response = await client.fetch("https://example.com")

        assert response.status_code == 200
