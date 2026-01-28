"""Unit tests for DuplicateChecker.

TDD Red phase: These tests define the expected behavior of DuplicateChecker.
Issue #1719: 重複チェック機構実装

Tests cover:
- DuplicateChecker creation with default and custom settings
- is_duplicate: URL-based duplicate detection
- mark_seen: marking articles as seen
- filter_new: filtering out duplicate articles
- Persistence: save/load to JSON file
- Expiration: cleaning up old entries beyond history_days
- Edge cases: empty articles, expired URLs, concurrent mark_seen
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from news.core.article import Article, ArticleSource
from news.core.dedup import DuplicateChecker


def _make_article(
    url: str = "https://example.com/article/1",
    title: str = "Test Article",
    published_at: datetime | None = None,
) -> Article:
    """Helper to create a test Article with minimal fields."""
    return Article(
        url=url,
        title=title,
        published_at=published_at or datetime.now(timezone.utc),
        source=ArticleSource.YFINANCE_TICKER,
    )


class TestDuplicateCheckerCreation:
    """Test DuplicateChecker instantiation."""

    def test_正常系_デフォルト設定で作成できる(self) -> None:
        """DuplicateCheckerをデフォルト設定で作成できることを確認。"""
        checker = DuplicateChecker()

        assert checker.history_days == 7
        assert checker.seen_count == 0

    def test_正常系_カスタムhistory_daysで作成できる(self) -> None:
        """カスタムのhistory_daysで作成できることを確認。"""
        checker = DuplicateChecker(history_days=30)

        assert checker.history_days == 30

    def test_異常系_history_daysが0以下でValueError(self) -> None:
        """history_daysが0以下の場合ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="history_days must be positive"):
            DuplicateChecker(history_days=0)

        with pytest.raises(ValueError, match="history_days must be positive"):
            DuplicateChecker(history_days=-1)


class TestIsDuplicate:
    """Test DuplicateChecker.is_duplicate method."""

    def test_正常系_未登録のURLはFalse(self) -> None:
        """未登録のURLに対してis_duplicateがFalseを返すことを確認。"""
        checker = DuplicateChecker()
        article = _make_article(url="https://example.com/new-article")

        assert checker.is_duplicate(article) is False

    def test_正常系_登録済みのURLはTrue(self) -> None:
        """mark_seen後にis_duplicateがTrueを返すことを確認。"""
        checker = DuplicateChecker()
        article = _make_article(url="https://example.com/seen-article")

        checker.mark_seen(article)

        assert checker.is_duplicate(article) is True

    def test_正常系_異なるURLはFalse(self) -> None:
        """異なるURLの記事はis_duplicateがFalseを返すことを確認。"""
        checker = DuplicateChecker()
        article1 = _make_article(url="https://example.com/article-1")
        article2 = _make_article(url="https://example.com/article-2")

        checker.mark_seen(article1)

        assert checker.is_duplicate(article2) is False

    def test_正常系_同じURLで異なるタイトルもTrue(self) -> None:
        """同じURLで異なるタイトルの記事もis_duplicateがTrueを返すことを確認。"""
        checker = DuplicateChecker()
        article1 = _make_article(
            url="https://example.com/article",
            title="Original Title",
        )
        article2 = _make_article(
            url="https://example.com/article",
            title="Updated Title",
        )

        checker.mark_seen(article1)

        assert checker.is_duplicate(article2) is True


class TestMarkSeen:
    """Test DuplicateChecker.mark_seen method."""

    def test_正常系_mark_seenでURLが登録される(self) -> None:
        """mark_seenで記事URLが登録されることを確認。"""
        checker = DuplicateChecker()
        article = _make_article(url="https://example.com/new")

        checker.mark_seen(article)

        assert checker.seen_count == 1
        assert checker.is_duplicate(article) is True

    def test_正常系_同じURLを複数回mark_seenしても重複しない(self) -> None:
        """同じURLを複数回mark_seenしてもカウントが増えないことを確認。"""
        checker = DuplicateChecker()
        article = _make_article(url="https://example.com/article")

        checker.mark_seen(article)
        checker.mark_seen(article)
        checker.mark_seen(article)

        assert checker.seen_count == 1

    def test_正常系_複数の異なるURLをmark_seenできる(self) -> None:
        """複数の異なるURLをmark_seenできることを確認。"""
        checker = DuplicateChecker()

        for i in range(5):
            article = _make_article(url=f"https://example.com/article-{i}")
            checker.mark_seen(article)

        assert checker.seen_count == 5


