"""Unit tests for notebooklm.browser.helpers module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_page_mock() -> MagicMock:
    """Create a mock Playwright page with sync locator() method.

    Playwright's ``page.locator()`` is synchronous and returns a Locator,
    while Locator methods like ``wait_for()``, ``count()``, ``click()``
    are async. This helper creates a mock that matches that behavior.

    Returns
    -------
    MagicMock
        A mock page object.
    """
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    return mock_page


def _make_locator_mock(
    *,
    count: int = 1,
    inner_text: str = "",
    wait_for_side_effect: Exception | None = None,
) -> MagicMock:
    """Create a mock Playwright Locator.

    Parameters
    ----------
    count : int
        Value returned by ``locator.count()``.
    inner_text : str
        Value returned by ``locator.inner_text()``.
    wait_for_side_effect : Exception | None
        If set, ``wait_for()`` raises this exception.

    Returns
    -------
    MagicMock
        A mock locator object with async methods.
    """
    mock_locator = MagicMock()
    mock_locator.count = AsyncMock(return_value=count)
    mock_locator.inner_text = AsyncMock(return_value=inner_text)
    mock_locator.click = AsyncMock()

    if wait_for_side_effect:
        mock_locator.wait_for = AsyncMock(side_effect=wait_for_side_effect)
    else:
        mock_locator.wait_for = AsyncMock()

    # first property returns the locator itself (for element access)
    mock_locator.first = mock_locator
    return mock_locator


class TestWaitForElement:
    """Tests for wait_for_element helper."""

    @pytest.mark.asyncio
    async def test_正常系_最初のセレクタで要素が見つかる(self) -> None:
        from notebooklm.browser.helpers import wait_for_element

        mock_page = _make_page_mock()
        mock_locator = _make_locator_mock(count=1)
        mock_page.locator.return_value = mock_locator

        result = await wait_for_element(
            mock_page, ['button[aria-label="test"]'], timeout_ms=5000
        )
        assert result is mock_locator.first

    @pytest.mark.asyncio
    async def test_正常系_フォールバックセレクタで要素が見つかる(self) -> None:
        from notebooklm.browser.helpers import wait_for_element

        mock_page = _make_page_mock()

        mock_locator_fail = _make_locator_mock(
            wait_for_side_effect=TimeoutError("not found"),
        )
        mock_locator_ok = _make_locator_mock(count=1)

        mock_page.locator.side_effect = [mock_locator_fail, mock_locator_ok]

        result = await wait_for_element(
            mock_page,
            ['button[aria-label="miss"]', 'button[aria-label="hit"]'],
            timeout_ms=5000,
        )
        assert result is mock_locator_ok.first

    @pytest.mark.asyncio
    async def test_異常系_全セレクタで見つからないとElementNotFoundError(
        self,
    ) -> None:
        from notebooklm.browser.helpers import wait_for_element
        from notebooklm.errors import ElementNotFoundError

        mock_page = _make_page_mock()
        mock_locator = _make_locator_mock(
            wait_for_side_effect=TimeoutError("not found"),
        )
        mock_page.locator.return_value = mock_locator

        with pytest.raises(ElementNotFoundError, match="No element found"):
            await wait_for_element(
                mock_page, ['button[aria-label="nonexistent"]'], timeout_ms=1000
            )


class TestExtractText:
    """Tests for extract_text helper."""

    @pytest.mark.asyncio
    async def test_正常系_テキストを抽出できる(self) -> None:
        from notebooklm.browser.helpers import extract_text

        mock_page = _make_page_mock()
        mock_locator = _make_locator_mock(count=1, inner_text="  Hello World  ")
        mock_page.locator.return_value = mock_locator

        result = await extract_text(mock_page, "div.content")
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_正常系_要素が見つからない場合Noneを返す(self) -> None:
        from notebooklm.browser.helpers import extract_text

        mock_page = _make_page_mock()
        mock_locator = _make_locator_mock(count=0)
        mock_page.locator.return_value = mock_locator

        result = await extract_text(mock_page, "div.missing")
        assert result is None


class TestPollUntil:
    """Tests for poll_until helper with exponential backoff."""

    @pytest.mark.asyncio
    async def test_正常系_条件が即座に満たされる(self) -> None:
        from notebooklm.browser.helpers import poll_until

        check_fn = AsyncMock(return_value=True)

        result = await poll_until(check_fn, timeout_seconds=10.0, interval_seconds=1.0)
        assert result is True
        check_fn.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_正常系_数回のポーリング後に条件が満たされる(self) -> None:
        from notebooklm.browser.helpers import poll_until

        call_count = 0

        async def check() -> bool:
            nonlocal call_count
            call_count += 1
            return call_count >= 3

        with patch("notebooklm.browser.helpers.asyncio.sleep", new_callable=AsyncMock):
            result = await poll_until(
                check, timeout_seconds=30.0, interval_seconds=0.01
            )

        assert result is True
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_異常系_タイムアウトでBrowserTimeoutError(self) -> None:
        from notebooklm.browser.helpers import poll_until
        from notebooklm.errors import BrowserTimeoutError

        check_fn = AsyncMock(return_value=False)

        with (
            patch("notebooklm.browser.helpers.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(BrowserTimeoutError, match="Polling timed out"),
        ):
            await poll_until(check_fn, timeout_seconds=0.01, interval_seconds=0.001)


class TestWaitForDownload:
    """Tests for wait_for_download helper."""

    @pytest.mark.asyncio
    async def test_正常系_ダウンロード完了を待機できる(self) -> None:
        from notebooklm.browser.helpers import wait_for_download

        mock_page = _make_page_mock()
        mock_download = MagicMock()
        mock_download.path = AsyncMock(return_value="/tmp/test.pdf")
        mock_download.suggested_filename = "test.pdf"

        # expect_download returns an async context manager
        # whose value attribute holds the download object
        mock_download_info = MagicMock()
        mock_download_info.value = mock_download

        mock_download_ctx = AsyncMock()
        mock_download_ctx.__aenter__ = AsyncMock(return_value=mock_download_info)
        mock_download_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_page.expect_download.return_value = mock_download_ctx

        result = await wait_for_download(mock_page)
        assert result.suggested_filename == "test.pdf"


class TestClickWithFallback:
    """Tests for click_with_fallback helper."""

    @pytest.mark.asyncio
    async def test_正常系_最初のセレクタでクリックできる(self) -> None:
        from notebooklm.browser.helpers import click_with_fallback

        mock_page = _make_page_mock()
        mock_locator = _make_locator_mock(count=1)
        mock_page.locator.return_value = mock_locator

        await click_with_fallback(
            mock_page, ['button[aria-label="test"]'], timeout_ms=5000
        )
        mock_locator.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_正常系_フォールバックでクリックできる(self) -> None:
        from notebooklm.browser.helpers import click_with_fallback

        mock_page = _make_page_mock()
        mock_locator_fail = _make_locator_mock(count=0)
        mock_locator_ok = _make_locator_mock(count=1)
        mock_page.locator.side_effect = [mock_locator_fail, mock_locator_ok]

        await click_with_fallback(
            mock_page,
            ['button[aria-label="miss"]', 'button[aria-label="hit"]'],
            timeout_ms=5000,
        )
        mock_locator_ok.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_全セレクタでクリックできないとElementNotFoundError(
        self,
    ) -> None:
        from notebooklm.browser.helpers import click_with_fallback
        from notebooklm.errors import ElementNotFoundError

        mock_page = _make_page_mock()
        mock_locator = _make_locator_mock(count=0)
        mock_page.locator.return_value = mock_locator

        with pytest.raises(ElementNotFoundError):
            await click_with_fallback(
                mock_page, ['button[aria-label="none"]'], timeout_ms=1000
            )


class TestNavigateToNotebook:
    """Tests for navigate_to_notebook helper."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブックに遷移できる(self) -> None:
        from notebooklm.browser.helpers import navigate_to_notebook

        mock_page = _make_page_mock()
        mock_page.url = "https://notebooklm.google.com/notebook/abc-123"

        await navigate_to_notebook(mock_page, "abc-123")
        mock_page.goto.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_ログインページにリダイレクトでSessionExpiredError(
        self,
    ) -> None:
        from notebooklm.browser.helpers import navigate_to_notebook
        from notebooklm.errors import SessionExpiredError

        mock_page = _make_page_mock()
        mock_page.url = "https://accounts.google.com/signin"

        with pytest.raises(SessionExpiredError):
            await navigate_to_notebook(mock_page, "abc-123")


