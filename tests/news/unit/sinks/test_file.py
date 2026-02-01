"""Unit tests for FileSink in the news package.

Tests for the FileSink class that outputs news articles to JSON files.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import HttpUrl

from news.core.article import Article, ArticleSource, ContentType, Provider
from news.core.result import FetchResult
from news.core.sink import SinkProtocol, SinkType
from news.sinks.file import FileSink, WriteMode


class TestWriteModeEnum:
    """Test WriteMode enumeration."""

    def test_正常系_WriteMode_OVERWRITEが存在する(self) -> None:
        """WriteMode.OVERWRITEが定義されていることを確認。"""
        assert hasattr(WriteMode, "OVERWRITE")
        assert WriteMode.OVERWRITE.value == "overwrite"

    def test_正常系_WriteMode_APPENDが存在する(self) -> None:
        """WriteMode.APPENDが定義されていることを確認。"""
        assert hasattr(WriteMode, "APPEND")
        assert WriteMode.APPEND.value == "append"


class TestFileSinkInitialization:
    """Test FileSink initialization."""

    def test_正常系_デフォルト出力ディレクトリで初期化できる(
        self,
        temp_dir: Path,
    ) -> None:
        """デフォルト設定でFileSinkを初期化できることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        assert sink.output_dir == temp_dir
        assert sink.write_mode == WriteMode.OVERWRITE

    def test_正常系_APPENDモードで初期化できる(
        self,
        temp_dir: Path,
    ) -> None:
        """APPENDモードでFileSinkを初期化できることを確認。"""
        sink = FileSink(output_dir=temp_dir, write_mode=WriteMode.APPEND)

        assert sink.write_mode == WriteMode.APPEND

    def test_正常系_カスタムファイル名パターンで初期化できる(
        self,
        temp_dir: Path,
    ) -> None:
        """カスタムファイル名パターンでFileSinkを初期化できることを確認。"""
        sink = FileSink(output_dir=temp_dir, filename_pattern="custom_{date}.json")

        assert sink.filename_pattern == "custom_{date}.json"

    def test_異常系_存在しないディレクトリでもエラーにならない(self) -> None:
        """存在しないディレクトリでも初期化時にエラーにならないことを確認。

        ディレクトリは書き込み時に自動作成される。
        """
        sink = FileSink(output_dir=Path("/nonexistent/path"))

        assert sink.output_dir == Path("/nonexistent/path")


