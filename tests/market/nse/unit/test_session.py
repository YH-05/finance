"""Unit tests for market.nse.session module.

NseSession の動作を検証するテストスイート。
httpx ベースの HTTP セッションクラス（Cookie ライフサイクル管理付き）のテスト。

Test TODO List:
- [x] NseSession: デフォルト値で初期化
- [x] NseSession: カスタム config / retry_config で初期化
- [x] NseSession: httpx.Client が follow_redirects=True で生成される
- [x] NseSession: context manager プロトコル
- [x] NseSession: 例外発生時も close が呼ばれる
- [x] get(): _ensure_cookies() が呼ばれる
- [x] get(): polite_delay（monotonic ベース間隔制御）
- [x] get(): ランダム User-Agent ヘッダー設定
- [x] get(): デフォルトヘッダーが含まれる
- [x] get(): params が httpx に渡される
- [x] get(): 429 レスポンスで NseRateLimitError
- [x] get(): 403 レスポンスで NseCookieError
- [x] get(): 5xx レスポンスで NseAPIError
- [x] get(): 正常レスポンスを返却
- [x] get(): timeout が設定される
- [x] get(): SSRF防止 - 許可されたホストへのリクエストが成功する
- [x] get(): SSRF防止 - 不正なホストへのリクエストが ValueError で拒否される
- [x] get(): SSRF防止 - ホストなしURLが ValueError で拒否される
- [x] get_with_retry(): 成功時はリトライなし
- [x] get_with_retry(): 失敗後リトライで成功
- [x] get_with_retry(): 全リトライ失敗で NseRateLimitError
- [x] get_with_retry(): 指数バックオフでディレイが増加する
- [x] get_with_retry(): max_delay 上限でクリップされる
- [x] get_with_retry(): 403でNseCookieErrorが発生しCookieリフレッシュしてリトライ
- [x] get_with_retry(): NseCookieError後リトライ成功
- [x] _ensure_cookies(): Cookie未取得時に初回取得
- [x] _ensure_cookies(): Cookie有効期限内は再取得しない
- [x] _ensure_cookies(): Cookie TTL切れで再取得
- [x] _ensure_cookies(): Cookie取得後 _cookie_acquired_at が設定される
- [x] _ensure_cookies(): Cookie取得タイムアウトでフォールバック
- [x] _ensure_cookies(): Cookie取得403でフォールバック
- [x] close(): セッションが閉じられる
- [x] structlog ロガーの使用
- [x] __all__ エクスポート
"""

from unittest.mock import MagicMock, call, patch

import pytest

from market.nse.constants import ALLOWED_HOSTS, BASE_URL, DEFAULT_HEADERS
from market.nse.errors import NseAPIError, NseCookieError, NseRateLimitError
from market.nse.session import NseSession
from market.nse.types import NseConfig, RetryConfig

# Test URL within allowed hosts
_TEST_URL = f"{BASE_URL}/api/equity-stockIndices"


# =============================================================================
# Initialization tests
# =============================================================================


