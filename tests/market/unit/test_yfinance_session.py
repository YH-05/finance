"""Unit tests for market.yfinance.session module.

This module provides comprehensive tests for the HTTP session abstractions
used by the yfinance module, including:
- HttpSessionProtocol interface
- CurlCffiSession implementation
- StandardRequestsSession implementation
- Mock HTTP session for testing
- YFinanceFetcher session injection

Test TODO List:
- [x] HttpSessionProtocol: protocol has get, close, raw_session
- [x] CurlCffiSession: implements HttpSessionProtocol
- [x] CurlCffiSession: browser impersonation
- [x] CurlCffiSession: context manager support
- [x] CurlCffiSession: get method forwards requests
- [x] CurlCffiSession: close method releases resources
- [x] CurlCffiSession: raw_session returns underlying session
- [x] StandardRequestsSession: implements HttpSessionProtocol
- [x] StandardRequestsSession: context manager support
- [x] StandardRequestsSession: get method forwards requests
- [x] StandardRequestsSession: close method releases resources
- [x] StandardRequestsSession: raw_session returns underlying session
- [x] MockHttpSession: implements HttpSessionProtocol
- [x] MockHttpSession: configurable responses
- [x] YFinanceFetcher: accepts http_session parameter
- [x] YFinanceFetcher: uses injected session
- [x] YFinanceFetcher: defaults to CurlCffiSession
- [x] YFinanceFetcher: closes session on context exit
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Mock HTTP Session for Testing
# =============================================================================


class MockHttpSession:
    """Mock HTTP session for testing purposes.

    This class implements the HttpSessionProtocol interface and allows
    configuring responses for testing without making actual HTTP requests.

    Parameters
    ----------
    responses : dict[str, Any] | None
        Dictionary mapping URLs to response objects.
        If a URL is not found, returns a default empty response.
    default_response : Any | None
        Default response object for unmapped URLs.
        Defaults to a MagicMock.

    Examples
    --------
    >>> mock_session = MockHttpSession(
    ...     responses={"https://api.example.com/data": {"status": "ok"}}
    ... )
    >>> response = mock_session.get("https://api.example.com/data")
    >>> response
    {'status': 'ok'}
    """

    def __init__(
        self,
        responses: dict[str, Any] | None = None,
        default_response: Any | None = None,
    ) -> None:
        """Initialize the mock session.

        Parameters
        ----------
        responses : dict[str, Any] | None
            Mapping of URLs to responses.
        default_response : Any | None
            Default response for unmapped URLs.
        """
        self._responses = responses or {}
        self._default_response = (
            default_response if default_response is not None else MagicMock()
        )
        self._get_calls: list[tuple[str, dict[str, Any]]] = []
        self._closed = False
        self._internal_session = MagicMock()

    @property
    def raw_session(self) -> Any:
        """Return the internal mock session.

        Returns
        -------
        Any
            The internal mock session object.
        """
        return self._internal_session

    def get(self, url: str, **kwargs: Any) -> Any:
        """Mock GET request.

        Parameters
        ----------
        url : str
            The URL to request.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        Any
            The configured response or default response.
        """
        self._get_calls.append((url, kwargs))
        return self._responses.get(url, self._default_response)

    def close(self) -> None:
        """Mark the session as closed."""
        self._closed = True

    @property
    def is_closed(self) -> bool:
        """Check if the session has been closed.

        Returns
        -------
        bool
            True if close() has been called.
        """
        return self._closed

    @property
    def call_history(self) -> list[tuple[str, dict[str, Any]]]:
        """Get the history of get() calls.

        Returns
        -------
        list[tuple[str, dict[str, Any]]]
            List of (url, kwargs) tuples for each get() call.
        """
        return self._get_calls

    def __enter__(self) -> "MockHttpSession":
        """Support context manager protocol."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Close on context exit."""
        self.close()


# =============================================================================
# Tests for HttpSessionProtocol
# =============================================================================


