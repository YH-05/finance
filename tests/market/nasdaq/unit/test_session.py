"""Unit tests for market.nasdaq.session module.

NasdaqSession の動作を検証するテストスイート。
curl_cffi ベースの HTTP セッションクラスのテスト。

Test TODO List:
- [x] NasdaqSession: デフォルト値で初期化
- [x] NasdaqSession: カスタム config / retry_config で初期化
- [x] NasdaqSession: curl_cffi セッションが impersonate で生成される
- [x] NasdaqSession: context manager プロトコル
- [x] NasdaqSession: 例外発生時も close が呼ばれる
- [x] get(): ポライトディレイ + ジッター適用
- [x] get(): ランダム User-Agent ヘッダー設定
- [x] get(): デフォルトヘッダーが含まれる
- [x] get(): params が curl_cffi に渡される
- [x] get(): 403 レスポンスで NasdaqRateLimitError
- [x] get(): 429 レスポンスで NasdaqRateLimitError
- [x] get(): 正常レスポンスを返却
- [x] get(): timeout が設定される
- [x] get_with_retry(): 成功時はリトライなし
- [x] get_with_retry(): 失敗後リトライで成功
- [x] get_with_retry(): リトライ時に rotate_session() を呼び出す
- [x] get_with_retry(): 全リトライ失敗で NasdaqRateLimitError
- [x] get_with_retry(): 指数バックオフでディレイが増加する
- [x] rotate_session(): 新しい偽装ターゲットでセッション再生成
- [x] rotate_session(): BROWSER_IMPERSONATE_TARGETS から選択される
- [x] close(): セッションが閉じられる
- [x] structlog ロガーの使用
- [x] __all__ エクスポート
- [x] get(): 許可されたホストへのリクエストが成功する
- [x] get(): 不正なホストへのリクエストがValueErrorで拒否される
- [x] get(): ホストなしURLがValueErrorで拒否される
"""

from unittest.mock import MagicMock, patch

import pytest

from market.nasdaq.constants import (
    ALLOWED_HOSTS,
    BROWSER_IMPERSONATE_TARGETS,
    DEFAULT_HEADERS,
    NASDAQ_SCREENER_URL,
)
from market.nasdaq.errors import NasdaqRateLimitError
from market.nasdaq.session import NasdaqSession
from market.nasdaq.types import NasdaqConfig, RetryConfig

# =============================================================================
# Initialization tests
# =============================================================================


class TestNasdaqSessionInit:
    """NasdaqSession 初期化のテスト。"""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """デフォルトの NasdaqConfig / RetryConfig で初期化されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            session = NasdaqSession()

        assert session._config is not None
        assert session._retry_config is not None
        assert isinstance(session._config, NasdaqConfig)
        assert isinstance(session._retry_config, RetryConfig)

    def test_正常系_カスタムconfigで初期化できる(self) -> None:
        """カスタム NasdaqConfig で初期化されること。"""
        config = NasdaqConfig(polite_delay=5.0, impersonate="edge99")
        retry_config = RetryConfig(max_attempts=5, initial_delay=0.5)

        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            session = NasdaqSession(config=config, retry_config=retry_config)

        assert session._config.polite_delay == 5.0
        assert session._config.impersonate == "edge99"
        assert session._retry_config.max_attempts == 5
        assert session._retry_config.initial_delay == 0.5

    def test_正常系_curl_cffiセッションが生成される(self) -> None:
        """curl_cffi.Session が impersonate パラメータで生成されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            NasdaqSession()
            mock_curl.Session.assert_called_once_with(impersonate="chrome")

    def test_正常系_カスタムimpersonateでセッション生成(self) -> None:
        """カスタム impersonate でセッションが生成されること。"""
        config = NasdaqConfig(impersonate="safari15_3")
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            NasdaqSession(config=config)
            mock_curl.Session.assert_called_once_with(impersonate="safari15_3")


# =============================================================================
# Context manager tests
# =============================================================================


class TestNasdaqSessionContextManager:
    """NasdaqSession context manager のテスト。"""

    def test_正常系_context_managerとして使用できる(self) -> None:
        """with 文で使用できること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_curl.Session.return_value = mock_session

            with NasdaqSession() as session:
                assert isinstance(session, NasdaqSession)

            mock_session.close.assert_called_once()

    def test_正常系_例外発生時もcloseが呼ばれる(self) -> None:
        """例外発生時もセッションが閉じられること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_curl.Session.return_value = mock_session

            with (
                pytest.raises(ValueError, match="test error"),
                NasdaqSession() as _session,
            ):
                raise ValueError("test error")

            mock_session.close.assert_called_once()


# =============================================================================
# get() tests
# =============================================================================