class TestNseSessionInit:
    """NseSession 初期化のテスト。"""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """デフォルトの NseConfig / RetryConfig で初期化されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            session = NseSession()

        assert session._config is not None
        assert session._retry_config is not None
        assert isinstance(session._config, NseConfig)
        assert isinstance(session._retry_config, RetryConfig)

    def test_正常系_カスタムconfigで初期化できる(self) -> None:
        """カスタム NseConfig で初期化されること。"""
        config = NseConfig(polite_delay=1.0, timeout=60.0)
        retry_config = RetryConfig(max_attempts=5, initial_delay=0.5)

        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            session = NseSession(config=config, retry_config=retry_config)

        assert session._config.polite_delay == 1.0
        assert session._config.timeout == 60.0
        assert session._retry_config.max_attempts == 5
        assert session._retry_config.initial_delay == 0.5

    def test_正常系_httpx_Clientがfollow_redirects付きで生成される(self) -> None:
        """httpx.Client が follow_redirects=True で生成されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            NseSession()
            call_kwargs = mock_client_cls.call_args
            assert call_kwargs[1].get("follow_redirects") is True

    def test_正常系_初期化時Cookie未取得状態(self) -> None:
        """初期化時に _cookie_acquired_at が 0.0 であること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            session = NseSession()

        assert session._cookie_acquired_at == 0.0


# =============================================================================
# Context manager tests
# =============================================================================


class TestNseSessionContextManager:
    """NseSession context manager のテスト。"""

    def test_正常系_context_managerとして使用できる(self) -> None:
        """with 文で使用できること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            with NseSession() as session:
                assert isinstance(session, NseSession)

            mock_client.close.assert_called_once()

    def test_正常系_例外発生時もcloseが呼ばれる(self) -> None:
        """例外発生時もセッションが閉じられること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            with (
                pytest.raises(ValueError, match="test error"),
                NseSession() as _session,
            ):
                raise ValueError("test error")

            mock_client.close.assert_called_once()


# =============================================================================
# _ensure_cookies() tests
# =============================================================================


class TestNseSessionEnsureCookies:
    """NseSession._ensure_cookies() のテスト。"""

    def test_正常系_Cookie未取得時に初回取得する(self) -> None:
        """Cookie 未取得時に BASE_URL へ GET リクエストを送ること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=100.0),
            ):
                session = NseSession()
                session._ensure_cookies()

            # Should have called GET on BASE_URL to get cookies
            calls = [c[0][0] for c in mock_client.get.call_args_list]
            assert BASE_URL in calls

    def test_正常系_Cookie取得後_cookie_acquired_atが設定される(self) -> None:
        """Cookie 取得後に _cookie_acquired_at が更新されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=500.0),
            ):
                session = NseSession()
                session._ensure_cookies()
                assert session._cookie_acquired_at == 500.0

    def test_正常系_Cookie有効期限内は再取得しない(self) -> None:
        """Cookie が有効期限内であれば BASE_URL へのリクエストをスキップすること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=100.0),
            ):
                session = NseSession()
                # Simulate cookie already obtained 1 second ago
                session._cookie_acquired_at = 99.0  # 1 second ago, well within TTL
                mock_client.get.reset_mock()

                session._ensure_cookies()

            # Should NOT have called GET again (cookie still valid)
            mock_client.get.assert_not_called()

    def test_正常系_Cookie_TTL切れで再取得する(self) -> None:
        """Cookie TTL が切れていれば BASE_URL を再取得すること。"""
        config = NseConfig(cookie_refresh_interval=300.0)

        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=600.0),
            ):
                session = NseSession(config=config)
                # Simulate cookie obtained 301 seconds ago (expired)
                session._cookie_acquired_at = 299.0  # 301 seconds ago
                mock_client.get.reset_mock()

                session._ensure_cookies()

            # Should have refreshed cookie
            calls = [c[0][0] for c in mock_client.get.call_args_list]
            assert BASE_URL in calls

    def test_正常系_Cookie取得タイムアウトでフォールバック(self) -> None:
        """Cookie 取得がタイムアウトしても _cookie_acquired_at が設定されること。"""
        import httpx

        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.ReadTimeout("timed out")
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=100.0),
            ):
                session = NseSession()
                session._ensure_cookies()

                # Should mark as acquired despite timeout
                assert session._cookie_acquired_at == 100.0

    def test_正常系_Cookie取得403でフォールバック(self) -> None:
        """Cookie 取得が 403 でも _cookie_acquired_at が設定されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=200.0),
            ):
                session = NseSession()
                session._ensure_cookies()

                # Should mark as acquired despite 403
                assert session._cookie_acquired_at == 200.0


# =============================================================================
# get() tests
# =============================================================================


class TestNseSessionGet:
    """NseSession.get() のテスト。"""

    def test_正常系_正常なレスポンスを返却する(
        self, mock_httpx_response_200: MagicMock
    ) -> None:
        """200 レスポンスが正常に返却されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_httpx_response_200
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                # Pre-set cookie to skip cookie refresh
                session._cookie_acquired_at = 0.0
                with patch.object(session, "_ensure_cookies"):
                    response = session.get(_TEST_URL)

            assert response.status_code == 200

    def test_正常系_ensure_cookiesが呼ばれる(self) -> None:
        """get() 実行時に _ensure_cookies() が呼ばれること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with patch.object(session, "_ensure_cookies") as mock_ensure_cookies:
                    session.get(_TEST_URL)

                mock_ensure_cookies.assert_called_once()

    def test_正常系_polite_delayがmonotonic制御で適用される(self) -> None:
        """polite_delay が time.monotonic() ベースで適用されること。"""
        config = NseConfig(polite_delay=2.0, delay_jitter=0.0)

        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep") as mock_sleep,
                patch(
                    "market.nse.session.time.monotonic",
                    side_effect=[100.0, 100.0, 100.5, 100.5],
                ),
                patch("market.nse.session.random.uniform", return_value=0.0),
            ):
                session = NseSession(config=config)
                with patch.object(session, "_ensure_cookies"):
                    # First request: no delay
                    session.get(_TEST_URL)
                    # Second request: should wait remaining polite_delay
                    session.get(_TEST_URL)

                # Second call should sleep for remaining delay (2.0 - 0.5 = 1.5)
                assert mock_sleep.call_count >= 1
                delay_calls = [
                    c[0][0] for c in mock_sleep.call_args_list if c[0][0] > 1.0
                ]
                assert len(delay_calls) >= 1
                assert delay_calls[0] == pytest.approx(1.5, abs=0.01)

    def test_正常系_polite_delay経過済みでsleepスキップ(self) -> None:
        """十分な時間が経過していれば sleep がスキップされること。"""
        config = NseConfig(polite_delay=0.1, delay_jitter=0.0)

        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep") as mock_sleep,
                patch(
                    "market.nse.session.time.monotonic",
                    side_effect=[100.0, 100.0, 101.0, 101.0],
                ),
                patch("market.nse.session.random.uniform", return_value=0.0),
            ):
                session = NseSession(config=config)
                with patch.object(session, "_ensure_cookies"):
                    session.get(_TEST_URL)
                    session.get(_TEST_URL)

                polite_sleeps = [
                    c[0][0] for c in mock_sleep.call_args_list if c[0][0] > 0
                ]
                assert len(polite_sleeps) == 0

    def test_正常系_User_Agentヘッダーが設定される(self) -> None:
        """ランダムな User-Agent がヘッダーに設定されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
                patch(
                    "market.nse.session.random.choice",
                    return_value="MockUserAgent/1.0",
                ),
            ):
                session = NseSession()
                with patch.object(session, "_ensure_cookies"):
                    session.get(_TEST_URL)

                # Find the call for the API URL (not BASE_URL cookie fetch)
                api_calls = [
                    c for c in mock_client.get.call_args_list if c[0][0] == _TEST_URL
                ]
                assert len(api_calls) >= 1
                headers = api_calls[-1][1]["headers"]
                assert headers["User-Agent"] == "MockUserAgent/1.0"

    def test_正常系_デフォルトヘッダーが含まれる(self) -> None:
        """DEFAULT_HEADERS の項目がヘッダーに含まれること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with patch.object(session, "_ensure_cookies"):
                    session.get(_TEST_URL)

                api_calls = [
                    c for c in mock_client.get.call_args_list if c[0][0] == _TEST_URL
                ]
                assert len(api_calls) >= 1
                headers = api_calls[-1][1]["headers"]
                for key, value in DEFAULT_HEADERS.items():
                    if key == "User-Agent":
                        assert "User-Agent" in headers
                    else:
                        assert headers[key] == value

    def test_正常系_paramsがhttpxに渡される(self) -> None:
        """params が httpx.Client.get に渡されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with patch.object(session, "_ensure_cookies"):
                    session.get(_TEST_URL, params={"index": "NIFTY 50"})

                api_calls = [
                    c for c in mock_client.get.call_args_list if c[0][0] == _TEST_URL
                ]
                assert len(api_calls) >= 1
                assert api_calls[-1][1]["params"] == {"index": "NIFTY 50"}

    def test_正常系_timeoutが設定される(self) -> None:
        """config.timeout がリクエストに渡されること。"""
        config = NseConfig(timeout=15.0)

        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession(config=config)
                with patch.object(session, "_ensure_cookies"):
                    session.get(_TEST_URL)

                api_calls = [
                    c for c in mock_client.get.call_args_list if c[0][0] == _TEST_URL
                ]
                assert len(api_calls) >= 1
                assert api_calls[-1][1]["timeout"] == 15.0

    def test_異常系_429レスポンスでNseRateLimitError(
        self, mock_httpx_response_429: MagicMock
    ) -> None:
        """429 レスポンスで NseRateLimitError が発生すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_httpx_response_429
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with (
                    patch.object(session, "_ensure_cookies"),
                    pytest.raises(NseRateLimitError) as exc_info,
                ):
                    session.get(_TEST_URL)

                assert exc_info.value.url == _TEST_URL

    def test_異常系_403レスポンスでNseCookieError(
        self, mock_httpx_response_403: MagicMock
    ) -> None:
        """403 レスポンスで NseCookieError が発生すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_httpx_response_403
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with (
                    patch.object(session, "_ensure_cookies"),
                    pytest.raises(NseCookieError) as exc_info,
                ):
                    session.get(_TEST_URL)

                assert exc_info.value.url == _TEST_URL

    def test_異常系_5xxレスポンスでNseAPIError(
        self, mock_httpx_response_500: MagicMock
    ) -> None:
        """500 レスポンスで NseAPIError が発生すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_httpx_response_500
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with (
                    patch.object(session, "_ensure_cookies"),
                    pytest.raises(NseAPIError) as exc_info,
                ):
                    session.get(_TEST_URL)

                assert exc_info.value.status_code == 500


# =============================================================================
# URL whitelist validation tests
# =============================================================================


class TestNseSessionURLWhitelist:
    """NseSession URL ホワイトリスト検証のテスト。"""

    def test_正常系_許可されたホストへのリクエストが成功する(self) -> None:
        """ALLOWED_HOSTS に含まれるホストへのリクエストが成功すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with patch.object(session, "_ensure_cookies"):
                    response = session.get(_TEST_URL)

            assert response.status_code == 200

    def test_異常系_不正なホストへのリクエストがValueErrorで拒否される(self) -> None:
        """ALLOWED_HOSTS に含まれないホストが ValueError で拒否されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value = MagicMock()

            session = NseSession()

            with pytest.raises(ValueError, match="not in allowed hosts"):
                session.get("https://evil.example.com/api/data")

    def test_異常系_ホストなしURLがValueErrorで拒否される(self) -> None:
        """ホストが空の URL が ValueError で拒否されること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value = MagicMock()

            session = NseSession()

            with pytest.raises(ValueError, match="URL scheme must be"):
                session.get("/relative/path/only")

    def test_正常系_ALLOWED_HOSTSにwww_nseindia_comが含まれる(self) -> None:
        """ALLOWED_HOSTS に www.nseindia.com が含まれていること。"""
        assert "www.nseindia.com" in ALLOWED_HOSTS

    def test_正常系_ALLOWED_HOSTSがfrozensetである(self) -> None:
        """ALLOWED_HOSTS が frozenset であること。"""
        assert isinstance(ALLOWED_HOSTS, frozenset)


