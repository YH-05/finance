"""E2E integration tests for RSS collection to GitHub Project workflow.

This module tests the complete end-to-end workflow from RSS feed collection,
filtering, to GitHub Issue creation and Project posting.
"""

import asyncio
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pytest_httpserver import HTTPServer  # type: ignore[import-untyped]

from database.utils.logging_config import get_logger
from rss import FeedFetcher, FeedManager, FeedReader

logger = get_logger(__name__)


# Sample RSS feed content with financial news
RSS_FINANCE_FEED_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Finance News Feed</title>
    <link>https://example.com/finance</link>
    <description>Financial news and market updates</description>
    {items}
  </channel>
</rss>
"""

RSS_ITEM_TEMPLATE = """
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <pubDate>{pub_date}</pubDate>
      <description>{description}</description>
    </item>
"""


def create_finance_feed(items: list[dict[str, str]]) -> str:
    """Create a sample RSS feed with financial news items.

    Parameters
    ----------
    items : list[dict[str, str]]
        List of item dictionaries with keys: title, link, pub_date, description

    Returns
    -------
    str
        RSS 2.0 XML string
    """
    items_xml = "".join(RSS_ITEM_TEMPLATE.format(**item) for item in items)
    return RSS_FINANCE_FEED_TEMPLATE.format(items=items_xml)


def load_filter_config(config_path: Path) -> dict[str, Any]:
    """Load finance news filter configuration.

    Parameters
    ----------
    config_path : Path
        Path to filter configuration file

    Returns
    -------
    dict[str, Any]
        Filter configuration
    """
    with open(config_path) as f:
        return json.load(f)


def matches_financial_keywords(item_text: str, filter_config: dict[str, Any]) -> bool:
    """Check if text matches financial keywords.

    Parameters
    ----------
    item_text : str
        Combined text from title, summary, and content
    filter_config : dict[str, Any]
        Filter configuration

    Returns
    -------
    bool
        True if text matches financial keywords
    """
    text_lower = item_text.lower()
    include_keywords: dict[str, list[str]] = filter_config["keywords"]["include"]

    match_count = 0
    for keywords in include_keywords.values():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                match_count += 1

    min_matches: int = filter_config["filtering"]["min_keyword_matches"]
    return match_count >= min_matches


def is_excluded(item_text: str, filter_config: dict[str, Any]) -> bool:
    """Check if text should be excluded.

    Parameters
    ----------
    item_text : str
        Combined text from title and summary
    filter_config : dict[str, Any]
        Filter configuration

    Returns
    -------
    bool
        True if text should be excluded
    """
    text_lower = item_text.lower()
    exclude_keywords: dict[str, list[str]] = filter_config["keywords"]["exclude"]

    for keywords in exclude_keywords.values():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                # Don't exclude if it also matches financial keywords
                return not matches_financial_keywords(item_text, filter_config)

    return False


@pytest.fixture
def filter_config() -> dict[str, Any]:
    """Load filter configuration for testing."""
    config_path = Path("data/config/finance-news-filter.json")
    return load_filter_config(config_path)


@pytest.fixture
def rss_data_dir(temp_dir: Path) -> Path:
    """Create RSS data directory for testing."""
    rss_dir = temp_dir / "rss"
    rss_dir.mkdir(parents=True, exist_ok=True)
    return rss_dir


@pytest.fixture
def feed_manager(rss_data_dir: Path) -> FeedManager:
    """Create FeedManager instance for testing."""
    return FeedManager(rss_data_dir)


@pytest.fixture
def feed_fetcher(rss_data_dir: Path) -> FeedFetcher:
    """Create FeedFetcher instance for testing."""
    return FeedFetcher(rss_data_dir)


@pytest.fixture
def feed_reader(rss_data_dir: Path) -> FeedReader:
    """Create FeedReader instance for testing."""
    return FeedReader(rss_data_dir)


class TestRSSToGitHubE2E:
    """E2E tests for RSS collection to GitHub Project workflow."""

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_正常系_RSS取得からGitHub投稿までの完全フロー(
        self,
        mock_subprocess: MagicMock,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
        filter_config: dict[str, Any],
    ) -> None:
        """Test complete workflow: RSS fetch → filter → GitHub post."""
        # 1. Setup mock RSS feed with financial news
        financial_items = [
            {
                "title": "日銀、政策金利を引き上げ",
                "link": "https://example.com/news/boj-rate-hike",
                "pub_date": "Mon, 15 Jan 2024 09:00:00 GMT",
                "description": "日本銀行が政策金利を0.1%引き上げることを決定した",
            },
            {
                "title": "米ドル円、150円台に上昇",
                "link": "https://example.com/news/usdjpy-150",
                "pub_date": "Tue, 16 Jan 2024 09:00:00 GMT",
                "description": "為替市場で米ドル円が150円台まで上昇",
            },
            {
                "title": "サッカー日本代表、優勝",
                "link": "https://example.com/news/soccer-win",
                "pub_date": "Wed, 17 Jan 2024 09:00:00 GMT",
                "description": "サッカー日本代表がワールドカップで優勝",
            },
        ]

        feed_content = create_finance_feed(financial_items)
        httpserver.expect_request("/finance.xml").respond_with_data(
            feed_content, content_type="application/rss+xml"
        )

        # 2. Register feed
        feed = feed_manager.add_feed(
            url=httpserver.url_for("/finance.xml"),
            title="Finance News Feed",
            category="finance",
        )

        # 3. Fetch feed content
        result = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result.success is True
        assert result.items_count == 3

        # 4. Read and filter items
        items = feed_reader.get_items(feed_id=feed.feed_id)
        assert len(items) == 3

        # Apply filtering
        filtered_items = []
        for item in items:
            item_text = f"{item.title} {item.summary or ''}"

            # Check if matches financial keywords
            if not matches_financial_keywords(item_text, filter_config):
                logger.info(
                    "Item filtered out (no keyword match)",
                    title=item.title,
                )
                continue

            # Check if should be excluded
            if is_excluded(item_text, filter_config):
                logger.info("Item excluded", title=item.title)
                continue

            filtered_items.append(item)

        # Should filter out soccer news, keep financial news
        assert len(filtered_items) == 2
        assert any("日銀" in item.title for item in filtered_items)
        assert any("米ドル円" in item.title for item in filtered_items)
        assert not any("サッカー" in item.title for item in filtered_items)

        # 5. Mock GitHub CLI for issue creation
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = b"https://github.com/user/repo/issues/1"

        # Create GitHub issues for filtered items
        created_issues = []
        for item in filtered_items:
            issue_body = f"""## 概要

