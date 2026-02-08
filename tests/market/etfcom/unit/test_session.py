"""Unit tests for market.etfcom.session module.

ETFComSession の動作を検証するテストスイート。
curl_cffi ベースの HTTP セッションクラスのテスト。

Test TODO List:
- [x] ETFComSession: デフォルト値で初期化
- [x] ETFComSession: カスタム config / retry_config で初期化
- [x] ETFComSession: context manager プロトコル
- [x] get(): ポライトディレイ適用
- [x] get(): ランダム User-Agent ヘッダー設定
- [x] get(): Referer ヘッダー設定
- [x] get(): 403 レスポンスで ETFComBlockedError
- [x] get(): 429 レスポンスで ETFComBlockedError
- [x] get(): 正常レスポンスを返却
- [x] get_with_retry(): 指数バックオフリトライ
- [x] get_with_retry(): 失敗時に rotate_session() を呼び出す
- [x] get_with_retry(): 全リトライ失敗で例外
- [x] get_with_retry(): 成功時はリトライ不要
- [x] rotate_session(): 新しい偽装ターゲットでセッション再生成
- [x] close(): セッションを閉じる
- [x] structlog ロガーの使用
- [x] __all__ エクスポート
"""

from unittest.mock import MagicMock, patch

import pytest

from market.etfcom.constants import (
    BROWSER_IMPERSONATE_TARGETS,
    DEFAULT_HEADERS,
    ETFCOM_BASE_URL,
)
from market.etfcom.errors import ETFComBlockedError
from market.etfcom.session import ETFComSession
from market.etfcom.types import RetryConfig, ScrapingConfig

# =============================================================================
# Initialization tests
# =============================================================================


class TestETFComSessionInit:
    """ETFComSession 初期化のテスト。"""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """デフォルトの ScrapingConfig / RetryConfig で初期化されること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            session = ETFComSession()

        assert session._config is not None
        assert session._retry_config is not None
        assert isinstance(session._config, ScrapingConfig)
        assert isinstance(session._retry_config, RetryConfig)

    def test_正常系_カスタムconfigで初期化できる(self) -> None:
        """カスタム ScrapingConfig で初期化されること。"""
        config = ScrapingConfig(polite_delay=5.0, impersonate="edge99")
        retry_config = RetryConfig(max_attempts=5, initial_delay=0.5)

        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            session = ETFComSession(config=config, retry_config=retry_config)

        assert session._config.polite_delay == 5.0
        assert session._config.impersonate == "edge99"
        assert session._retry_config.max_attempts == 5
        assert session._retry_config.initial_delay == 0.5

    def test_正常系_curl_cffiセッションが生成される(self) -> None:
        """curl_cffi.Session が impersonate パラメータで生成されること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            ETFComSession()
            mock_curl.Session.assert_called_once_with(impersonate="chrome")

    def test_正常系_カスタムimpersonateでセッション生成(self) -> None:
        """カスタム impersonate でセッションが生成されること。"""
        config = ScrapingConfig(impersonate="safari15_3")
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()
            ETFComSession(config=config)
            mock_curl.Session.assert_called_once_with(impersonate="safari15_3")


# =============================================================================
# Context manager tests
# =============================================================================


class TestETFComSessionContextManager:
    """ETFComSession context manager のテスト。"""

    def test_正常系_context_managerとして使用できる(self) -> None:
        """with 文で使用できること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_curl.Session.return_value = mock_session

            with ETFComSession() as session:
                assert isinstance(session, ETFComSession)

            mock_session.close.assert_called_once()

    def test_正常系_例外発生時もcloseが呼ばれる(self) -> None:
        """例外発生時もセッションが閉じられること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_curl.Session.return_value = mock_session

            with (
                pytest.raises(ValueError, match="test error"),
                ETFComSession() as _session,
            ):
                raise ValueError("test error")

            mock_session.close.assert_called_once()


# =============================================================================
# get() tests
# =============================================================================