class TestHttpSessionProtocol:
    """Tests for HttpSessionProtocol interface."""

    def test_正常系_プロトコルが必要なメソッドを定義している(self) -> None:
        """HttpSessionProtocol が get, close, raw_session を定義していることを確認."""
        from market.yfinance.session import HttpSessionProtocol

        assert hasattr(HttpSessionProtocol, "get")
        assert hasattr(HttpSessionProtocol, "close")
        assert hasattr(HttpSessionProtocol, "raw_session")

    def test_正常系_getメソッドのシグネチャが正しい(self) -> None:
        """get メソッドが url と **kwargs を受け取ることを確認."""
        import inspect

        from market.yfinance.session import HttpSessionProtocol

        sig = inspect.signature(HttpSessionProtocol.get)
        params = list(sig.parameters.keys())

        assert "url" in params
        # **kwargs の存在確認（VAR_KEYWORD）
        has_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        assert has_kwargs, "get method should accept **kwargs"

    def test_正常系_closeメソッドが引数なしで呼び出せる(self) -> None:
        """close メソッドが引数なしで呼び出せることを確認."""
        import inspect

        from market.yfinance.session import HttpSessionProtocol

        sig = inspect.signature(HttpSessionProtocol.close)
        params = [p for p in sig.parameters.values() if p.name != "self"]

        assert len(params) == 0

    def test_正常系_具象クラスがプロトコルを満たす(self) -> None:
        """必要なメソッドを持つクラスがプロトコルを満たすことを確認."""
        from market.yfinance.session import HttpSessionProtocol  # noqa: TC001

        class ConcreteSession:
            """A concrete implementation satisfying HttpSessionProtocol."""

            def __init__(self) -> None:
                self._internal = object()

            @property
            def raw_session(self) -> Any:
                return self._internal

            def get(self, url: str, **kwargs: Any) -> Any:
                return {"status": 200}

            def close(self) -> None:
                pass

        # 型ヒントとして使用可能
        session: HttpSessionProtocol = ConcreteSession()
        result = session.get("https://example.com")
        assert result == {"status": 200}
        session.close()


# =============================================================================
# Tests for CurlCffiSession
# =============================================================================