class TestFilterNew:
    """Test DuplicateChecker.filter_new method."""

    def test_正常系_全て新規の場合は全件返す(self) -> None:
        """全て新規記事の場合、全件が返されることを確認。"""
        checker = DuplicateChecker()
        articles = [
            _make_article(url=f"https://example.com/article-{i}") for i in range(3)
        ]

        new_articles = checker.filter_new(articles)

        assert len(new_articles) == 3

    def test_正常系_全て重複の場合は空リスト(self) -> None:
        """全て重複記事の場合、空リストが返されることを確認。"""
        checker = DuplicateChecker()
        articles = [
            _make_article(url=f"https://example.com/article-{i}") for i in range(3)
        ]

        # Mark all as seen
        for article in articles:
            checker.mark_seen(article)

        new_articles = checker.filter_new(articles)

        assert len(new_articles) == 0

    def test_正常系_一部重複の場合は新規のみ返す(self) -> None:
        """一部重複の場合、新規記事のみが返されることを確認。"""
        checker = DuplicateChecker()

        # Mark first 2 as seen
        for i in range(2):
            article = _make_article(url=f"https://example.com/article-{i}")
            checker.mark_seen(article)

        # Create 4 articles (2 seen + 2 new)
        articles = [
            _make_article(url=f"https://example.com/article-{i}") for i in range(4)
        ]

        new_articles = checker.filter_new(articles)

        assert len(new_articles) == 2
        urls = [str(a.url) for a in new_articles]
        assert "https://example.com/article-2" in urls
        assert "https://example.com/article-3" in urls

    def test_エッジケース_空リストでfilter_new(self) -> None:
        """空リストに対してfilter_newが空リストを返すことを確認。"""
        checker = DuplicateChecker()

        new_articles = checker.filter_new([])

        assert new_articles == []

    def test_正常系_filter_newは元のリストを変更しない(self) -> None:
        """filter_newが元のリストを変更しないことを確認。"""
        checker = DuplicateChecker()
        articles = [
            _make_article(url=f"https://example.com/article-{i}") for i in range(3)
        ]
        checker.mark_seen(articles[0])

        original_len = len(articles)
        checker.filter_new(articles)

        assert len(articles) == original_len


class TestExpiration:
    """Test DuplicateChecker URL expiration."""

    def test_正常系_期限内のURLは重複として検出される(self) -> None:
        """期限内のURLがis_duplicateでTrueを返すことを確認。"""
        checker = DuplicateChecker(history_days=7)
        article = _make_article(url="https://example.com/recent")

        checker.mark_seen(article)

        assert checker.is_duplicate(article) is True

    def test_正常系_期限切れのURLは重複として検出されない(self) -> None:
        """期限切れのURLがis_duplicateでFalseを返すことを確認。"""
        checker = DuplicateChecker(history_days=7)
        article = _make_article(url="https://example.com/old")

        # Manually add an old entry
        old_time = datetime.now(timezone.utc) - timedelta(days=8)
        checker._seen_urls[str(article.url)] = old_time.isoformat()

        assert checker.is_duplicate(article) is False

    def test_正常系_clean_expiredで期限切れエントリが削除される(self) -> None:
        """clean_expiredで期限切れエントリが削除されることを確認。"""
        checker = DuplicateChecker(history_days=7)

        # Add recent entry
        recent_article = _make_article(url="https://example.com/recent")
        checker.mark_seen(recent_article)

        # Add old entry manually
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        checker._seen_urls["https://example.com/old"] = old_time.isoformat()

        assert checker.seen_count == 2

        checker.clean_expired()

        assert checker.seen_count == 1
        assert not checker.is_duplicate(_make_article(url="https://example.com/old"))
        assert checker.is_duplicate(recent_article)


