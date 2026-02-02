"""Unit tests for market.yfinance.session module.

TDD Red Phase: These tests are designed to fail initially.
The implementation (market.yfinance.session) does not exist yet.

Test TODO List:
- [x] HttpSessionProtocol: protocol has get method
- [x] HttpSessionProtocol: protocol has close method
- [x] HttpSessionProtocol: concrete implementation satisfies protocol
- [x] HttpSessionProtocol: class without get method does not satisfy protocol
- [x] HttpSessionProtocol: class without close method does not satisfy protocol
"""

from typing import Any

import pytest


class TestHttpSessionProtocol:
    """Tests for HttpSessionProtocol.

    HttpSessionProtocol is a typing.Protocol that defines the interface
    for HTTP session objects used by the yfinance module.

    Required methods:
    - get(url: str, **kwargs) -> Any
    - close() -> None

    Required properties:
    - raw_session -> Any
    """

    def test_正常系_プロトコルが定義されている(self) -> None:
        """HttpSessionProtocol が定義されていることを確認。"""
        from market.yfinance.session import HttpSessionProtocol

        assert hasattr(HttpSessionProtocol, "get")
        assert hasattr(HttpSessionProtocol, "close")
        assert hasattr(HttpSessionProtocol, "raw_session")

    def test_正常系_getメソッドのシグネチャが正しい(self) -> None:
        """get メソッドが url と **kwargs を受け取ることを確認。"""
        import inspect

        from market.yfinance.session import HttpSessionProtocol

        sig = inspect.signature(HttpSessionProtocol.get)
        params = list(sig.parameters.keys())

        # self, url, **kwargs の3つ
        assert "self" in params or params[0] == "self"
        assert "url" in params
        # **kwargs の存在確認（VAR_KEYWORD）
        has_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        assert has_kwargs, "get method should accept **kwargs"

    def test_正常系_closeメソッドのシグネチャが正しい(self) -> None:
        """close メソッドが引数なしで呼び出せることを確認。"""
        import inspect

        from market.yfinance.session import HttpSessionProtocol

        sig = inspect.signature(HttpSessionProtocol.close)
        params = list(sig.parameters.keys())

        # self のみ
        assert len(params) == 1
        assert params[0] == "self"

    def test_正常系_具象クラスがプロトコルを満たす(self) -> None:
        """必要なメソッドを持つクラスがプロトコルを満たすことを確認。"""
        from typing import Protocol, runtime_checkable

        from market.yfinance.session import HttpSessionProtocol  # noqa: TC001

        # プロトコルが runtime_checkable でない場合のテスト
        # isinstance チェックには runtime_checkable が必要
        class ConcreteSession:
            """A concrete implementation that satisfies HttpSessionProtocol."""

            def __init__(self) -> None:
                self._internal_session = object()

            @property
            def raw_session(self) -> Any:
                return self._internal_session

            def get(self, url: str, **kwargs: Any) -> Any:
                return {"status": 200}

            def close(self) -> None:
                pass

        # 型チェッカーはこのクラスが HttpSessionProtocol を満たすとみなす
        session: HttpSessionProtocol = ConcreteSession()

        # メソッドが呼び出せることを確認
        result = session.get("https://example.com")
        assert result == {"status": 200}

        # raw_session が呼び出せることを確認
        raw = session.raw_session
        assert raw is not None

        # close が呼び出せることを確認（例外が出なければ成功）
        session.close()

    def test_正常系_getメソッドがAnyを返す(self) -> None:
        """get メソッドの戻り値がAny型であることを確認。"""
        import inspect
        from typing import Any, get_type_hints

        from market.yfinance.session import HttpSessionProtocol

        hints = get_type_hints(HttpSessionProtocol.get)
        assert hints.get("return") is Any

    def test_正常系_closeメソッドがNoneを返す(self) -> None:
        """close メソッドの戻り値がNone型であることを確認。"""
        import inspect
        from typing import get_type_hints

        from market.yfinance.session import HttpSessionProtocol

        hints = get_type_hints(HttpSessionProtocol.close)
        assert hints.get("return") is type(None)