class TestFileSinkProtocolCompliance:
    """Test FileSink implements SinkProtocol."""

    def test_正常系_SinkProtocolに準拠する(
        self,
        temp_dir: Path,
    ) -> None:
        """FileSinkがSinkProtocolに準拠することを確認。"""
        sink = FileSink(output_dir=temp_dir)

        assert isinstance(sink, SinkProtocol)

    def test_正常系_sink_nameが正しい(
        self,
        temp_dir: Path,
    ) -> None:
        """sink_nameが正しい値を返すことを確認。"""
        sink = FileSink(output_dir=temp_dir)

        assert sink.sink_name == "json_file"

    def test_正常系_sink_typeがFILEである(
        self,
        temp_dir: Path,
    ) -> None:
        """sink_typeがSinkType.FILEであることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        assert sink.sink_type == SinkType.FILE


class TestFileSinkWrite:
    """Test FileSink.write() method."""

    @pytest.fixture
    def sample_article(self) -> Article:
        """テスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/test-article"),
            title="Test Article Title",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            summary="This is a test article summary.",
            content_type=ContentType.ARTICLE,
            provider=Provider(
                name="Yahoo Finance",
                url=HttpUrl("https://finance.yahoo.com/"),
            ),
            related_tickers=["AAPL"],
            tags=["technology"],
        )

    @pytest.fixture
    def sample_articles(self, sample_article: Article) -> list[Article]:
        """テスト用の複数Articleを提供するフィクスチャ。"""
        article2 = Article(
            url=HttpUrl("https://finance.yahoo.com/news/test-article-2"),
            title="Test Article Title 2",
            published_at=datetime(2026, 1, 27, 22, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_SEARCH,
            summary="This is another test article.",
            tags=["macro"],
        )
        return [sample_article, article2]

    def test_正常系_単一記事を書き込める(
        self,
        temp_dir: Path,
        sample_article: Article,
    ) -> None:
        """単一の記事をJSONファイルに書き込めることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        result = sink.write([sample_article])

        assert result is True
        # ファイルが作成されていることを確認
        files = list(temp_dir.glob("*.json"))
        assert len(files) == 1

    def test_正常系_複数記事を書き込める(
        self,
        temp_dir: Path,
        sample_articles: list[Article],
    ) -> None:
        """複数の記事をJSONファイルに書き込めることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        result = sink.write(sample_articles)

        assert result is True
        files = list(temp_dir.glob("*.json"))
        assert len(files) == 1
        # ファイル内容を確認
        with files[0].open() as f:
            data = json.load(f)
        assert len(data["articles"]) == 2

    def test_正常系_空の記事リストでTrueを返す(
        self,
        temp_dir: Path,
    ) -> None:
        """空の記事リストでwriteしてもTrueを返すことを確認。"""
        sink = FileSink(output_dir=temp_dir)

        result = sink.write([])

        assert result is True

    def test_正常系_JSON出力フォーマットが正しい(
        self,
        temp_dir: Path,
        sample_article: Article,
    ) -> None:
        """JSON出力フォーマットがproject.mdの仕様に準拠していることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        sink.write([sample_article])

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)

        # メタデータの検証
        assert "meta" in data
        assert "fetched_at" in data["meta"]
        assert "sources" in data["meta"]
        assert "article_count" in data["meta"]
        assert "version" in data["meta"]
        assert data["meta"]["version"] == "1.0"
        assert data["meta"]["article_count"] == 1

        # 記事データの検証
        assert "articles" in data
        assert len(data["articles"]) == 1
        article_data = data["articles"][0]
        assert article_data["url"] == "https://finance.yahoo.com/news/test-article"
        assert article_data["title"] == "Test Article Title"
        assert article_data["source"] == "yfinance_ticker"

    def test_正常系_ファイル名パターンが適用される(
        self,
        temp_dir: Path,
        sample_article: Article,
    ) -> None:
        """ファイル名パターンが正しく適用されることを確認。"""
        sink = FileSink(
            output_dir=temp_dir,
            filename_pattern="news_{date}.json",
        )

        sink.write([sample_article])

        files = list(temp_dir.glob("*.json"))
        assert len(files) == 1
        # ファイル名がパターンに従っていることを確認
        filename = files[0].name
        assert filename.startswith("news_")
        assert filename.endswith(".json")
        # YYYYMMDD形式の日付が含まれていることを確認
        date_part = filename.replace("news_", "").replace(".json", "")
        assert len(date_part) == 8
        assert date_part.isdigit()

    def test_正常系_メタデータを追加できる(
        self,
        temp_dir: Path,
        sample_article: Article,
    ) -> None:
        """カスタムメタデータをJSON出力に含められることを確認。"""
        sink = FileSink(output_dir=temp_dir)
        metadata = {"custom_field": "custom_value", "run_id": "test-123"}

        sink.write([sample_article], metadata=metadata)

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)
        assert data["meta"]["custom_field"] == "custom_value"
        assert data["meta"]["run_id"] == "test-123"

    def test_正常系_sourcesにすべてのソース名が含まれる(
        self,
        temp_dir: Path,
        sample_articles: list[Article],
    ) -> None:
        """meta.sourcesに全てのArticleSourceが含まれることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        sink.write(sample_articles)

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)
        assert set(data["meta"]["sources"]) == {"yfinance_ticker", "yfinance_search"}