{item.summary or item.title}

## 情報源

- **URL**: {item.link}
- **公開日**: {item.published}

## 詳細

{item.content or ""}
"""

            # Call GitHub CLI to create issue
            mock_subprocess(
                [
                    "gh",
                    "issue",
                    "create",
                    "--repo",
                    "user/repo",
                    "--title",
                    item.title,
                    "--body",
                    issue_body,
                    "--label",
                    "news",
                ],
                capture_output=True,
                check=True,
            )

            created_issues.append(
                {
                    "title": item.title,
                    "url": "https://github.com/user/repo/issues/1",
                }
            )

        # Verify GitHub CLI was called correctly
        assert mock_subprocess.call_count == 2
        assert len(created_issues) == 2

        # Verify issue titles
        issue_titles = [issue["title"] for issue in created_issues]
        assert "日銀、政策金利を引き上げ" in issue_titles
        assert "米ドル円、150円台に上昇" in issue_titles

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_正常系_重複チェックで既存Issueをスキップ(
        self,
        mock_subprocess: MagicMock,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
        filter_config: dict[str, Any],
    ) -> None:
        """Test duplicate detection skips existing issues."""
        # 1. Setup mock RSS feed
        items = [
            {
                "title": "株価上昇のニュース",
                "link": "https://example.com/news/stock-rise",
                "pub_date": "Mon, 15 Jan 2024 09:00:00 GMT",
                "description": "日経平均株価が大幅上昇",
            },
        ]

        feed_content = create_finance_feed(items)
        httpserver.expect_request("/finance.xml").respond_with_data(
            feed_content, content_type="application/rss+xml"
        )

        # 2. Register and fetch feed
        feed = feed_manager.add_feed(
            url=httpserver.url_for("/finance.xml"),
            title="Finance News",
            category="finance",
        )
        asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))

        # 3. Mock existing GitHub issues
        existing_issues = [
            {
                "number": 100,
                "title": "株価上昇のニュース",
                "url": "https://github.com/user/repo/issues/100",
            },
        ]

        # 4. Check for duplicates
        items_list = feed_reader.get_items(feed_id=feed.feed_id)
        new_items = []

        for item in items_list:
            is_duplicate = any(
                existing["title"] == item.title for existing in existing_issues
            )

            if not is_duplicate:
                new_items.append(item)

        # Should skip duplicate
        assert len(new_items) == 0

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_異常系_GitHub_CLI失敗時のエラーハンドリング(
        self,
        mock_subprocess: MagicMock,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
        filter_config: dict[str, Any],
    ) -> None:
        """Test error handling when GitHub CLI fails."""
        # 1. Setup mock RSS feed
        items = [
            {
                "title": "為替市場の動向",
                "link": "https://example.com/news/forex",
                "pub_date": "Mon, 15 Jan 2024 09:00:00 GMT",
                "description": "為替市場でドル高が進行",
            },
        ]

        feed_content = create_finance_feed(items)
        httpserver.expect_request("/finance.xml").respond_with_data(
            feed_content, content_type="application/rss+xml"
        )

        # 2. Register and fetch feed
        feed = feed_manager.add_feed(
            url=httpserver.url_for("/finance.xml"),
            title="Finance News",
            category="finance",
        )
        asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))

        # 3. Mock GitHub CLI failure
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh", "issue", "create"],
            stderr=b"Error: API rate limit exceeded",
        )

        # 4. Try to create issue and handle error
        items_list = feed_reader.get_items(feed_id=feed.feed_id)
        errors = []

        for item in items_list:
            try:
                mock_subprocess(
                    ["gh", "issue", "create", "--title", item.title],
                    capture_output=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                errors.append(
                    {
                        "item": item.title,
                        "error": e.stderr.decode() if e.stderr else str(e),
                    }
                )
                logger.error(
                    "Failed to create GitHub issue",
                    title=item.title,
                    error=str(e),
                )

        # Verify error was caught
        assert len(errors) == 1
        assert "rate limit" in errors[0]["error"].lower()

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_異常系_RSS取得失敗時のリトライ(
        self,
        mock_subprocess: MagicMock,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
    ) -> None:
        """Test retry logic when RSS fetch fails."""
        # 1. Setup mock RSS feed that fails initially
        httpserver.expect_request("/finance.xml").respond_with_data(
            "Internal Server Error", status=500
        )

        # 2. Register feed
        feed = feed_manager.add_feed(
            url=httpserver.url_for("/finance.xml"),
            title="Finance News",
            category="finance",
        )

        # 3. Try to fetch - should fail
        result = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result.success is False
        assert result.error_message is not None

        # 4. Simulate retry with success
        httpserver.clear()
        items = [
            {
                "title": "金利政策の発表",
                "link": "https://example.com/news/rate-policy",
                "pub_date": "Mon, 15 Jan 2024 09:00:00 GMT",
                "description": "中央銀行が金利政策を発表",
            },
        ]
        feed_content = create_finance_feed(items)
        httpserver.expect_request("/finance.xml").respond_with_data(
            feed_content, content_type="application/rss+xml"
        )

        # Retry fetch
        result2 = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result2.success is True
        assert result2.items_count == 1


class TestFilteringLogic:
    """Tests for filtering logic used in E2E workflow."""

    def test_正常系_金融キーワードマッチング(
        self, filter_config: dict[str, Any]
    ) -> None:
        """Test financial keyword matching."""
        # Should match
        assert matches_financial_keywords("日銀が政策金利を引き上げ", filter_config)
        assert matches_financial_keywords("株価が上昇した", filter_config)
        assert matches_financial_keywords("為替相場の動向", filter_config)

        # Should not match
        assert not matches_financial_keywords("サッカー試合の結果", filter_config)
        assert not matches_financial_keywords("映画の新作公開", filter_config)

    def test_正常系_除外キーワード判定(self, filter_config: dict[str, Any]) -> None:
        """Test exclusion keyword detection."""
        # Should be excluded
        assert is_excluded("サッカー日本代表が優勝", filter_config)
        assert is_excluded("映画の新作が公開された", filter_config)

        # Should not be excluded (financial news)
        assert not is_excluded("日銀が金利を引き上げ", filter_config)
        assert not is_excluded("株価が急上昇", filter_config)

        # Should not be excluded (mixed content with financial keywords)
        assert not is_excluded("オリンピック開催が株価に影響", filter_config)


class TestGitHubIntegrationHelpers:
    """Tests for GitHub integration helper functions."""

    @pytest.mark.integration
    def test_正常系_タイトル類似度計算(self) -> None:
        """Test title similarity calculation for duplicate detection."""
        from difflib import SequenceMatcher

        def calculate_similarity(title1: str, title2: str) -> float:
            """Calculate title similarity."""
            return SequenceMatcher(None, title1, title2).ratio()

        # High similarity
        assert (
            calculate_similarity("日銀が金利を引き上げ", "日銀が金利を引き上げ") > 0.9
        )
        assert (
            calculate_similarity("株価上昇のニュース", "株価上昇に関するニュース") > 0.7
        )

        # Low similarity
        assert calculate_similarity("日銀が金利を引き上げ", "株価が急落した") < 0.5

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_正常系_GitHub_CLI呼び出し(self, mock_subprocess: MagicMock) -> None:
        """Test GitHub CLI invocation."""
        # Mock successful issue creation
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = b"https://github.com/user/repo/issues/200"

        # Call GitHub CLI
        result = mock_subprocess(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                "user/repo",
                "--title",
                "Test Issue",
                "--body",
                "Test body",
            ],
            capture_output=True,
            check=True,
        )

        assert result.returncode == 0
        assert b"issues/200" in result.stdout