# =============================================================================
# get_with_retry() tests
# =============================================================================


class TestNseSessionGetWithRetry:
    """NseSession.get_with_retry() のテスト。"""

    def test_正常系_成功時はリトライなし(self) -> None:
        """最初の試行で成功した場合リトライしないこと。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession()
                with patch.object(session, "_ensure_cookies"):
                    response = session.get_with_retry(_TEST_URL)

            assert response.status_code == 200
            assert mock_client.get.call_count == 1

    def test_正常系_失敗後リトライで成功(self) -> None:
        """失敗後にリトライで成功すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.text = "Too Many Requests"
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            mock_client.get.side_effect = [
                mock_response_429,
                mock_response_ok,
            ]
            mock_client_cls.return_value = mock_client

            retry_config = RetryConfig(max_attempts=3, initial_delay=0.01)

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession(retry_config=retry_config)
                with patch.object(session, "_ensure_cookies"):
                    response = session.get_with_retry(_TEST_URL)

            assert response.status_code == 200

    def test_異常系_全リトライ失敗でNseRateLimitError(self) -> None:
        """全リトライが失敗した場合 NseRateLimitError が発生すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.text = "Too Many Requests"
            mock_client.get.return_value = mock_response_429
            mock_client_cls.return_value = mock_client

            retry_config = RetryConfig(max_attempts=2, initial_delay=0.01)

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=0.0),
            ):
                session = NseSession(retry_config=retry_config)
                with (
                    patch.object(session, "_ensure_cookies"),
                    pytest.raises(NseRateLimitError),
                ):
                    session.get_with_retry(_TEST_URL)

    def test_正常系_指数バックオフでディレイが増加する(self) -> None:
        """リトライ間のディレイが指数バックオフで増加すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.text = "Too Many Requests"
            mock_client.get.return_value = mock_response_429
            mock_client_cls.return_value = mock_client

            retry_config = RetryConfig(
                max_attempts=3,
                initial_delay=1.0,
                exponential_base=2.0,
                jitter=False,
            )

            sleep_calls: list[float] = []

            def track_sleep(duration: float) -> None:
                sleep_calls.append(duration)

            with patch("market.nse.session.time") as mock_time:
                mock_time.monotonic.return_value = 0.0
                mock_time.sleep.side_effect = track_sleep

                session = NseSession(retry_config=retry_config)
                with (
                    patch.object(session, "_ensure_cookies"),
                    pytest.raises(NseRateLimitError),
                ):
                    session.get_with_retry(_TEST_URL)

            retry_delays = [d for d in sleep_calls if d >= 1.0]
            assert len(retry_delays) >= 2

    def test_正常系_max_delay上限でクリップされる(self) -> None:
        """max_delay が指数バックオフの上限としてクリップされること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.text = "Too Many Requests"
            mock_client.get.return_value = mock_response_429
            mock_client_cls.return_value = mock_client

            retry_config = RetryConfig(
                max_attempts=3,
                initial_delay=1.0,
                max_delay=5.0,
                exponential_base=10.0,
                jitter=False,
            )

            sleep_calls: list[float] = []

            def track_sleep(duration: float) -> None:
                sleep_calls.append(duration)

            with patch("market.nse.session.time") as mock_time:
                mock_time.monotonic.return_value = 0.0
                mock_time.sleep.side_effect = track_sleep

                session = NseSession(retry_config=retry_config)
                with (
                    patch.object(session, "_ensure_cookies"),
                    pytest.raises(NseRateLimitError),
                ):
                    session.get_with_retry(_TEST_URL)

            retry_delays = [d for d in sleep_calls if d >= 1.0]
            assert len(retry_delays) >= 2
            for delay in retry_delays:
                assert delay <= 5.0 + 0.01

    def test_正常系_NseCookieError時にCookieリフレッシュしてリトライする(self) -> None:
        """403 によって NseCookieError が発生した場合、Cookie をリフレッシュしてリトライすること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response_403 = MagicMock()
            mock_response_403.status_code = 403
            mock_response_403.text = "Forbidden"
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            mock_client.get.side_effect = [
                mock_response_403,
                mock_response_ok,  # After cookie refresh
            ]
            mock_client_cls.return_value = mock_client

            retry_config = RetryConfig(max_attempts=3, initial_delay=0.01)

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=100.0),
            ):
                session = NseSession(retry_config=retry_config)
                with patch.object(session, "_ensure_cookies") as mock_ensure:
                    # First call gets 403, second should succeed after cookie refresh
                    response = session.get_with_retry(_TEST_URL)

            assert response.status_code == 200
            # _ensure_cookies should have been called again for cookie refresh
            assert mock_ensure.call_count >= 2

    def test_正常系_NseCookieError後リトライ成功(self) -> None:
        """NseCookieError 発生後にリトライが成功すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            # Need 3 responses: 403 (API call), 200 (cookie refresh), 200 (API retry)
            mock_response_403 = MagicMock()
            mock_response_403.status_code = 403
            mock_response_403.text = "Forbidden"
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            mock_client.get.side_effect = [
                mock_response_403,  # First API call returns 403
                mock_response_ok,  # Cookie refresh (BASE_URL) returns 200
                mock_response_ok,  # Retry API call returns 200
            ]
            mock_client_cls.return_value = mock_client

            retry_config = RetryConfig(max_attempts=3, initial_delay=0.01)

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=100.0),
            ):
                session = NseSession(retry_config=retry_config)
                # Pre-set cookie as acquired so initial _ensure_cookies skips
                session._cookie_acquired_at = 99.0  # 1 second ago, within TTL

                response = session.get_with_retry(_TEST_URL)

            assert response.status_code == 200
            # _cookie_acquired_at should have been reset to 0.0 on NseCookieError
            # and then set again after successful cookie refresh
            assert session._cookie_acquired_at > 0.0

    def test_異常系_全リトライ失敗でNseCookieError(self) -> None:
        """全リトライが NseCookieError で失敗した場合 NseCookieError が発生すること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response_403 = MagicMock()
            mock_response_403.status_code = 403
            mock_response_403.text = "Forbidden"
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            # Flow: API→403 (attempt 1), cookie_refresh→200, API→403 (attempt 2)
            # Cookie is pre-set as valid, so initial _ensure_cookies is skipped.
            # On CookieError, _cookie_acquired_at is reset to 0.0 and next
            # _ensure_cookies call consumes mock_response_ok (cookie refresh).
            mock_client.get.side_effect = [
                mock_response_403,  # 1st API attempt → NseCookieError
                mock_response_ok,  # Cookie refresh before 2nd attempt
                mock_response_403,  # 2nd API attempt → NseCookieError
            ]
            mock_client_cls.return_value = mock_client

            retry_config = RetryConfig(max_attempts=2, initial_delay=0.01)

            with (
                patch("market.nse.session.time.sleep"),
                patch("market.nse.session.time.monotonic", return_value=100.0),
            ):
                session = NseSession(retry_config=retry_config)
                # Pre-set cookie as recently acquired to skip initial _ensure_cookies
                session._cookie_acquired_at = 99.0  # 1 second ago, within TTL
                with pytest.raises(NseCookieError):
                    session.get_with_retry(_TEST_URL)

    def test_正常系_jitter有効時にバックオフ遅延がランダム範囲内(self) -> None:
        """jitter=True（デフォルト）のとき sleep 値が期待範囲内であること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.text = "Too Many Requests"
            mock_client.get.return_value = mock_response_429
            mock_client_cls.return_value = mock_client

            initial_delay = 1.0
            retry_config = RetryConfig(
                max_attempts=2,
                initial_delay=initial_delay,
                exponential_base=2.0,
                jitter=True,  # AIDEV-NOTE: default; verify random sleep stays in range
                max_delay=60.0,
            )

            sleep_calls: list[float] = []

            def track_sleep(duration: float) -> None:
                sleep_calls.append(duration)

            with (
                patch("market.nse.session.time.monotonic", return_value=0.0),
                patch("market.nse.session.time.sleep", side_effect=track_sleep),
            ):
                session = NseSession(retry_config=retry_config)
                with (
                    patch.object(session, "_ensure_cookies"),
                    pytest.raises(NseRateLimitError),
                ):
                    session.get_with_retry(_TEST_URL)

            # At least one backoff sleep should have occurred
            retry_delays = [d for d in sleep_calls if d > 0]
            assert len(retry_delays) >= 1
            # With jitter, delay should not exceed max_delay
            for delay in retry_delays:
                assert delay <= retry_config.max_delay + 0.01


# =============================================================================
# close() tests
# =============================================================================


class TestNseSessionClose:
    """NseSession.close() のテスト。"""

    def test_正常系_セッションが閉じられる(self) -> None:
        """close() でセッションが閉じられること。"""
        with patch("market.nse.session.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            session = NseSession()
            session.close()

            mock_client.close.assert_called_once()


# =============================================================================
# Logging tests
# =============================================================================


class TestNseSessionLogging:
    """NseSession のロギングテスト。"""

    def test_正常系_loggerが定義されている(self) -> None:
        """モジュールレベルで structlog ロガーが定義されていること。"""
        import market.nse.session as session_module

        assert hasattr(session_module, "logger")


# =============================================================================
# __all__ export tests
# =============================================================================


class TestModuleExports:
    """__all__ エクスポートのテスト。"""

    def test_正常系_NseSessionがエクスポートされている(self) -> None:
        """__all__ に NseSession が含まれていること。"""
        from market.nse.session import __all__

        assert "NseSession" in __all__