class TestFileSinkWriteMode:
    """Test FileSink write modes (OVERWRITE and APPEND)."""

    @pytest.fixture
    def sample_article_1(self) -> Article:
        """テスト用のArticle 1を提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/article-1"),
            title="Article 1",
            published_at=datetime(2026, 1, 27, 10, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

    @pytest.fixture
    def sample_article_2(self) -> Article:
        """テスト用のArticle 2を提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/article-2"),
            title="Article 2",
            published_at=datetime(2026, 1, 27, 11, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_SEARCH,
        )

    def test_正常系_OVERWRITEモードで上書きされる(
        self,
        temp_dir: Path,
        sample_article_1: Article,
        sample_article_2: Article,
    ) -> None:
        """OVERWRITEモードで既存ファイルが上書きされることを確認。"""
        sink = FileSink(output_dir=temp_dir, write_mode=WriteMode.OVERWRITE)

        # 最初の書き込み
        sink.write([sample_article_1])
        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data1 = json.load(f)
        assert len(data1["articles"]) == 1
        assert data1["articles"][0]["title"] == "Article 1"

        # 2回目の書き込み（上書き）
        sink.write([sample_article_2])
        with files[0].open() as f:
            data2 = json.load(f)
        assert len(data2["articles"]) == 1
        assert data2["articles"][0]["title"] == "Article 2"

    def test_正常系_APPENDモードで追記される(
        self,
        temp_dir: Path,
        sample_article_1: Article,
        sample_article_2: Article,
    ) -> None:
        """APPENDモードで既存ファイルに追記されることを確認。"""
        sink = FileSink(output_dir=temp_dir, write_mode=WriteMode.APPEND)

        # 最初の書き込み
        sink.write([sample_article_1])

        # 2回目の書き込み（追記）
        sink.write([sample_article_2])

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)
        assert len(data["articles"]) == 2
        # 順序が保持されていることを確認
        assert data["articles"][0]["title"] == "Article 1"
        assert data["articles"][1]["title"] == "Article 2"

    def test_正常系_APPENDモードでsourcesが統合される(
        self,
        temp_dir: Path,
        sample_article_1: Article,
        sample_article_2: Article,
    ) -> None:
        """APPENDモードでmeta.sourcesが正しく統合されることを確認。"""
        sink = FileSink(output_dir=temp_dir, write_mode=WriteMode.APPEND)

        sink.write([sample_article_1])  # yfinance_ticker
        sink.write([sample_article_2])  # yfinance_search

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)
        assert set(data["meta"]["sources"]) == {"yfinance_ticker", "yfinance_search"}
        assert data["meta"]["article_count"] == 2

    def test_正常系_APPENDモードで重複URLは追加されない(
        self,
        temp_dir: Path,
        sample_article_1: Article,
    ) -> None:
        """APPENDモードで同じURLの記事は重複して追加されないことを確認。"""
        sink = FileSink(output_dir=temp_dir, write_mode=WriteMode.APPEND)

        sink.write([sample_article_1])
        sink.write([sample_article_1])  # 同じ記事を再度追加

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)
        # 重複が排除されていることを確認
        assert len(data["articles"]) == 1


