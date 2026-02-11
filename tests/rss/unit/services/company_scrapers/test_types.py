"""Unit tests for company_scrapers data types and exception classes."""

import pytest

from rss.services.company_scrapers.types import (
    ArticleMetadata,
    BotDetectionError,
    CompanyConfig,
    CompanyScrapeResult,
    InvestmentContext,
    PdfMetadata,
    RateLimitError,
    ScrapedArticle,
    ScrapingError,
    StructureChangedError,
    StructureReport,
)

# ---------------------------------------------------------------------------
# InvestmentContext
# ---------------------------------------------------------------------------


class TestInvestmentContext:
    """Tests for InvestmentContext frozen dataclass."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        ctx = InvestmentContext()
        assert ctx.tickers == ()
        assert ctx.sectors == ()
        assert ctx.keywords == ()

    def test_正常系_全フィールドを指定して作成できる(self) -> None:
        ctx = InvestmentContext(
            tickers=("NVDA",),
            sectors=("Semiconductor", "Data Center"),
            keywords=("GPU", "CUDA", "H100"),
        )
        assert ctx.tickers == ("NVDA",)
        assert ctx.sectors == ("Semiconductor", "Data Center")
        assert ctx.keywords == ("GPU", "CUDA", "H100")

    def test_正常系_frozenで変更不可(self) -> None:
        ctx = InvestmentContext(tickers=("MSFT",))
        with pytest.raises(AttributeError):
            ctx.tickers = ("GOOGL",)  # type: ignore[misc]

    def test_正常系_等価比較できる(self) -> None:
        ctx1 = InvestmentContext(tickers=("NVDA",), sectors=("Semiconductor",))
        ctx2 = InvestmentContext(tickers=("NVDA",), sectors=("Semiconductor",))
        assert ctx1 == ctx2

    def test_正常系_複数ティッカーを保持できる(self) -> None:
        ctx = InvestmentContext(tickers=("MSFT", "GOOGL"))
        assert len(ctx.tickers) == 2
        assert "MSFT" in ctx.tickers
        assert "GOOGL" in ctx.tickers


# ---------------------------------------------------------------------------
# CompanyConfig
# ---------------------------------------------------------------------------


class TestCompanyConfig:
    """Tests for CompanyConfig frozen dataclass."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        config = CompanyConfig(
            key="openai",
            name="OpenAI",
            category="ai_llm",
            blog_url="https://openai.com/news/",
        )
        assert config.key == "openai"
        assert config.name == "OpenAI"
        assert config.category == "ai_llm"
        assert config.blog_url == "https://openai.com/news/"

    def test_正常系_デフォルト値が正しく設定される(self) -> None:
        config = CompanyConfig(
            key="openai",
            name="OpenAI",
            category="ai_llm",
            blog_url="https://openai.com/news/",
        )
        assert config.article_list_selector == "article"
        assert config.article_title_selector == "h2"
        assert config.article_date_selector == "time"
        assert config.requires_playwright is False
        assert config.rate_limit_seconds == 3.0
        assert config.investment_context == InvestmentContext()

    def test_正常系_全フィールドを指定して作成できる(self) -> None:
        ctx = InvestmentContext(
            tickers=("NVDA",),
            sectors=("Semiconductor",),
            keywords=("GPU",),
        )
        config = CompanyConfig(
            key="nvidia_ai",
            name="NVIDIA",
            category="gpu_chips",
            blog_url="https://blogs.nvidia.com/",
            article_list_selector="div.post",
            article_title_selector="h3.title",
            article_date_selector="span.date",
            requires_playwright=True,
            rate_limit_seconds=5.0,
            investment_context=ctx,
        )
        assert config.key == "nvidia_ai"
        assert config.requires_playwright is True
        assert config.rate_limit_seconds == 5.0
        assert config.investment_context.tickers == ("NVDA",)

    def test_正常系_frozenで変更不可(self) -> None:
        config = CompanyConfig(
            key="openai",
            name="OpenAI",
            category="ai_llm",
            blog_url="https://openai.com/news/",
        )
        with pytest.raises(AttributeError):
            config.key = "changed"  # type: ignore[misc]

    def test_正常系_等価比較できる(self) -> None:
        config1 = CompanyConfig(
            key="openai",
            name="OpenAI",
            category="ai_llm",
            blog_url="https://openai.com/news/",
        )
        config2 = CompanyConfig(
            key="openai",
            name="OpenAI",
            category="ai_llm",
            blog_url="https://openai.com/news/",
        )
        assert config1 == config2


