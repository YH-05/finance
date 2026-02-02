"""Unit tests for market.yfinance.session module.

Tests for HttpSessionProtocol and CurlCffiSession implementations.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestHttpSessionProtocol:
    """Tests for HttpSessionProtocol interface."""

    def test_正常系_プロトコルがget_closeメソッドを定義(self) -> None:
        """HttpSessionProtocol が get と close メソッドを定義していることを確認。"""
        from market.yfinance.session import HttpSessionProtocol

        # Protocol methods should be defined
        assert hasattr(HttpSessionProtocol, "get")
        assert hasattr(HttpSessionProtocol, "close")


class TestCurlCffiSession:
    """Tests for CurlCffiSession class."""

    def test_正常系_クラスが存在する(self) -> None:
        """CurlCffiSession クラスが存在することを確認。"""
        from market.yfinance.session import CurlCffiSession

        assert CurlCffiSession is not None

    def test_正常系_HttpSessionProtocolを実装(self) -> None:
        """CurlCffiSession が HttpSessionProtocol を実装していることを確認。"""
        from market.yfinance.session import CurlCffiSession, HttpSessionProtocol

        # Should have get and close methods
        assert hasattr(CurlCffiSession, "get")
        assert hasattr(CurlCffiSession, "close")

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_デフォルトimpersonate設定(
        self, mock_session_cls: MagicMock
    ) -> None:
        """デフォルトの impersonate が設定されることを確認。"""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = CurlCffiSession()

        # curl_requests.Session should be called with impersonate
        mock_session_cls.assert_called_once()
        call_kwargs = mock_session_cls.call_args.kwargs
        assert "impersonate" in call_kwargs
        assert call_kwargs["impersonate"] == "chrome"

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_カスタムimpersonate設定(self, mock_session_cls: MagicMock) -> None:
        """カスタムの impersonate が設定されることを確認。"""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = CurlCffiSession(impersonate="safari15_3")

        mock_session_cls.assert_called_once_with(impersonate="safari15_3")

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_getメソッドがリクエストを転送(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドが内部セッションにリクエストを転送することを確認。"""
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
    def test_正常系_closeメソッドがセッションをクローズ(
        self, mock_session_cls: MagicMock
    ) -> None:
        """close メソッドが内部セッションをクローズすることを確認。"""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = CurlCffiSession()
        session.close()

        mock_session.close.assert_called_once()

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_コンテキストマネージャーサポート(
        self, mock_session_cls: MagicMock
    ) -> None:
        """コンテキストマネージャーとして使用できることを確認。"""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        with CurlCffiSession() as session:
            assert session is not None

        # close should be called on context exit
        mock_session.close.assert_called_once()

    @patch("market.yfinance.session.curl_requests.Session")
    def test_正常系_getメソッドがkwargsを正しく渡す(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドがすべての kwargs を正しく転送することを確認。"""
        from market.yfinance.session import CurlCffiSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = CurlCffiSession()
        session.get(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
        )

        mock_session.get.assert_called_once_with(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
        )


class TestStandardRequestsSession:
    """Tests for StandardRequestsSession class."""

    def test_正常系_クラスが存在する(self) -> None:
        """StandardRequestsSession クラスが存在することを確認。"""
        from market.yfinance.session import StandardRequestsSession

        assert StandardRequestsSession is not None

    def test_正常系_HttpSessionProtocolを実装(self) -> None:
        """StandardRequestsSession が HttpSessionProtocol を実装していることを確認。"""
        from market.yfinance.session import HttpSessionProtocol, StandardRequestsSession

        # Should have get and close methods
        assert hasattr(StandardRequestsSession, "get")
        assert hasattr(StandardRequestsSession, "close")

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_セッションが初期化される(self, mock_session_cls: MagicMock) -> None:
        """requests.Session が初期化されることを確認。"""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        _session = StandardRequestsSession()

        mock_session_cls.assert_called_once()

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_getメソッドがリクエストを転送(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドが内部セッションにリクエストを転送することを確認。"""
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
    def test_正常系_closeメソッドがセッションをクローズ(
        self, mock_session_cls: MagicMock
    ) -> None:
        """close メソッドが内部セッションをクローズすることを確認。"""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = StandardRequestsSession()
        session.close()

        mock_session.close.assert_called_once()

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_コンテキストマネージャーサポート(
        self, mock_session_cls: MagicMock
    ) -> None:
        """コンテキストマネージャーとして使用できることを確認。"""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        with StandardRequestsSession() as session:
            assert session is not None

        # close should be called on context exit
        mock_session.close.assert_called_once()

    @patch("market.yfinance.session.requests.Session")
    def test_正常系_getメソッドがkwargsを正しく渡す(
        self, mock_session_cls: MagicMock
    ) -> None:
        """get メソッドがすべての kwargs を正しく転送することを確認。"""
        from market.yfinance.session import StandardRequestsSession

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = StandardRequestsSession()
        session.get(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
        )

        mock_session.get.assert_called_once_with(
            "https://example.com",
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            timeout=30.0,
        )


class TestSessionExports:
    """Tests for module exports."""

    def test_正常系_CurlCffiSessionがエクスポートされている(self) -> None:
        """CurlCffiSession が __all__ に含まれていることを確認。"""
        from market.yfinance import session

        assert "CurlCffiSession" in session.__all__

    def test_正常系_StandardRequestsSessionがエクスポートされている(self) -> None:
        """StandardRequestsSession が __all__ に含まれていることを確認。"""
        from market.yfinance import session

        assert "StandardRequestsSession" in session.__all__