class TestFileSinkWriteBatch:
    """Test FileSink.write_batch() method."""

    @pytest.fixture
    def sample_fetch_results(self) -> list[FetchResult]:
        """テスト用のFetchResultリストを提供するフィクスチャ。"""
        article1 = Article(
            url=HttpUrl("https://finance.yahoo.com/news/aapl-1"),
            title="AAPL Article",
            published_at=datetime(2026, 1, 27, 10, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )
        article2 = Article(
            url=HttpUrl("https://finance.yahoo.com/news/googl-1"),
            title="GOOGL Article",
            published_at=datetime(2026, 1, 27, 11, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )
        return [
            FetchResult(articles=[article1], success=True, ticker="AAPL"),
            FetchResult(articles=[article2], success=True, ticker="GOOGL"),
        ]

    def test_正常系_write_batchで複数FetchResultを書き込める(
        self,
        temp_dir: Path,
        sample_fetch_results: list[FetchResult],
    ) -> None:
        """write_batchで複数のFetchResultを書き込めることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        result = sink.write_batch(sample_fetch_results)

        assert result is True
        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)
        assert len(data["articles"]) == 2

    def test_正常系_空のwrite_batchでTrueを返す(
        self,
        temp_dir: Path,
    ) -> None:
        """空のFetchResultリストでwrite_batchしてもTrueを返すことを確認。"""
        sink = FileSink(output_dir=temp_dir)

        result = sink.write_batch([])

        assert result is True

    def test_正常系_失敗したFetchResultは無視される(
        self,
        temp_dir: Path,
    ) -> None:
        """success=FalseのFetchResultの記事は書き込まれないことを確認。"""
        article = Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test",
            published_at=datetime(2026, 1, 27, 10, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )
        results = [
            FetchResult(articles=[article], success=True, ticker="AAPL"),
            FetchResult(articles=[], success=False, ticker="INVALID"),
        ]
        sink = FileSink(output_dir=temp_dir)

        result = sink.write_batch(results)

        assert result is True
        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)
        assert len(data["articles"]) == 1


class TestFileSinkDirectoryCreation:
    """Test FileSink automatic directory creation."""

    def test_正常系_出力ディレクトリが自動作成される(
        self,
        temp_dir: Path,
    ) -> None:
        """存在しない出力ディレクトリが自動作成されることを確認。"""
        nested_dir = temp_dir / "nested" / "path" / "to" / "output"
        sink = FileSink(output_dir=nested_dir)
        article = Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test",
            published_at=datetime(2026, 1, 27, 10, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

        result = sink.write([article])

        assert result is True
        assert nested_dir.exists()
        files = list(nested_dir.glob("*.json"))
        assert len(files) == 1


class TestFileSinkErrorHandling:
    """Test FileSink error handling."""

    def test_異常系_書き込み権限がない場合Falseを返す(
        self,
        temp_dir: Path,
    ) -> None:
        """書き込み権限がないディレクトリへの書き込みでFalseを返すことを確認。

        Note: This test may be skipped on systems where permission changes don't work.
        """
        import stat

        read_only_dir = temp_dir / "read_only"
        read_only_dir.mkdir()

        try:
            # ディレクトリを読み取り専用に変更
            read_only_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

            sink = FileSink(output_dir=read_only_dir)
            article = Article(
                url=HttpUrl("https://finance.yahoo.com/news/test"),
                title="Test",
                published_at=datetime(2026, 1, 27, 10, 0, 0, tzinfo=timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
            )

            result = sink.write([article])

            assert result is False
        finally:
            # クリーンアップのために権限を戻す
            read_only_dir.chmod(stat.S_IRWXU)


class TestFileSinkGetOutputPath:
    """Test FileSink._get_output_path() method."""

    def test_正常系_デフォルトパターンで正しいパスが生成される(
        self,
        temp_dir: Path,
    ) -> None:
        """デフォルトのファイル名パターンで正しいパスが生成されることを確認。"""
        sink = FileSink(output_dir=temp_dir)

        path = sink._get_output_path()

        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        expected = temp_dir / f"news_{today}.json"
        assert path == expected

    def test_正常系_カスタムパターンで正しいパスが生成される(
        self,
        temp_dir: Path,
    ) -> None:
        """カスタムファイル名パターンで正しいパスが生成されることを確認。"""
        sink = FileSink(
            output_dir=temp_dir,
            filename_pattern="custom_output_{date}.json",
        )

        path = sink._get_output_path()

        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        expected = temp_dir / f"custom_output_{today}.json"
        assert path == expected


class TestFileSinkArticleSerialization:
    """Test FileSink article serialization to JSON."""

    def test_正常系_全フィールドが正しくシリアライズされる(
        self,
        temp_dir: Path,
    ) -> None:
        """Articleの全フィールドが正しくJSONにシリアライズされることを確認。"""
        article = Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            summary="Test summary",
            content_type=ContentType.VIDEO,
            provider=Provider(
                name="Reuters",
                url=HttpUrl("https://www.reuters.com/"),
            ),
            related_tickers=["AAPL", "GOOGL"],
            tags=["tech", "earnings"],
            summary_ja="日本語サマリー",
            category="Technology",
            sentiment=0.5,
        )
        sink = FileSink(output_dir=temp_dir)

        sink.write([article])

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)

        article_data = data["articles"][0]
        assert article_data["url"] == "https://finance.yahoo.com/news/test"
        assert article_data["title"] == "Test Article"
        assert article_data["published_at"] == "2026-01-27T23:33:53+00:00"
        assert article_data["source"] == "yfinance_ticker"
        assert article_data["summary"] == "Test summary"
        assert article_data["content_type"] == "video"
        assert article_data["provider"]["name"] == "Reuters"
        assert article_data["provider"]["url"] == "https://www.reuters.com/"
        assert article_data["related_tickers"] == ["AAPL", "GOOGL"]
        assert article_data["tags"] == ["tech", "earnings"]
        assert article_data["summary_ja"] == "日本語サマリー"
        assert article_data["category"] == "Technology"
        assert article_data["sentiment"] == 0.5

    def test_正常系_Noneフィールドはnullとしてシリアライズされる(
        self,
        temp_dir: Path,
    ) -> None:
        """Noneフィールドがnullとしてシリアライズされることを確認。"""
        article = Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            # summary, provider, thumbnail, summary_ja, category, sentiment are None
        )
        sink = FileSink(output_dir=temp_dir)

        sink.write([article])

        files = list(temp_dir.glob("*.json"))
        with files[0].open() as f:
            data = json.load(f)

        article_data = data["articles"][0]
        assert article_data["summary"] is None
        assert article_data["provider"] is None
        assert article_data["thumbnail"] is None
        assert article_data["summary_ja"] is None
        assert article_data["category"] is None
        assert article_data["sentiment"] is None