# ---------------------------------------------------------------------------
# ScrapedArticle
# ---------------------------------------------------------------------------


class TestScrapedArticle:
    """Tests for ScrapedArticle frozen dataclass."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        article = ScrapedArticle(
            url="https://openai.com/news/article1",
            title="New Model Released",
            text="Full article text here.",
        )
        assert article.url == "https://openai.com/news/article1"
        assert article.title == "New Model Released"
        assert article.text == "Full article text here."

    def test_正常系_デフォルト値が正しく設定される(self) -> None:
        article = ScrapedArticle(
            url="https://example.com/post",
            title="Title",
            text="Body",
        )
        assert article.source_type == "blog"
        assert article.pdf is None
        assert article.attached_pdfs == ()

    def test_正常系_PDF添付ありで作成できる(self) -> None:
        article = ScrapedArticle(
            url="https://example.com/post",
            title="Earnings Report",
            text="Q4 results...",
            source_type="press_release",
            pdf="https://example.com/report.pdf",
            attached_pdfs=(
                "https://example.com/supplement.pdf",
                "https://example.com/slides.pdf",
            ),
        )
        assert article.pdf == "https://example.com/report.pdf"
        assert len(article.attached_pdfs) == 2

    def test_正常系_frozenで変更不可(self) -> None:
        article = ScrapedArticle(
            url="https://example.com/post",
            title="Title",
            text="Body",
        )
        with pytest.raises(AttributeError):
            article.url = "https://changed.com"  # type: ignore[misc]

    def test_正常系_source_typeリテラル型を受け付ける(self) -> None:
        for source in ("blog", "newsroom", "rss", "press_release"):
            article = ScrapedArticle(
                url="https://example.com",
                title="T",
                text="B",
                source_type=source,  # type: ignore[arg-type]
            )
            assert article.source_type == source


# ---------------------------------------------------------------------------
# CompanyScrapeResult
# ---------------------------------------------------------------------------


class TestCompanyScrapeResult:
    """Tests for CompanyScrapeResult frozen dataclass."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        result = CompanyScrapeResult(company="openai")
        assert result.company == "openai"
        assert result.articles == ()
        assert result.validation == "valid"

    def test_正常系_記事ありで作成できる(self) -> None:
        articles = (
            ScrapedArticle(
                url="https://example.com/1",
                title="Article 1",
                text="Text 1",
            ),
            ScrapedArticle(
                url="https://example.com/2",
                title="Article 2",
                text="Text 2",
            ),
        )
        result = CompanyScrapeResult(
            company="nvidia",
            articles=articles,
            validation="valid",
        )
        assert len(result.articles) == 2
        assert result.articles[0].title == "Article 1"

    def test_正常系_validation_statusのリテラル値(self) -> None:
        for status in ("valid", "partial", "failed"):
            result = CompanyScrapeResult(
                company="test",
                validation=status,  # type: ignore[arg-type]
            )
            assert result.validation == status

    def test_正常系_frozenで変更不可(self) -> None:
        result = CompanyScrapeResult(company="openai")
        with pytest.raises(AttributeError):
            result.company = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ArticleMetadata
# ---------------------------------------------------------------------------