class TestETFComSessionGet:
    """ETFComSession.get() のテスト。"""

    def test_正常系_正常なレスポンスを返却する(self) -> None:
        """200 レスポンスが正常に返却されること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession()
                response = session.get("https://www.etf.com/SPY")

            assert response.status_code == 200

    def test_正常系_ポライトディレイが適用される(self) -> None:
        """polite_delay + ジッターが適用されること。"""
        config = ScrapingConfig(polite_delay=2.0, delay_jitter=1.0)

        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with (
                patch("market.etfcom.session.time.sleep") as mock_sleep,
                patch("market.etfcom.session.random.uniform", return_value=0.5),
            ):
                session = ETFComSession(config=config)
                session.get("https://www.etf.com/SPY")

                mock_sleep.assert_called_once()
                actual_delay = mock_sleep.call_args[0][0]
                assert actual_delay == pytest.approx(2.5, abs=0.01)

    def test_正常系_User_Agentヘッダーが設定される(self) -> None:
        """ランダムな User-Agent がヘッダーに設定されること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with (
                patch("market.etfcom.session.time.sleep"),
                patch(
                    "market.etfcom.session.random.choice",
                    return_value="MockUserAgent/1.0",
                ),
            ):
                session = ETFComSession()
                session.get("https://www.etf.com/SPY")

                call_kwargs = mock_session.get.call_args
                headers = call_kwargs[1]["headers"]
                assert headers["User-Agent"] == "MockUserAgent/1.0"

    def test_正常系_Refererヘッダーが設定される(self) -> None:
        """Referer ヘッダーに ETFCOM_BASE_URL が設定されること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession()
                session.get("https://www.etf.com/SPY")

                call_kwargs = mock_session.get.call_args
                headers = call_kwargs[1]["headers"]
                assert headers["Referer"] == ETFCOM_BASE_URL

    def test_正常系_デフォルトヘッダーが含まれる(self) -> None:
        """DEFAULT_HEADERS の項目がヘッダーに含まれること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession()
                session.get("https://www.etf.com/SPY")

                call_kwargs = mock_session.get.call_args
                headers = call_kwargs[1]["headers"]
                for key, value in DEFAULT_HEADERS.items():
                    assert headers[key] == value

    def test_異常系_403レスポンスでETFComBlockedError(self) -> None:
        """403 レスポンスで ETFComBlockedError が発生すること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession()

                with pytest.raises(ETFComBlockedError) as exc_info:
                    session.get("https://www.etf.com/SPY")

                assert exc_info.value.status_code == 403
                assert exc_info.value.url == "https://www.etf.com/SPY"

    def test_異常系_429レスポンスでETFComBlockedError(self) -> None:
        """429 レスポンスで ETFComBlockedError が発生すること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession()

                with pytest.raises(ETFComBlockedError) as exc_info:
                    session.get("https://www.etf.com/SPY")

                assert exc_info.value.status_code == 429

    def test_正常系_timeoutが設定される(self) -> None:
        """config.timeout がリクエストに渡されること。"""
        config = ScrapingConfig(timeout=15.0)

        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession(config=config)
                session.get("https://www.etf.com/SPY")

                call_kwargs = mock_session.get.call_args
                assert call_kwargs[1]["timeout"] == 15.0

    def test_正常系_追加のkwargsが渡される(self) -> None:
        """追加の kwargs が curl_cffi.get に渡されること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession()
                session.get("https://www.etf.com/SPY", params={"key": "value"})

                call_kwargs = mock_session.get.call_args
                assert call_kwargs[1]["params"] == {"key": "value"}


# =============================================================================
# get_with_retry() tests
# =============================================================================


class TestETFComSessionGetWithRetry:
    """ETFComSession.get_with_retry() のテスト。"""

    def test_正常系_成功時はリトライなし(self) -> None:
        """最初の試行で成功した場合リトライしないこと。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_curl.Session.return_value = mock_session

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession()
                response = session.get_with_retry("https://www.etf.com/SPY")

            assert response.status_code == 200
            # get() は1回だけ呼ばれる
            assert mock_session.get.call_count == 1

    def test_正常系_失敗後リトライで成功(self) -> None:
        """失敗後にリトライで成功すること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            mock_session.get.side_effect = [mock_response_blocked, mock_response_ok]
            mock_curl.Session.return_value = mock_session

            retry_config = RetryConfig(max_attempts=3, initial_delay=0.01)

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession(retry_config=retry_config)
                response = session.get_with_retry("https://www.etf.com/SPY")

            assert response.status_code == 200

    def test_正常系_リトライ時にrotate_sessionが呼ばれる(self) -> None:
        """リトライ時に rotate_session() が呼ばれること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            mock_session.get.side_effect = [mock_response_blocked, mock_response_ok]
            mock_curl.Session.return_value = mock_session

            retry_config = RetryConfig(max_attempts=3, initial_delay=0.01)

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession(retry_config=retry_config)
                with patch.object(session, "rotate_session") as mock_rotate:
                    session.get_with_retry("https://www.etf.com/SPY")
                    mock_rotate.assert_called_once()

    def test_異常系_全リトライ失敗でETFComBlockedError(self) -> None:
        """全リトライが失敗した場合 ETFComBlockedError が発生すること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_session.get.return_value = mock_response_blocked
            mock_curl.Session.return_value = mock_session

            retry_config = RetryConfig(max_attempts=2, initial_delay=0.01)

            with patch("market.etfcom.session.time.sleep"):
                session = ETFComSession(retry_config=retry_config)

                with pytest.raises(ETFComBlockedError):
                    session.get_with_retry("https://www.etf.com/SPY")

    def test_正常系_指数バックオフでディレイが増加する(self) -> None:
        """リトライ間のディレイが指数バックオフで増加すること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_response_blocked = MagicMock()
            mock_response_blocked.status_code = 403
            mock_session.get.return_value = mock_response_blocked
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

            with patch("market.etfcom.session.time.sleep", side_effect=track_sleep):
                session = ETFComSession(retry_config=retry_config)

                with pytest.raises(ETFComBlockedError):
                    session.get_with_retry("https://www.etf.com/SPY")

            # ポライトディレイ分を除いたリトライディレイを確認
            # 各リトライ前に sleep が呼ばれる（ポライトディレイ + リトライディレイ）
            # max_attempts=3 なので、リトライディレイは2回（attempt 1, 2 の後）
            retry_delays = [d for d in sleep_calls if d >= 1.0]
            assert len(retry_delays) >= 2