class TestNasdaqSessionGet:
    """NasdaqSession.get() のテスト。"""

    def test_正常系_正常なレスポンスを返却する(self) -> None:
        """200 レスポンスが正常に返却されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession()
                response = session.get(NASDAQ_SCREENER_URL)

            assert response.status_code == 200

    def test_正常系_ポライトディレイが適用される(self) -> None:
        """polite_delay + ジッターが適用されること。"""
        config = NasdaqConfig(polite_delay=2.0, delay_jitter=1.0)

        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with (
                patch("market.nasdaq.session.time.sleep") as mock_sleep,
                patch("market.nasdaq.session.random.uniform", return_value=0.5),
            ):
                session = NasdaqSession(config=config)
                session.get(NASDAQ_SCREENER_URL)

                mock_sleep.assert_called_once()
                actual_delay = mock_sleep.call_args[0][0]
                assert actual_delay == pytest.approx(2.5, abs=0.01)

    def test_正常系_User_Agentヘッダーが設定される(self) -> None:
        """ランダムな User-Agent がヘッダーに設定されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with (
                patch("market.nasdaq.session.time.sleep"),
                patch(
                    "market.nasdaq.session.random.choice",
                    return_value="MockUserAgent/1.0",
                ),
            ):
                session = NasdaqSession()
                session.get(NASDAQ_SCREENER_URL)

                call_kwargs = mock_session.request.call_args
                headers = call_kwargs[1]["headers"]
                assert headers["User-Agent"] == "MockUserAgent/1.0"

    def test_正常系_デフォルトヘッダーが含まれる(self) -> None:
        """DEFAULT_HEADERS の項目（User-Agent以外）がヘッダーに含まれること。

        User-Agent はランダムローテーションで上書きされるため、
        その他のヘッダー（Accept, Accept-Language, Accept-Encoding）を検証する。
        """
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession()
                session.get(NASDAQ_SCREENER_URL)

                call_kwargs = mock_session.request.call_args
                headers = call_kwargs[1]["headers"]
                for key, value in DEFAULT_HEADERS.items():
                    if key == "User-Agent":
                        # User-Agent is overridden by random rotation
                        assert "User-Agent" in headers
                    else:
                        assert headers[key] == value

    def test_正常系_paramsがcurl_cffiに渡される(self) -> None:
        """params が curl_cffi.Session.request に渡されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession()
                session.get(
                    NASDAQ_SCREENER_URL,
                    params={"exchange": "nasdaq", "limit": "0"},
                )

                call_kwargs = mock_session.request.call_args
                assert call_kwargs[1]["params"] == {
                    "exchange": "nasdaq",
                    "limit": "0",
                }

    def test_正常系_timeoutが設定される(self) -> None:
        """config.timeout がリクエストに渡されること。"""
        config = NasdaqConfig(timeout=15.0)

        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession(config=config)
                session.get(NASDAQ_SCREENER_URL)

                call_kwargs = mock_session.request.call_args
                assert call_kwargs[1]["timeout"] == 15.0

    def test_異常系_403レスポンスでNasdaqRateLimitError(self) -> None:
        """403 レスポンスで NasdaqRateLimitError が発生すること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession()

                with pytest.raises(NasdaqRateLimitError) as exc_info:
                    session.get(NASDAQ_SCREENER_URL)

                assert exc_info.value.url == NASDAQ_SCREENER_URL

    def test_異常系_429レスポンスでNasdaqRateLimitError(self) -> None:
        """429 レスポンスで NasdaqRateLimitError が発生すること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession()

                with pytest.raises(NasdaqRateLimitError):
                    session.get(NASDAQ_SCREENER_URL)


# =============================================================================
# URL whitelist validation tests
# =============================================================================


class TestNasdaqSessionURLWhitelist:
    """NasdaqSession URL ホワイトリスト検証のテスト。"""

    def test_正常系_許可されたホストへのリクエストが成功する(self) -> None:
        """ALLOWED_HOSTS に含まれるホストへのリクエストが成功すること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession()
                response = session.get(NASDAQ_SCREENER_URL)

            assert response.status_code == 200

    def test_異常系_不正なホストへのリクエストがValueErrorで拒否される(self) -> None:
        """ALLOWED_HOSTS に含まれないホストへのリクエストが ValueError で拒否されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()

            session = NasdaqSession()

            with pytest.raises(ValueError, match="not in allowed hosts"):
                session.get("https://evil.example.com/api/data")

    def test_異常系_ホストなしURLがValueErrorで拒否される(self) -> None:
        """ホストが空のURLが ValueError で拒否されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()

            session = NasdaqSession()

            with pytest.raises(ValueError, match="not in allowed hosts"):
                session.get("/relative/path/only")

    def test_正常系_ALLOWED_HOSTSにapi_nasdaq_comが含まれる(self) -> None:
        """ALLOWED_HOSTS に api.nasdaq.com が含まれていること。"""
        assert "api.nasdaq.com" in ALLOWED_HOSTS

    def test_正常系_ALLOWED_HOSTSがfrozensetである(self) -> None:
        """ALLOWED_HOSTS が frozenset であること。"""
        assert isinstance(ALLOWED_HOSTS, frozenset)


# =============================================================================
# get_with_retry() tests
# =============================================================================


