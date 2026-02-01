"""Unit tests for RSS CLI main module."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import pytest
from click.testing import CliRunner

from rss.cli.main import cli
from rss.services.feed_manager import FeedManager
from rss.storage.json_storage import JSONStorage
from rss.types import FeedItem, FeedItemsData

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


def extract_json(output: str) -> Any:
    """Extract JSON from CLI output, ignoring log lines.

    Parameters
    ----------
    output : str
        CLI output containing JSON and possibly log lines

    Returns
    -------
    Any
        Parsed JSON data

    Raises
    ------
    ValueError
        If no valid JSON found in output
    """
    # Filter out log lines first (lines starting with timestamp)
    lines = output.strip().split("\n")
    json_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Skip log lines (start with timestamp like 2026-01-14)
        if re.match(r"^\d{4}-\d{2}-\d{2}", stripped):
            continue
        json_lines.append(line)

    if json_lines:
        json_str = "\n".join(json_lines)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Fallback: try to find JSON starting with { or [
    # This handles cases where log lines are interspersed
    for start_idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("{", "[")):
            # Found start of JSON, collect until we find valid JSON
            for end_idx in range(len(lines), start_idx, -1):
                candidate = "\n".join(lines[start_idx:end_idx])
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

    raise ValueError(f"No valid JSON found in output: {output[:200]}...")


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def data_dir(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary data directory for testing."""
    # Initialize storage structure by creating the directory
    tmp_path.mkdir(parents=True, exist_ok=True)
    yield tmp_path


@pytest.fixture
def sample_feed(data_dir: Path) -> str:
    """Create a sample feed for testing."""
    manager = FeedManager(data_dir)
    feed = manager.add_feed(
        url="https://example.com/feed.xml",
        title="Test Feed",
        category="test",
    )
    return feed.feed_id


@pytest.fixture
def sample_items(data_dir: Path, sample_feed: str) -> list[FeedItem]:
    """Create sample items for testing."""
    storage = JSONStorage(data_dir)
    items = [
        FeedItem(
            item_id="item-001",
            title="Test Article 1",
            link="https://example.com/article1",
            published="2026-01-14T10:00:00Z",
            summary="This is a test summary about finance.",
            content="Full content here.",
            author="Author One",
            fetched_at="2026-01-14T12:00:00Z",
        ),
        FeedItem(
            item_id="item-002",
            title="Test Article 2",
            link="https://example.com/article2",
            published="2026-01-13T10:00:00Z",
            summary="Another test article about economics.",
            content="More content.",
            author="Author Two",
            fetched_at="2026-01-14T12:00:00Z",
        ),
    ]
    items_data = FeedItemsData(version="1.0", feed_id=sample_feed, items=items)
    storage.save_items(sample_feed, items_data)
    return items