class TestExtractTableData:
    """Tests for extract_table_data helper."""

    @pytest.mark.asyncio
    async def test_正常系_テーブルデータを抽出できる(self) -> None:
        from notebooklm.browser.helpers import extract_table_data

        mock_page = _make_page_mock()

        # Build mock table structure
        # Each row has a locator("td, th") that returns all_inner_texts
        mock_row_1 = MagicMock()
        mock_row_1_cells = MagicMock()
        mock_row_1_cells.all_inner_texts = AsyncMock(
            return_value=["Header1", "Header2"]
        )
        mock_row_1.locator.return_value = mock_row_1_cells

        mock_row_2 = MagicMock()
        mock_row_2_cells = MagicMock()
        mock_row_2_cells.all_inner_texts = AsyncMock(return_value=["Value1", "Value2"])
        mock_row_2.locator.return_value = mock_row_2_cells

        # Table locator returns rows
        mock_table = MagicMock()
        mock_table.count = AsyncMock(return_value=1)
        mock_tr_locator = MagicMock()
        mock_tr_locator.all = AsyncMock(return_value=[mock_row_1, mock_row_2])
        mock_table.locator.return_value = mock_tr_locator

        mock_page.locator.return_value = mock_table

        result = await extract_table_data(mock_page, "table.data")
        assert len(result) == 2
        assert result[0] == ["Header1", "Header2"]
        assert result[1] == ["Value1", "Value2"]

    @pytest.mark.asyncio
    async def test_正常系_テーブルが見つからない場合空リストを返す(self) -> None:
        from notebooklm.browser.helpers import extract_table_data

        mock_page = _make_page_mock()
        mock_locator = _make_locator_mock(count=0)
        mock_page.locator.return_value = mock_locator

        result = await extract_table_data(mock_page, "table.missing")
        assert result == []