class TestArticleMetadata:
    """Tests for ArticleMetadata frozen dataclass."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        meta = ArticleMetadata(
            url="https://example.com/article",
            title="Article Title",
        )
        assert meta.url == "https://example.com/article"
        assert meta.title == "Article Title"
        assert meta.date is None

    def test_正常系_日付ありで作成できる(self) -> None:
        meta = ArticleMetadata(
            url="https://example.com/article",
            title="Article Title",
            date="2026-02-10T12:00:00+00:00",
        )
        assert meta.date == "2026-02-10T12:00:00+00:00"

    def test_正常系_frozenで変更不可(self) -> None:
        meta = ArticleMetadata(
            url="https://example.com/article",
            title="Title",
        )
        with pytest.raises(AttributeError):
            meta.title = "Changed"  # type: ignore[misc]

    def test_正常系_等価比較できる(self) -> None:
        meta1 = ArticleMetadata(url="https://example.com", title="T")
        meta2 = ArticleMetadata(url="https://example.com", title="T")
        assert meta1 == meta2


# ---------------------------------------------------------------------------
# PdfMetadata
# ---------------------------------------------------------------------------


class TestPdfMetadata:
    """Tests for PdfMetadata frozen dataclass."""

    def test_正常系_全フィールドを指定して作成できる(self) -> None:
        pdf = PdfMetadata(
            url="https://example.com/report.pdf",
            local_path="/data/pdfs/report.pdf",
            company_key="nvidia",
            filename="report.pdf",
        )
        assert pdf.url == "https://example.com/report.pdf"
        assert pdf.local_path == "/data/pdfs/report.pdf"
        assert pdf.company_key == "nvidia"
        assert pdf.filename == "report.pdf"

    def test_正常系_frozenで変更不可(self) -> None:
        pdf = PdfMetadata(
            url="https://example.com/report.pdf",
            local_path="/data/pdfs/report.pdf",
            company_key="nvidia",
            filename="report.pdf",
        )
        with pytest.raises(AttributeError):
            pdf.filename = "changed.pdf"  # type: ignore[misc]

    def test_正常系_等価比較できる(self) -> None:
        pdf1 = PdfMetadata(
            url="https://example.com/r.pdf",
            local_path="/p/r.pdf",
            company_key="nvidia",
            filename="r.pdf",
        )
        pdf2 = PdfMetadata(
            url="https://example.com/r.pdf",
            local_path="/p/r.pdf",
            company_key="nvidia",
            filename="r.pdf",
        )
        assert pdf1 == pdf2


# ---------------------------------------------------------------------------
# StructureReport
# ---------------------------------------------------------------------------


class TestStructureReport:
    """Tests for StructureReport (mutable) dataclass."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        report = StructureReport(company="openai")
        assert report.company == "openai"
        assert report.article_list_hits == 0
        assert report.title_found_count == 0
        assert report.date_found_count == 0
        assert report.hit_rate == 0.0

    def test_正常系_全フィールドを指定して作成できる(self) -> None:
        report = StructureReport(
            company="nvidia",
            article_list_hits=10,
            title_found_count=9,
            date_found_count=8,
            hit_rate=0.9,
        )
        assert report.article_list_hits == 10
        assert report.hit_rate == 0.9

    def test_正常系_mutableで変更可能(self) -> None:
        report = StructureReport(company="openai")
        report.article_list_hits = 5
        report.hit_rate = 0.8
        assert report.article_list_hits == 5
        assert report.hit_rate == 0.8

    def test_正常系_インクリメンタルに更新できる(self) -> None:
        report = StructureReport(company="test")
        report.article_list_hits += 1
        report.title_found_count += 1
        report.date_found_count += 1
        assert report.article_list_hits == 1
        assert report.title_found_count == 1


# ---------------------------------------------------------------------------
# ScrapingError (base)
# ---------------------------------------------------------------------------


class TestScrapingError:
    """Tests for ScrapingError base exception."""

    def test_正常系_メッセージとドメインとURLで作成できる(self) -> None:
        error = ScrapingError(
            "Failed to scrape",
            domain="example.com",
            url="https://example.com/page",
        )
        assert str(error) == "Failed to scrape"
        assert error.domain == "example.com"
        assert error.url == "https://example.com/page"

    def test_正常系_Exceptionを継承している(self) -> None:
        assert issubclass(ScrapingError, Exception)

    def test_正常系_catchできる(self) -> None:
        with pytest.raises(ScrapingError, match="Failed"):
            raise ScrapingError(
                "Failed to scrape",
                domain="example.com",
                url="https://example.com",
            )

    def test_正常系_ExceptionとしてもCatchできる(self) -> None:
        with pytest.raises(Exception, match="Failed"):
            raise ScrapingError(
                "Failed to scrape",
                domain="example.com",
                url="https://example.com",
            )


# ---------------------------------------------------------------------------
# RateLimitError
# ---------------------------------------------------------------------------


class TestRateLimitError:
    """Tests for RateLimitError exception."""

    def test_正常系_ScrapingErrorを継承している(self) -> None:
        assert issubclass(RateLimitError, ScrapingError)

    def test_正常系_retry_afterなしで作成できる(self) -> None:
        error = RateLimitError(
            "Rate limited",
            domain="example.com",
            url="https://example.com/page",
        )
        assert str(error) == "Rate limited"
        assert error.domain == "example.com"
        assert error.url == "https://example.com/page"
        assert error.retry_after is None

    def test_正常系_retry_afterありで作成できる(self) -> None:
        error = RateLimitError(
            "Rate limited",
            domain="example.com",
            url="https://example.com/page",
            retry_after=30.0,
        )
        assert error.retry_after == 30.0

    def test_正常系_ScrapingErrorとしてCatchできる(self) -> None:
        with pytest.raises(ScrapingError):
            raise RateLimitError(
                "429 Too Many Requests",
                domain="example.com",
                url="https://example.com",
            )