class TestPersistence:
    """Test DuplicateChecker save/load persistence."""

    def test_正常系_JSONファイルに保存できる(self, temp_dir: Path) -> None:
        """DuplicateCheckerの状態をJSONファイルに保存できることを確認。"""
        checker = DuplicateChecker(history_days=7)
        article = _make_article(url="https://example.com/article-1")
        checker.mark_seen(article)

        file_path = temp_dir / "seen_urls.json"
        checker.save(file_path)

        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert "https://example.com/article-1" in content

    def test_正常系_JSONファイルから読み込める(self, temp_dir: Path) -> None:
        """JSONファイルからDuplicateCheckerの状態を読み込めることを確認。"""
        checker = DuplicateChecker(history_days=7)
        for i in range(3):
            article = _make_article(url=f"https://example.com/article-{i}")
            checker.mark_seen(article)

        file_path = temp_dir / "seen_urls.json"
        checker.save(file_path)

        loaded = DuplicateChecker.load(file_path, history_days=7)

        assert loaded.seen_count == 3
        for i in range(3):
            article = _make_article(url=f"https://example.com/article-{i}")
            assert loaded.is_duplicate(article) is True

    def test_正常系_save_loadの往復(self, temp_dir: Path) -> None:
        """save/loadを往復してもデータが保持されることを確認。"""
        checker = DuplicateChecker(history_days=14)
        urls = [f"https://example.com/article-{i}" for i in range(5)]
        for url in urls:
            checker.mark_seen(_make_article(url=url))

        file_path = temp_dir / "seen_urls.json"
        checker.save(file_path)
        loaded = DuplicateChecker.load(file_path, history_days=14)

        assert loaded.seen_count == 5
        assert loaded.history_days == 14
        for url in urls:
            assert loaded.is_duplicate(_make_article(url=url)) is True

    def test_正常系_存在しないファイルから空のCheckerを作成(
        self, temp_dir: Path
    ) -> None:
        """存在しないファイルパスでloadすると空のCheckerが返ることを確認。"""
        file_path = temp_dir / "non_existent.json"

        loaded = DuplicateChecker.load(file_path)

        assert loaded.seen_count == 0

    def test_正常系_ディレクトリが存在しない場合も保存できる(
        self, temp_dir: Path
    ) -> None:
        """親ディレクトリが存在しない場合も保存できることを確認。"""
        checker = DuplicateChecker()
        checker.mark_seen(_make_article())

        file_path = temp_dir / "subdir" / "deep" / "seen_urls.json"
        checker.save(file_path)

        assert file_path.exists()

    def test_異常系_不正なJSONファイルでValueError(self, temp_dir: Path) -> None:
        """不正なJSONファイルを読み込むとValueErrorが発生することを確認。"""
        file_path = temp_dir / "invalid.json"
        file_path.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid JSON"):
            DuplicateChecker.load(file_path)

    def test_正常系_load時に期限切れエントリが除外される(self, temp_dir: Path) -> None:
        """loadで読み込む際に期限切れエントリが除外されることを確認。"""
        import json

        file_path = temp_dir / "seen_urls.json"

        # Create data with both recent and old entries
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        recent_time = datetime.now(timezone.utc).isoformat()

        data = {
            "https://example.com/old": old_time,
            "https://example.com/recent": recent_time,
        }
        file_path.write_text(json.dumps(data), encoding="utf-8")

        loaded = DuplicateChecker.load(file_path, history_days=7)

        assert loaded.seen_count == 1
        assert not loaded.is_duplicate(_make_article(url="https://example.com/old"))
        assert loaded.is_duplicate(_make_article(url="https://example.com/recent"))

    def test_正常系_空のCheckerを保存できる(self, temp_dir: Path) -> None:
        """空のDuplicateCheckerを保存できることを確認。"""
        checker = DuplicateChecker()
        file_path = temp_dir / "empty.json"

        checker.save(file_path)

        assert file_path.exists()
        loaded = DuplicateChecker.load(file_path)
        assert loaded.seen_count == 0


class TestSeenCount:
    """Test DuplicateChecker.seen_count property."""

    def test_正常系_初期状態のseen_countは0(self) -> None:
        """初期状態のseen_countが0であることを確認。"""
        checker = DuplicateChecker()
        assert checker.seen_count == 0

    def test_正常系_mark_seen後のseen_countが正しい(self) -> None:
        """mark_seen後のseen_countが正しいことを確認。"""
        checker = DuplicateChecker()

        for i in range(10):
            checker.mark_seen(_make_article(url=f"https://example.com/article-{i}"))

        assert checker.seen_count == 10