class TestHttpSessionProtocolCompliance:
    """Tests for protocol compliance checking.

    These tests verify that classes correctly implement or fail to implement
    the HttpSessionProtocol.
    """

    def test_正常系_両メソッドを持つクラスはプロトコルを満たす(self) -> None:
        """get, close, raw_session を持つクラスがプロトコルを満たすことを確認。"""
        from market.yfinance.session import HttpSessionProtocol

        class ValidSession:
            def __init__(self) -> None:
                self._internal = object()

            @property
            def raw_session(self) -> Any:
                return self._internal

            def get(self, url: str, **kwargs: Any) -> Any:
                return None

            def close(self) -> None:
                pass

        # 型ヒントとして使用可能（コンパイル時チェック）
        def use_session(session: HttpSessionProtocol) -> None:
            session.get("https://example.com")
            _ = session.raw_session
            session.close()

        # 呼び出しが成功することを確認
        valid = ValidSession()
        use_session(valid)

    def test_異常系_getメソッドがないクラスはプロトコルを満たさない(self) -> None:
        """get メソッドがないクラスがプロトコルを満たさないことを確認。

        Note: Protocol のチェックは静的型チェッカーで行われるため、
        このテストは構造的に get がないことを確認するのみ。
        """

        class NoGetSession:
            def close(self) -> None:
                pass

        assert not hasattr(NoGetSession, "get")

    def test_異常系_closeメソッドがないクラスはプロトコルを満たさない(self) -> None:
        """close メソッドがないクラスがプロトコルを満たさないことを確認。

        Note: Protocol のチェックは静的型チェッカーで行われるため、
        このテストは構造的に close がないことを確認するのみ。
        """

        class NoCloseSession:
            def get(self, url: str, **kwargs: Any) -> Any:
                return None

        assert not hasattr(NoCloseSession, "close")


class TestHttpSessionProtocolDocstring:
    """Tests for HttpSessionProtocol docstring.

    Verifies that the protocol has proper NumPy-style documentation.
    """

    def test_正常系_プロトコルにDocstringがある(self) -> None:
        """HttpSessionProtocol にDocstringがあることを確認。"""
        from market.yfinance.session import HttpSessionProtocol

        assert HttpSessionProtocol.__doc__ is not None
        assert len(HttpSessionProtocol.__doc__) > 0

    def test_正常系_getメソッドにDocstringがある(self) -> None:
        """get メソッドにDocstringがあることを確認。"""
        from market.yfinance.session import HttpSessionProtocol

        assert HttpSessionProtocol.get.__doc__ is not None
        assert len(HttpSessionProtocol.get.__doc__) > 0

    def test_正常系_closeメソッドにDocstringがある(self) -> None:
        """close メソッドにDocstringがあることを確認。"""
        from market.yfinance.session import HttpSessionProtocol

        assert HttpSessionProtocol.close.__doc__ is not None
        assert len(HttpSessionProtocol.close.__doc__) > 0

    def test_正常系_raw_sessionプロパティにDocstringがある(self) -> None:
        """raw_session プロパティにDocstringがあることを確認。"""
        from market.yfinance.session import HttpSessionProtocol

        assert HttpSessionProtocol.raw_session.__doc__ is not None
        assert len(HttpSessionProtocol.raw_session.__doc__) > 0


class TestCurlCffiSessionRawSession:
    """Tests for CurlCffiSession.raw_session property."""

    def test_正常系_raw_sessionがcurl_cffiセッションを返す(self) -> None:
        """raw_session が curl_cffi.requests.Session を返すことを確認。"""
        from curl_cffi import requests as curl_requests

        from market.yfinance.session import CurlCffiSession

        session = CurlCffiSession()
        try:
            raw = session.raw_session
            assert isinstance(raw, curl_requests.Session)
        finally:
            session.close()

    def test_正常系_raw_sessionが内部セッションと同一(self) -> None:
        """raw_session が内部の _session と同じオブジェクトを返すことを確認。"""
        from market.yfinance.session import CurlCffiSession

        session = CurlCffiSession()
        try:
            assert session.raw_session is session._session
        finally:
            session.close()


class TestStandardRequestsSessionRawSession:
    """Tests for StandardRequestsSession.raw_session property."""

    def test_正常系_raw_sessionがrequestsセッションを返す(self) -> None:
        """raw_session が requests.Session を返すことを確認。"""
        import requests

        from market.yfinance.session import StandardRequestsSession

        session = StandardRequestsSession()
        try:
            raw = session.raw_session
            assert isinstance(raw, requests.Session)
        finally:
            session.close()

    def test_正常系_raw_sessionが内部セッションと同一(self) -> None:
        """raw_session が内部の _session と同じオブジェクトを返すことを確認。"""
        from market.yfinance.session import StandardRequestsSession

        session = StandardRequestsSession()
        try:
            assert session.raw_session is session._session
        finally:
            session.close()