# ---------------------------------------------------------------------------
# StructureChangedError
# ---------------------------------------------------------------------------


class TestStructureChangedError:
    """Tests for StructureChangedError exception."""

    def test_正常系_ScrapingErrorを継承している(self) -> None:
        assert issubclass(StructureChangedError, ScrapingError)

    def test_正常系_selectorフィールドを持つ(self) -> None:
        error = StructureChangedError(
            "Blog structure changed",
            domain="openai.com",
            url="https://openai.com/news/",
            selector="article.post",
        )
        assert str(error) == "Blog structure changed"
        assert error.domain == "openai.com"
        assert error.url == "https://openai.com/news/"
        assert error.selector == "article.post"

    def test_正常系_ScrapingErrorとしてCatchできる(self) -> None:
        with pytest.raises(ScrapingError):
            raise StructureChangedError(
                "Structure changed",
                domain="example.com",
                url="https://example.com",
                selector="div.content",
            )


# ---------------------------------------------------------------------------
# BotDetectionError
# ---------------------------------------------------------------------------


class TestBotDetectionError:
    """Tests for BotDetectionError exception."""

    def test_正常系_ScrapingErrorを継承している(self) -> None:
        assert issubclass(BotDetectionError, ScrapingError)

    def test_正常系_メッセージとドメインとURLで作成できる(self) -> None:
        error = BotDetectionError(
            "Bot detected",
            domain="example.com",
            url="https://example.com/page",
        )
        assert str(error) == "Bot detected"
        assert error.domain == "example.com"
        assert error.url == "https://example.com/page"

    def test_正常系_ScrapingErrorとしてCatchできる(self) -> None:
        with pytest.raises(ScrapingError):
            raise BotDetectionError(
                "Captcha required",
                domain="example.com",
                url="https://example.com",
            )


# ---------------------------------------------------------------------------
# Exception hierarchy integration
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    """Tests for the complete exception hierarchy."""

    def test_正常系_全例外がScrapingErrorを継承している(self) -> None:
        assert issubclass(RateLimitError, ScrapingError)
        assert issubclass(StructureChangedError, ScrapingError)
        assert issubclass(BotDetectionError, ScrapingError)

    def test_正常系_ScrapingErrorで全子例外をCatchできる(self) -> None:
        errors = [
            RateLimitError(
                "rate limited",
                domain="d",
                url="u",
            ),
            StructureChangedError(
                "changed",
                domain="d",
                url="u",
                selector="s",
            ),
            BotDetectionError(
                "bot",
                domain="d",
                url="u",
            ),
        ]
        for error in errors:
            with pytest.raises(ScrapingError):
                raise error

    def test_正常系_各例外は区別してCatchできる(self) -> None:
        with pytest.raises(RateLimitError):
            raise RateLimitError("rate", domain="d", url="u")

        with pytest.raises(StructureChangedError):
            raise StructureChangedError("struct", domain="d", url="u", selector="s")

        with pytest.raises(BotDetectionError):
            raise BotDetectionError("bot", domain="d", url="u")


# ---------------------------------------------------------------------------
# Package __init__ imports
# ---------------------------------------------------------------------------


class TestPackageExports:
    """Tests for package-level imports from __init__.py."""

    def test_正常系_initからデータ型をインポートできる(self) -> None:
        from rss.services.company_scrapers import (
            ArticleMetadata,
            CompanyConfig,
            CompanyScrapeResult,
            InvestmentContext,
            PdfMetadata,
            ScrapedArticle,
            StructureReport,
        )

        # Verify they are the correct classes
        assert ArticleMetadata.__name__ == "ArticleMetadata"
        assert CompanyConfig.__name__ == "CompanyConfig"
        assert CompanyScrapeResult.__name__ == "CompanyScrapeResult"
        assert InvestmentContext.__name__ == "InvestmentContext"
        assert PdfMetadata.__name__ == "PdfMetadata"
        assert ScrapedArticle.__name__ == "ScrapedArticle"
        assert StructureReport.__name__ == "StructureReport"