class TestCli:
    """Tests for CLI main group."""

    def test_cli_help(self, cli_runner: CliRunner) -> None:
        """Test CLI help message."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "RSS Feed Management CLI" in result.output
        assert "add" in result.output
        assert "list" in result.output

    def test_cli_version_not_exist(self, cli_runner: CliRunner) -> None:
        """Test that --version is not implemented (expected behavior)."""
        result = cli_runner.invoke(cli, ["--version"])
        # --version is not implemented, should show error
        assert result.exit_code != 0


class TestAddCommand:
    """Tests for add command."""

    def test_add_feed_success(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test successful feed addition."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "add",
                "--url",
                "https://example.com/new-feed.xml",
                "--title",
                "New Feed",
                "--category",
                "finance",
            ],
        )
        assert result.exit_code == 0
        assert "Feed registered successfully" in result.output

    def test_add_feed_json_output(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test add command with JSON output."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "add",
                "--url",
                "https://example.com/json-feed.xml",
                "--title",
                "JSON Feed",
                "--category",
                "test",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = extract_json(result.output)
        assert "feed_id" in data
        assert data["title"] == "JSON Feed"

    def test_add_feed_duplicate_error(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test error when adding duplicate feed URL."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "add",
                "--url",
                "https://example.com/feed.xml",  # Same as sample_feed
                "--title",
                "Duplicate Feed",
                "--category",
                "test",
            ],
        )
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_add_feed_invalid_url(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test error with invalid URL."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "add",
                "--url",
                "not-a-valid-url",
                "--title",
                "Invalid Feed",
                "--category",
                "test",
            ],
        )
        assert result.exit_code == 1
        assert "Error" in result.output


class TestListCommand:
    """Tests for list command."""

    def test_list_feeds_empty(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test listing feeds when none exist."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "list"],
        )
        assert result.exit_code == 0
        assert "No feeds found" in result.output

    def test_list_feeds_with_data(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test listing feeds with existing data."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "list"],
        )
        assert result.exit_code == 0
        assert "Test Feed" in result.output
        assert "Total: 1 feeds" in result.output

    def test_list_feeds_json_output(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test list command with JSON output."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "list", "--json"],
        )
        assert result.exit_code == 0
        data = extract_json(result.output)
        assert len(data) == 1
        assert data[0]["title"] == "Test Feed"

    def test_list_feeds_filter_category(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test listing feeds filtered by category."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "list", "--category", "nonexistent"],
        )
        assert result.exit_code == 0
        assert "No feeds found" in result.output


class TestUpdateCommand:
    """Tests for update command."""

    def test_update_feed_title(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test updating feed title."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "update",
                sample_feed,
                "--title",
                "Updated Title",
            ],
        )
        assert result.exit_code == 0
        assert "Feed updated successfully" in result.output
        assert "Updated Title" in result.output

    def test_update_feed_not_found(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test error when updating non-existent feed."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "update",
                "nonexistent-id",
                "--title",
                "New Title",
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_update_feed_json_output(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test update command with JSON output."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "update",
                sample_feed,
                "--category",
                "updated",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = extract_json(result.output)
        assert data["category"] == "updated"


class TestRemoveCommand:
    """Tests for remove command."""

    def test_remove_feed_success(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test successful feed removal."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "remove", sample_feed],
        )
        assert result.exit_code == 0
        assert "Feed removed successfully" in result.output

    def test_remove_feed_not_found(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test error when removing non-existent feed."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "remove", "nonexistent-id"],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_remove_feed_json_output(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test remove command with JSON output."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "remove", sample_feed, "--json"],
        )
        assert result.exit_code == 0
        data = extract_json(result.output)
        assert data["status"] == "removed"


class TestFetchCommand:
    """Tests for fetch command."""

    def test_fetch_requires_arg_or_all(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test that fetch requires feed_id or --all."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "fetch"],
        )
        assert result.exit_code == 1
        assert "Specify feed_id or --all" in result.output

    def test_fetch_all_empty(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test fetch all when no feeds exist."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "fetch", "--all"],
        )
        assert result.exit_code == 0
        assert "No feeds to fetch" in result.output


class TestItemsCommand:
    """Tests for items command."""

    def test_items_empty(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
    ) -> None:
        """Test listing items when none exist."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "items", sample_feed],
        )
        assert result.exit_code == 0
        assert "No items found" in result.output

    def test_items_with_data(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
        sample_items: list[FeedItem],
    ) -> None:
        """Test listing items with existing data."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "items", sample_feed],
        )
        assert result.exit_code == 0
        assert "Test Article 1" in result.output
        assert "Showing 2 items" in result.output

    def test_items_json_output(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
        sample_items: list[FeedItem],
    ) -> None:
        """Test items command with JSON output."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "items", sample_feed, "--json"],
        )
        assert result.exit_code == 0
        data = extract_json(result.output)
        assert len(data) == 2
        assert data[0]["title"] == "Test Article 1"

    def test_items_with_limit(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
        sample_items: list[FeedItem],
    ) -> None:
        """Test items command with limit."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "items", sample_feed, "--limit", "1"],
        )
        assert result.exit_code == 0
        assert "Showing 1 items" in result.output


class TestSearchCommand:
    """Tests for search command."""

    def test_search_no_results(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
        sample_items: list[FeedItem],
    ) -> None:
        """Test search with no matching results."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "search", "-q", "nonexistent"],
        )
        assert result.exit_code == 0
        assert "No items found" in result.output

    def test_search_with_results(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
        sample_items: list[FeedItem],
    ) -> None:
        """Test search with matching results."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "search", "-q", "finance"],
        )
        assert result.exit_code == 0
        assert "Test Article 1" in result.output
        assert "Found 1 items" in result.output

    def test_search_json_output(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
        sample_items: list[FeedItem],
    ) -> None:
        """Test search command with JSON output."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "search", "-q", "test", "--json"],
        )
        assert result.exit_code == 0
        data = extract_json(result.output)
        assert len(data) == 2

    def test_search_filter_category(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
        sample_feed: str,
        sample_items: list[FeedItem],
    ) -> None:
        """Test search with category filter."""
        result = cli_runner.invoke(
            cli,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "-q",
                "test",
                "--category",
                "nonexistent",
            ],
        )
        assert result.exit_code == 0
        assert "No items found" in result.output


class TestExitCodes:
    """Tests for exit codes."""

    def test_success_exit_code(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test that successful commands return exit code 0."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "list"],
        )
        assert result.exit_code == 0

    def test_error_exit_code(
        self,
        cli_runner: CliRunner,
        data_dir: Path,
    ) -> None:
        """Test that error commands return exit code 1."""
        result = cli_runner.invoke(
            cli,
            ["--data-dir", str(data_dir), "remove", "nonexistent"],
        )
        assert result.exit_code == 1