class TestCurlCffiSession:
    """Tests for CurlCffiSession class."""

    def test_正常系_クラスが存在しインポートできる(self) -> None:
        """CurlCffiSession クラスがインポートできることを確認."""
        from market.yfinance.session import CurlCffiSession

        assert CurlCffiSession is not None

    def test_正常系_HttpSessionProtocolのメソッドを持つ(self) -> None:
        """CurlCffiSession が必要なメソッドを持つことを確認."""
        from market.yfinance.session import CurlCffiSession

        assert hasattr(CurlCffiSession, "get")
        assert hasattr(CurlCffiSession, "close")
        assert hasattr(CurlCffiSession, "raw_session")

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_デフォルトでchromeをimpersonate(
        self, mock_session_cls: MagicMock
    ) -> None:
        """デフォルトで chrome ブラウザをimpersonateすることを確認."""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        _session = CurlCffiSession()

        mock_session_cls.assert_called_once()
        call_kwargs = mock_session_cls.call_args.kwargs
        assert call_kwargs.get("impersonate") == "chrome"

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_カスタムimpersonate設定が反映される(
        self, mock_session_cls: MagicMock
    ) -> None:
        """カスタムの impersonate 設定が反映されることを確認."""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        _session = CurlCffiSession(impersonate="safari15_3")

        mock_session_cls.assert_called_once_with(impersonate="safari15_3")

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_getメソッドが内部セッションにリクエストを転送(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドが内部セッションにリクエストを転送することを確認."""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        session = CurlCffiSession()
        response = session.get("https://example.com", headers={"User-Agent": "Test"})

        mock_session.get.assert_called_once_with(
            "https://example.com", headers={"User-Agent": "Test"}
        )
        assert response == mock_response

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_getメソッドがすべてのkwargsを正しく渡す(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドがすべての kwargs を正しく転送することを確認."""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = CurlCffiSession()
        session.get(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
            verify=True,
        )

        mock_session.get.assert_called_once_with(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
            verify=True,
        )

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_closeメソッドが内部セッションをクローズ(
        self, mock_session_cls: MagicMock
    ) -> None:
        """close メソッドが内部セッションをクローズすることを確認."""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = CurlCffiSession()
        session.close()

        mock_session.close.assert_called_once()

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_コンテキストマネージャーで自動クローズ(
        self, mock_session_cls: MagicMock
    ) -> None:
        """コンテキストマネージャー終了時に自動でクローズされることを確認."""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        with CurlCffiSession() as session:
            assert session is not None

        mock_session.close.assert_called_once()

    def test_正常系_raw_sessionがcurl_cffiセッションを返す(self) -> None:
        """raw_session が curl_cffi.requests.Session を返すことを確認."""
        from curl_cffi import requests as curl_requests

        from market.yfinance.session import CurlCffiSession

        session = CurlCffiSession()
        try:
            raw = session.raw_session
            assert isinstance(raw, curl_requests.Session)
        finally:
            session.close()

    def test_正常系_raw_sessionが内部セッションと同一(self) -> None:
        """raw_session が内部の _session と同じオブジェクトを返すことを確認."""
        from market.yfinance.session import CurlCffiSession

        session = CurlCffiSession()
        try:
            assert session.raw_session is session._session
        finally:
            session.close()


# =============================================================================
# Tests for StandardRequestsSession
# =============================================================================


class TestStandardRequestsSession:
    """Tests for StandardRequestsSession class."""

    def test_正常系_クラスが存在しインポートできる(self) -> None:
        """StandardRequestsSession クラスがインポートできることを確認."""
        from market.yfinance.session import StandardRequestsSession

        assert StandardRequestsSession is not None

    def test_正常系_HttpSessionProtocolのメソッドを持つ(self) -> None:
        """StandardRequestsSession が必要なメソッドを持つことを確認."""
        from market.yfinance.session import StandardRequestsSession

        assert hasattr(StandardRequestsSession, "get")
        assert hasattr(StandardRequestsSession, "close")
        assert hasattr(StandardRequestsSession, "raw_session")

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_初期化時にrequestsセッションが作成される(
        self, mock_session_cls: MagicMock
    ) -> None:
        """初期化時に requests.Session が作成されることを確認."""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        _session = StandardRequestsSession()

        mock_session_cls.assert_called_once()

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_getメソッドが内部セッションにリクエストを転送(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドが内部セッションにリクエストを転送することを確認."""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        session = StandardRequestsSession()
        response = session.get("https://example.com", headers={"User-Agent": "Test"})

        mock_session.get.assert_called_once_with(
            "https://example.com", headers={"User-Agent": "Test"}
        )
        assert response == mock_response

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_getメソッドがすべてのkwargsを正しく渡す(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドがすべての kwargs を正しく転送することを確認."""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = StandardRequestsSession()
        session.get(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
            verify=True,
        )

        mock_session.get.assert_called_once_with(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
            verify=True,
        )

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_closeメソッドが内部セッションをクローズ(
        self, mock_session_cls: MagicMock
    ) -> None:
        """close メソッドが内部セッションをクローズすることを確認."""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = StandardRequestsSession()
        session.close()

        mock_session.close.assert_called_once()

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_コンテキストマネージャーで自動クローズ(
        self, mock_session_cls: MagicMock
    ) -> None:
        """コンテキストマネージャー終了時に自動でクローズされることを確認."""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        with StandardRequestsSession() as session:
            assert session is not None

        mock_session.close.assert_called_once()

    def test_正常系_raw_sessionがrequestsセッションを返す(self) -> None:
        """raw_session が requests.Session を返すことを確認."""
        import requests

        from market.yfinance.session import StandardRequestsSession

        session = StandardRequestsSession()
        try:
            raw = session.raw_session
            assert isinstance(raw, requests.Session)
        finally:
            session.close()

    def test_正常系_raw_sessionが内部セッションと同一(self) -> None:
        """raw_session が内部の _session と同じオブジェクトを返すことを確認."""
        from market.yfinance.session import StandardRequestsSession

        session = StandardRequestsSession()
        try:
            assert session.raw_session is session._session
        finally:
            session.close()


# =============================================================================
# Tests for MockHttpSession
# =============================================================================


class TestMockHttpSession:
    """Tests for MockHttpSession test helper class."""

    def test_正常系_HttpSessionProtocolのメソッドを持つ(self) -> None:
        """MockHttpSession が HttpSessionProtocol のメソッドを持つことを確認."""
        mock_session = MockHttpSession()

        assert hasattr(mock_session, "get")
        assert hasattr(mock_session, "close")
        assert hasattr(mock_session, "raw_session")

    def test_正常系_設定されたレスポンスを返す(self) -> None:
        """設定されたURLに対して設定されたレスポンスを返すことを確認."""
        responses = {
            "https://api.example.com/data": {"status": "ok", "data": [1, 2, 3]},
            "https://api.example.com/users": {"users": ["alice", "bob"]},
        }
        mock_session = MockHttpSession(responses=responses)

        response1 = mock_session.get("https://api.example.com/data")
        response2 = mock_session.get("https://api.example.com/users")

        assert response1 == {"status": "ok", "data": [1, 2, 3]}
        assert response2 == {"users": ["alice", "bob"]}

    def test_正常系_未設定URLでデフォルトレスポンスを返す(self) -> None:
        """未設定のURLに対してデフォルトレスポンスを返すことを確認."""
        default = {"error": "not found"}
        mock_session = MockHttpSession(default_response=default)

        response = mock_session.get("https://unknown.example.com")

        assert response == {"error": "not found"}

    def test_正常系_呼び出し履歴が記録される(self) -> None:
        """get() の呼び出し履歴が記録されることを確認."""
        mock_session = MockHttpSession()

        mock_session.get("https://example.com/a", headers={"X-Custom": "1"})
        mock_session.get("https://example.com/b", timeout=30)

        history = mock_session.call_history
        assert len(history) == 2
        assert history[0] == ("https://example.com/a", {"headers": {"X-Custom": "1"}})
        assert history[1] == ("https://example.com/b", {"timeout": 30})

    def test_正常系_closeでis_closedがTrueになる(self) -> None:
        """close() 呼び出し後に is_closed が True になることを確認."""
        mock_session = MockHttpSession()

        assert mock_session.is_closed is False
        mock_session.close()
        assert mock_session.is_closed is True

    def test_正常系_コンテキストマネージャーで自動クローズ(self) -> None:
        """コンテキストマネージャー終了時に自動でクローズされることを確認."""
        with MockHttpSession() as mock_session:
            assert mock_session.is_closed is False

        assert mock_session.is_closed is True

    def test_正常系_raw_sessionがモックオブジェクトを返す(self) -> None:
        """raw_session がモックオブジェクトを返すことを確認."""
        mock_session = MockHttpSession()
        raw = mock_session.raw_session

        assert raw is not None
        assert raw is mock_session._internal_session


# =============================================================================
# Tests for YFinanceFetcher Session Injection
# =============================================================================


class TestYFinanceFetcherSessionInjection:
    """Tests for YFinanceFetcher http_session dependency injection."""

    def test_正常系_http_sessionパラメータが存在する(self) -> None:
        """コンストラクタに http_session パラメータが存在することを確認."""
        import inspect

        from market.yfinance import YFinanceFetcher

        sig = inspect.signature(YFinanceFetcher.__init__)
        params = list(sig.parameters.keys())
        assert "http_session" in params

    def test_正常系_http_session未指定でCurlCffiSessionがデフォルト(self) -> None:
        """http_session 未指定時に CurlCffiSession がデフォルトで使用されることを確認."""
        from market.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        session = fetcher._get_session()

        assert session is not None
        assert hasattr(session, "get")
        assert hasattr(session, "close")
        assert hasattr(session, "raw_session")

    def test_正常系_カスタムセッションを注入できる(self) -> None:
        """http_session パラメータでカスタムセッションを注入できることを確認."""
        from market.yfinance import YFinanceFetcher

        mock_session = MockHttpSession()
        fetcher = YFinanceFetcher(http_session=mock_session)
        session = fetcher._get_session()

        assert session is mock_session

    def test_正常系_注入されたセッションのgetメソッドが使用可能(self) -> None:
        """注入されたセッションの get メソッドが使用可能なことを確認."""
        from market.yfinance import YFinanceFetcher

        responses = {"https://test.example.com": {"data": "test"}}
        mock_session = MockHttpSession(responses=responses)

        fetcher = YFinanceFetcher(http_session=mock_session)
        session = fetcher._get_session()

        response = session.get("https://test.example.com")
        assert response == {"data": "test"}

    @patch("market.yfinance.fetcher.yf.download")
    def test_正常系_fetchで注入されたセッションのraw_sessionが使用される(
        self,
        mock_download: MagicMock,
    ) -> None:
        """fetch メソッドで注入されたセッションの raw_session が使用されることを確認."""
        import pandas as pd

        from market.yfinance import FetchOptions, YFinanceFetcher

        # Create sample data
        sample_data = pd.DataFrame(
            {
                ("Close", "AAPL"): [154.0],
                ("High", "AAPL"): [155.0],
                ("Low", "AAPL"): [149.0],
                ("Open", "AAPL"): [150.0],
                ("Volume", "AAPL"): [1000000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        sample_data.columns = pd.MultiIndex.from_tuples(sample_data.columns)
        mock_download.return_value = sample_data

        mock_session = MockHttpSession()
        fetcher = YFinanceFetcher(http_session=mock_session)
        options = FetchOptions(symbols=["AAPL"])

        fetcher.fetch(options)

        # Verify download was called with the raw_session
        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs["session"] is mock_session.raw_session

    def test_正常系_closeで注入されたセッションがクローズされる(self) -> None:
        """close メソッドで注入されたセッションがクローズされることを確認."""
        from market.yfinance import YFinanceFetcher

        mock_session = MockHttpSession()
        fetcher = YFinanceFetcher(http_session=mock_session)

        assert mock_session.is_closed is False
        fetcher.close()
        assert mock_session.is_closed is True

    def test_正常系_コンテキストマネージャーで注入されたセッションがクローズされる(
        self,
    ) -> None:
        """コンテキストマネージャー終了時に注入されたセッションがクローズされることを確認."""
        from market.yfinance import YFinanceFetcher

        mock_session = MockHttpSession()

        with YFinanceFetcher(http_session=mock_session):
            assert mock_session.is_closed is False

        assert mock_session.is_closed is True

    def test_正常系_StandardRequestsSessionを注入できる(self) -> None:
        """StandardRequestsSession を注入できることを確認."""
        from market.yfinance import YFinanceFetcher
        from market.yfinance.session import StandardRequestsSession

        with patch("market.yfinance.session.requests.Session"):
            session = StandardRequestsSession()
            fetcher = YFinanceFetcher(http_session=session)

            assert fetcher._get_session() is session

    def test_正常系_MagicMockを使用してテストできる(self) -> None:
        """MagicMock を使用してセッションをモックできることを確認."""
        from market.yfinance import YFinanceFetcher

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=MagicMock())
        mock_session.close = MagicMock()
        mock_session.raw_session = MagicMock()

        fetcher = YFinanceFetcher(http_session=mock_session)
        session = fetcher._get_session()

        assert session is mock_session

    def test_正常系_注入されたセッションはローテートされない(self) -> None:
        """注入されたセッションが _rotate_session でローテートされないことを確認."""
        from market.yfinance import YFinanceFetcher

        mock_session = MockHttpSession()
        fetcher = YFinanceFetcher(http_session=mock_session)

        original_session = fetcher._get_session()
        fetcher._rotate_session()
        rotated_session = fetcher._get_session()

        # Should still be the same session (not rotated)
        assert original_session is rotated_session
        assert original_session is mock_session


# =============================================================================
# Tests for Module Exports
# =============================================================================


class TestSessionModuleExports:
    """Tests for session module exports."""

    def test_正常系_CurlCffiSessionがエクスポートされている(self) -> None:
        """CurlCffiSession が __all__ に含まれていることを確認."""
        from market.yfinance import session

        assert "CurlCffiSession" in session.__all__

    def test_正常系_StandardRequestsSessionがエクスポートされている(self) -> None:
        """StandardRequestsSession が __all__ に含まれていることを確認."""
        from market.yfinance import session

        assert "StandardRequestsSession" in session.__all__

    def test_正常系_HttpSessionProtocolがエクスポートされている(self) -> None:
        """HttpSessionProtocol が __all__ に含まれていることを確認."""
        from market.yfinance import session

        assert "HttpSessionProtocol" in session.__all__