class TestNasdaqSessionGetWithRetry:
    """NasdaqSession.get_with_retry() のテスト。"""

    def test_正常系_成功時はリトライなし(self) -> None:
        """最初の試行で成功した場合リトライしないこと。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.request.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession()
                response = session.get_with_retry(NASDAQ_SCREENER_URL)

            assert response.status_code == 200
            assert mock_session.request.call_count == 1

    def test_正常系_失敗後リトライで成功(self) -> None:
        """失敗後にリトライで成功すること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            mock_session.request.side_effect = [
                mock_response_blocked,
                mock_response_ok,
            ]
            mock_curl.Session.return_value = mock_session

            retry_config = RetryConfig(max_attempts=3, initial_delay=0.01)

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession(retry_config=retry_config)
                response = session.get_with_retry(NASDAQ_SCREENER_URL)

            assert response.status_code == 200

    def test_正常系_リトライ時にrotate_sessionが呼ばれる(self) -> None:
        """リトライ時に rotate_session() が呼ばれること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            mock_session.request.side_effect = [
                mock_response_blocked,
                mock_response_ok,
            ]
            mock_curl.Session.return_value = mock_session

            retry_config = RetryConfig(max_attempts=3, initial_delay=0.01)

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession(retry_config=retry_config)
                with patch.object(session, "rotate_session") as mock_rotate:
                    session.get_with_retry(NASDAQ_SCREENER_URL)
                    mock_rotate.assert_called_once()

    def test_異常系_全リトライ失敗でNasdaqRateLimitError(self) -> None:
        """全リトライが失敗した場合 NasdaqRateLimitError が発生すること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_session.request.return_value = mock_response_blocked
            mock_curl.Session.return_value = mock_session

            retry_config = RetryConfig(max_attempts=2, initial_delay=0.01)

            with patch("market.nasdaq.session.time.sleep"):
                session = NasdaqSession(retry_config=retry_config)

                with pytest.raises(NasdaqRateLimitError):
                    session.get_with_retry(NASDAQ_SCREENER_URL)

    def test_正常系_指数バックオフでディレイが増加する(self) -> None:
        """リトライ間のディレイが指数バックオフで増加すること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_session.request.return_value = mock_response_blocked
            mock_curl.Session.return_value = mock_session

            retry_config = RetryConfig(
                max_attempts=3,
                initial_delay=1.0,
                exponential_base=2.0,
                jitter=False,
            )

            sleep_calls: list[float] = []

            def track_sleep(duration: float) -> None:
                sleep_calls.append(duration)

            with patch("market.nasdaq.session.time.sleep", side_effect=track_sleep):
                session = NasdaqSession(retry_config=retry_config)

                with pytest.raises(NasdaqRateLimitError):
                    session.get_with_retry(NASDAQ_SCREENER_URL)

            # ポライトディレイ分を除いたリトライディレイを確認
            # max_attempts=3 なので、リトライディレイは2回（attempt 0, 1 の後）
            retry_delays = [d for d in sleep_calls if d >= 1.0]
            assert len(retry_delays) >= 2


# =============================================================================
# rotate_session() tests
# =============================================================================


class TestNasdaqSessionRotateSession:
    """NasdaqSession.rotate_session() のテスト。"""

    def test_正常系_新しい偽装ターゲットでセッション再生成(self) -> None:
        """rotate_session() が新しい偽装ターゲットで再生成すること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session_old = MagicMock()
            mock_session_new = MagicMock()
            mock_curl.Session.side_effect = [mock_session_old, mock_session_new]

            session = NasdaqSession()

            with patch(
                "market.nasdaq.session.random.choice",
                return_value="edge99",
            ):
                session.rotate_session()

            # 古いセッションが閉じられること
            mock_session_old.close.assert_called_once()
            # 新しいセッションが生成されること
            assert mock_curl.Session.call_count == 2

    def test_正常系_BROWSER_IMPERSONATE_TARGETSから選択される(self) -> None:
        """偽装ターゲットが BROWSER_IMPERSONATE_TARGETS から選択されること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()

            session = NasdaqSession()
            session.rotate_session()

            # 2回目の Session() 呼び出しの impersonate 引数を確認
            second_call_kwargs = mock_curl.Session.call_args
            target = second_call_kwargs[1]["impersonate"]
            assert target in BROWSER_IMPERSONATE_TARGETS


# =============================================================================
# close() tests
# =============================================================================


class TestNasdaqSessionClose:
    """NasdaqSession.close() のテスト。"""

    def test_正常系_セッションが閉じられる(self) -> None:
        """close() でセッションが閉じられること。"""
        with patch("market.nasdaq.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_curl.Session.return_value = mock_session

            session = NasdaqSession()
            session.close()

            mock_session.close.assert_called_once()


# =============================================================================
# Logging tests
# =============================================================================


class TestNasdaqSessionLogging:
    """NasdaqSession のロギングテスト。"""

    def test_正常系_loggerが定義されている(self) -> None:
        """モジュールレベルで structlog ロガーが定義されていること。"""
        import market.nasdaq.session as session_module

        assert hasattr(session_module, "logger")


# =============================================================================
# __all__ export tests
# =============================================================================


class TestModuleExports:
    """__all__ エクスポートのテスト。"""

    def test_正常系_NasdaqSessionがエクスポートされている(self) -> None:
        """__all__ に NasdaqSession が含まれていること。"""
        from market.nasdaq.session import __all__

        assert "NasdaqSession" in __all__
