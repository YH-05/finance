"""Unit tests for notebooklm.errors module."""

import pytest

from notebooklm.errors import (
    AuthenticationError,
    BrowserTimeoutError,
    ChatError,
    ElementNotFoundError,
    NavigationError,
    NotebookLMError,
    SessionExpiredError,
    SourceAddError,
    StudioGenerationError,
)


class TestNotebookLMError:
    """Tests for NotebookLMError base exception."""

    def test_正常系_メッセージのみで作成できる(self) -> None:
        error = NotebookLMError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.context == {}

    def test_正常系_コンテキスト付きで作成できる(self) -> None:
        context = {"notebook_id": "abc-123", "step": "create"}
        error = NotebookLMError("Failed", context=context)
        assert error.message == "Failed"
        assert error.context == context
        assert error.context["notebook_id"] == "abc-123"

    def test_正常系_Exceptionを継承している(self) -> None:
        error = NotebookLMError("test")
        assert isinstance(error, Exception)

    def test_正常系_コンテキストNoneで空dictになる(self) -> None:
        error = NotebookLMError("test", context=None)
        assert error.context == {}

    def test_正常系_raiseしてcatchできる(self) -> None:
        with pytest.raises(NotebookLMError, match="test error"):
            raise NotebookLMError("test error")


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = AuthenticationError("Login failed")
        assert isinstance(error, NotebookLMError)
        assert isinstance(error, Exception)

    def test_正常系_コンテキスト付きで作成できる(self) -> None:
        error = AuthenticationError(
            "Google login failed",
            context={"login_url": "https://accounts.google.com", "attempt": 2},
        )
        assert error.message == "Google login failed"
        assert error.context["attempt"] == 2

    def test_正常系_NotebookLMErrorでcatchできる(self) -> None:
        with pytest.raises(NotebookLMError):
            raise AuthenticationError("Login failed")


class TestNavigationError:
    """Tests for NavigationError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = NavigationError("Page not found")
        assert isinstance(error, NotebookLMError)

    def test_正常系_コンテキスト付きで作成できる(self) -> None:
        error = NavigationError(
            "Failed to navigate",
            context={"target_url": "https://notebooklm.google.com/notebook/abc"},
        )
        assert (
            error.context["target_url"] == "https://notebooklm.google.com/notebook/abc"
        )


class TestElementNotFoundError:
    """Tests for ElementNotFoundError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = ElementNotFoundError("Button not found")
        assert isinstance(error, NotebookLMError)

    def test_正常系_セレクター情報をコンテキストに含められる(self) -> None:
        error = ElementNotFoundError(
            "Create button not found",
            context={
                "selector": 'button[ref="e78"]',
                "fallback_selectors": ['button[ref="e135"]'],
            },
        )
        assert error.context["selector"] == 'button[ref="e78"]'
        assert len(error.context["fallback_selectors"]) == 1


class TestBrowserTimeoutError:
    """Tests for BrowserTimeoutError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = BrowserTimeoutError("Timeout")
        assert isinstance(error, NotebookLMError)

    def test_正常系_タイムアウト情報をコンテキストに含められる(self) -> None:
        error = BrowserTimeoutError(
            "Operation timed out",
            context={"operation": "audio_generation", "timeout_ms": 600000},
        )
        assert error.context["timeout_ms"] == 600000


class TestSessionExpiredError:
    """Tests for SessionExpiredError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = SessionExpiredError("Session expired")
        assert isinstance(error, NotebookLMError)

    def test_正常系_セッション情報をコンテキストに含められる(self) -> None:
        error = SessionExpiredError(
            "Session expired",
            context={
                "session_file": ".notebooklm-session.json",
                "last_used": "2026-02-15T10:00:00Z",
            },
        )
        assert error.context["session_file"] == ".notebooklm-session.json"


class TestSourceAddError:
    """Tests for SourceAddError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = SourceAddError("Failed to add source")
        assert isinstance(error, NotebookLMError)

    def test_正常系_ソース情報をコンテキストに含められる(self) -> None:
        error = SourceAddError(
            "URL source failed",
            context={
                "source_type": "url",
                "notebook_id": "abc-123",
                "source_url": "https://example.com",
            },
        )
        assert error.context["source_type"] == "url"


class TestChatError:
    """Tests for ChatError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = ChatError("Chat failed")
        assert isinstance(error, NotebookLMError)

    def test_正常系_チャット情報をコンテキストに含められる(self) -> None:
        error = ChatError(
            "No response",
            context={
                "notebook_id": "abc-123",
                "question": "What is this about?",
                "timeout_ms": 30000,
            },
        )
        assert error.context["question"] == "What is this about?"


class TestStudioGenerationError:
    """Tests for StudioGenerationError."""

    def test_正常系_NotebookLMErrorを継承している(self) -> None:
        error = StudioGenerationError("Generation failed")
        assert isinstance(error, NotebookLMError)

    def test_正常系_生成情報をコンテキストに含められる(self) -> None:
        error = StudioGenerationError(
            "Slide generation timed out",
            context={
                "content_type": "slides",
                "notebook_id": "abc-123",
                "timeout_seconds": 600,
            },
        )
        assert error.context["content_type"] == "slides"


class TestExceptionHierarchy:
    """Tests for the complete exception hierarchy."""

    def test_正常系_全例外がNotebookLMErrorを継承している(self) -> None:
        exceptions = [
            AuthenticationError("test"),
            NavigationError("test"),
            ElementNotFoundError("test"),
            BrowserTimeoutError("test"),
            SessionExpiredError("test"),
            SourceAddError("test"),
            ChatError("test"),
            StudioGenerationError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, NotebookLMError), (
                f"{type(exc).__name__} should inherit NotebookLMError"
            )
            assert isinstance(exc, Exception), (
                f"{type(exc).__name__} should inherit Exception"
            )

    def test_正常系_基底クラスでcatchすると全子クラスをcatchできる(self) -> None:
        exception_classes = [
            AuthenticationError,
            NavigationError,
            ElementNotFoundError,
            BrowserTimeoutError,
            SessionExpiredError,
            SourceAddError,
            ChatError,
            StudioGenerationError,
        ]
        for cls in exception_classes:
            with pytest.raises(NotebookLMError):
                raise cls(f"Test {cls.__name__}")

    def test_正常系_子クラスは個別にcatchできる(self) -> None:
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Login failed")

        with pytest.raises(BrowserTimeoutError):
            raise BrowserTimeoutError("Timeout")