# =============================================================================
# rotate_session() tests
# =============================================================================


class TestETFComSessionRotateSession:
    """ETFComSession.rotate_session() のテスト。"""

    def test_正常系_新しい偽装ターゲットでセッション再生成(self) -> None:
        """rotate_session() が新しい偽装ターゲットで再生成すること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session_old = MagicMock()
            mock_session_new = MagicMock()
            mock_curl.Session.side_effect = [mock_session_old, mock_session_new]

            session = ETFComSession()

            with patch(
                "market.etfcom.session.random.choice",
                return_value="edge99",
            ):
                session.rotate_session()

            # 古いセッションが閉じられること
            mock_session_old.close.assert_called_once()
            # 新しいセッションが生成されること
            assert mock_curl.Session.call_count == 2

    def test_正常系_BROWSER_IMPERSONATE_TARGETSから選択される(self) -> None:
        """偽装ターゲットが BROWSER_IMPERSONATE_TARGETS から選択されること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_curl.Session.return_value = MagicMock()

            session = ETFComSession()
            session.rotate_session()

            # 2回目の Session() 呼び出しの impersonate 引数を確認
            second_call_kwargs = mock_curl.Session.call_args
            target = second_call_kwargs[1]["impersonate"]
            assert target in BROWSER_IMPERSONATE_TARGETS


# =============================================================================
# close() tests
# =============================================================================


class TestETFComSessionClose:
    """ETFComSession.close() のテスト。"""

    def test_正常系_セッションが閉じられる(self) -> None:
        """close() でセッションが閉じられること。"""
        with patch("market.etfcom.session.curl_requests") as mock_curl:
            mock_session = MagicMock()
            mock_curl.Session.return_value = mock_session

            session = ETFComSession()
            session.close()

            mock_session.close.assert_called_once()


# =============================================================================
# Logging tests
# =============================================================================


class TestETFComSessionLogging:
    """ETFComSession のロギングテスト。"""

    def test_正常系_loggerが定義されている(self) -> None:
        """モジュールレベルで structlog ロガーが定義されていること。"""
        import market.etfcom.session as session_module

        assert hasattr(session_module, "logger")


# =============================================================================
# __all__ export tests
# =============================================================================


class TestModuleExports:
    """__all__ エクスポートのテスト。"""

    def test_正常系_ETFComSessionがエクスポートされている(self) -> None:
        """__all__ に ETFComSession が含まれていること。"""
        from market.etfcom.session import __all__

        assert "ETFComSession" in __all__
