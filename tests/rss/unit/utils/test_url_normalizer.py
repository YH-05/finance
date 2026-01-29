"""Unit tests for URL normalization and duplicate detection utilities.

Tests cover:
- normalize_url: URL normalization for duplicate comparison
- _is_tracking_param: Tracking parameter identification
- calculate_title_similarity: Jaccard title similarity
- is_duplicate: Combined URL + title duplicate detection
"""

from __future__ import annotations

import pytest

from rss.utils.url_normalizer import (
    TITLE_SIMILARITY_THRESHOLD,
    TRACKING_PARAMS,
    _is_tracking_param,
    calculate_title_similarity,
    is_duplicate,
    normalize_url,
)

# ---------------------------------------------------------------------------
# normalize_url tests
# ---------------------------------------------------------------------------


class TestNormalizeUrl:
    """Test URL normalization function."""

    # --- Basic normalization ---

    def test_正常系_末尾スラッシュ除去(self) -> None:
        assert (
            normalize_url("https://example.com/article/")
            == "https://example.com/article"
        )

    def test_正常系_複数の末尾スラッシュ除去(self) -> None:
        assert (
            normalize_url("https://example.com/article///")
            == "https://example.com/article"
        )

    def test_正常系_ホスト部分の小文字化(self) -> None:
        assert (
            normalize_url("https://EXAMPLE.COM/Article")
            == "https://example.com/Article"
        )

    def test_正常系_wwwプレフィックス除去(self) -> None:
        assert (
            normalize_url("https://www.cnbc.com/article") == "https://cnbc.com/article"
        )

    def test_正常系_WWWプレフィックス除去_大文字(self) -> None:
        assert (
            normalize_url("https://WWW.CNBC.COM/article") == "https://cnbc.com/article"
        )

    def test_正常系_wwwなしはそのまま(self) -> None:
        assert normalize_url("https://cnbc.com/article") == "https://cnbc.com/article"

    def test_正常系_wwwで始まるドメインは除去しない(self) -> None:
        # "www2.example.com" should not have "www." removed
        result = normalize_url("https://www2.example.com/article")
        assert result == "https://www2.example.com/article"

    # --- Fragment removal ---

    def test_正常系_フラグメント除去(self) -> None:
        assert (
            normalize_url("https://example.com/article#section")
            == "https://example.com/article"
        )

    def test_正常系_フラグメント除去_空フラグメント(self) -> None:
        assert (
            normalize_url("https://example.com/article#")
            == "https://example.com/article"
        )

    def test_正常系_フラグメントなしはそのまま(self) -> None:
        assert (
            normalize_url("https://example.com/article")
            == "https://example.com/article"
        )

    # --- index.html removal ---

    def test_正常系_末尾のindex_html除去(self) -> None:
        assert (
            normalize_url("https://example.com/news/index.html")
            == "https://example.com/news"
        )

    def test_正常系_パス末尾以外のindex_htmlは除去しない(self) -> None:
        # index.html in the middle of the path should not be removed
        result = normalize_url("https://example.com/index.html/other")
        assert result == "https://example.com/index.html/other"

    def test_正常系_ルートのindex_htmlも除去(self) -> None:
        result = normalize_url("https://example.com/index.html")
        # "/index.html" ends with "/index.html", so it is removed
        assert result == "https://example.com"

    # --- Tracking parameter removal ---

    def test_正常系_utm_パラメータ除去(self) -> None:
        url = "https://example.com/article?utm_source=twitter&utm_medium=social"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_fbclid除去(self) -> None:
        url = "https://example.com/article?fbclid=abc123"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_gclid除去(self) -> None:
        url = "https://example.com/article?gclid=xyz789"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_ref除去(self) -> None:
        url = "https://example.com/article?ref=homepage"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_campaign除去(self) -> None:
        url = "https://example.com/article?campaign=winter2026"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_sref除去(self) -> None:
        url = "https://example.com/article?sref=abc"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_mod除去(self) -> None:
        url = "https://example.com/article?mod=homepage"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_非トラッキングパラメータ保持(self) -> None:
        url = "https://example.com/article?page=2&sort=date"
        result = normalize_url(url)
        assert "page=2" in result
        assert "sort=date" in result

    def test_正常系_混在パラメータでトラッキングのみ除去(self) -> None:
        url = "https://example.com/article?page=2&utm_source=twitter&sort=date"
        result = normalize_url(url)
        assert "page=2" in result
        assert "sort=date" in result
        assert "utm_source" not in result

    def test_正常系_guce_プレフィックス除去(self) -> None:
        url = "https://example.com/article?guce_referrer=abc&guce_id=xyz"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_ncid除去(self) -> None:
        url = "https://example.com/article?ncid=abc123"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_si除去(self) -> None:
        url = "https://example.com/article?si=abc123"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_mc_cid除去(self) -> None:
        url = "https://example.com/article?mc_cid=abc123"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_mc_eid除去(self) -> None:
        url = "https://example.com/article?mc_eid=xyz789"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_taid除去(self) -> None:
        url = "https://example.com/article?taid=abc"
        assert normalize_url(url) == "https://example.com/article"

    def test_正常系_cmpid除去(self) -> None:
        url = "https://example.com/article?cmpid=van123"
        assert normalize_url(url) == "https://example.com/article"

    # --- Combined normalization ---

    def test_正常系_全正規化を組み合わせ(self) -> None:
        url = "https://WWW.CNBC.COM/news/article/?utm_source=twitter&page=1#comments"
        result = normalize_url(url)
        assert "www." not in result
        assert "cnbc.com" in result
        assert "utm_source" not in result
        assert "page=1" in result
        assert "#comments" not in result
        # No trailing slash
        assert not result.endswith("/")

    def test_正常系_同一記事の異なるURL表現を正規化(self) -> None:
        url1 = "https://www.cnbc.com/2026/01/15/markets.html?utm_source=google"
        url2 = "https://cnbc.com/2026/01/15/markets.html#section"
        url3 = "https://CNBC.COM/2026/01/15/markets.html/"

        assert normalize_url(url1) == normalize_url(url2) == normalize_url(url3)

    # --- Edge cases ---

    def test_エッジケース_空文字列(self) -> None:
        assert normalize_url("") == ""

    def test_エッジケース_クエリパラメータなし(self) -> None:
        assert (
            normalize_url("https://example.com/article")
            == "https://example.com/article"
        )

    def test_エッジケース_スキームなしURL(self) -> None:
        # urlparse handles scheme-less URLs by putting them in path
        result = normalize_url("example.com/article")
        assert isinstance(result, str)

    def test_エッジケース_HTTPスキーム(self) -> None:
        result = normalize_url("http://www.example.com/article")
        assert result == "http://example.com/article"

    def test_エッジケース_パスなし(self) -> None:
        result = normalize_url("https://example.com")
        assert result == "https://example.com"

    def test_エッジケース_ポート番号付きURL(self) -> None:
        result = normalize_url("https://example.com:8080/article")
        assert result == "https://example.com:8080/article"


# ---------------------------------------------------------------------------
# _is_tracking_param tests
# ---------------------------------------------------------------------------


class TestIsTrackingParam:
    """Test tracking parameter identification."""

    def test_正常系_utm_sourceはトラッキング(self) -> None:
        assert _is_tracking_param("utm_source") is True

    def test_正常系_utm_mediumはトラッキング(self) -> None:
        assert _is_tracking_param("utm_medium") is True

    def test_正常系_utm_campaignはトラッキング(self) -> None:
        assert _is_tracking_param("utm_campaign") is True

    def test_正常系_fbclidはトラッキング(self) -> None:
        assert _is_tracking_param("fbclid") is True

    def test_正常系_gclidはトラッキング(self) -> None:
        assert _is_tracking_param("gclid") is True

    def test_正常系_refはトラッキング(self) -> None:
        assert _is_tracking_param("ref") is True

    def test_正常系_sourceはトラッキング(self) -> None:
        assert _is_tracking_param("source") is True

    def test_正常系_pageは非トラッキング(self) -> None:
        assert _is_tracking_param("page") is False

    def test_正常系_sortは非トラッキング(self) -> None:
        assert _is_tracking_param("sort") is False

    def test_正常系_idは非トラッキング(self) -> None:
        assert _is_tracking_param("id") is False

    def test_正常系_guce_referrerはトラッキング(self) -> None:
        assert _is_tracking_param("guce_referrer") is True


# ---------------------------------------------------------------------------
# calculate_title_similarity tests
# ---------------------------------------------------------------------------


class TestCalculateTitleSimilarity:
    """Test Jaccard title similarity calculation."""

    def test_正常系_同一タイトルで類似度1(self) -> None:
        assert (
            calculate_title_similarity("S&P 500 hits record", "S&P 500 hits record")
            == 1.0
        )

    def test_正常系_完全に異なるタイトルで類似度0(self) -> None:
        result = calculate_title_similarity(
            "Apple announces iPhone", "Bitcoin reaches milestone"
        )
        assert result == 0.0

    def test_正常系_部分一致で中間値(self) -> None:
        result = calculate_title_similarity(
            "S&P 500 hits record high", "S&P 500 reaches record"
        )
        assert 0.0 < result < 1.0

    def test_正常系_大文字小文字を区別しない(self) -> None:
        assert calculate_title_similarity("BREAKING NEWS", "breaking news") == 1.0

    def test_エッジケース_空文字列は0(self) -> None:
        assert calculate_title_similarity("", "Some title") == 0.0

    def test_エッジケース_両方空文字列は0(self) -> None:
        assert calculate_title_similarity("", "") == 0.0

    def test_正常系_日本語タイトル(self) -> None:
        result = calculate_title_similarity("日経平均株価が上昇", "日経平均株価が下落")
        # Both share "日経平均株価が" as one word-split token in Japanese
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# is_duplicate tests
# ---------------------------------------------------------------------------


class TestIsDuplicate:
    """Test combined URL + title duplicate detection."""

    def test_正常系_URL一致で重複検出(self) -> None:
        new_item = {
            "link": "https://www.cnbc.com/2026/01/15/markets.html",
            "title": "Markets Today",
        }
        existing_issues = [
            {
                "article_url": "https://cnbc.com/2026/01/15/markets.html",
                "title": "[株価指数] Markets Today",
                "number": 42,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is True
        assert number == 42
        assert reason == "URL一致"

    def test_正常系_URL一致_wwwの差異を吸収(self) -> None:
        new_item = {
            "link": "https://www.example.com/article",
            "title": "Article",
        }
        existing_issues = [
            {
                "article_url": "https://example.com/article",
                "title": "[Index] Article",
                "number": 100,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is True
        assert number == 100

    def test_正常系_URL一致_トラッキングパラメータの差異を吸収(self) -> None:
        new_item = {
            "link": "https://example.com/article?utm_source=rss",
            "title": "Article",
        }
        existing_issues = [
            {
                "article_url": "https://example.com/article?utm_source=web",
                "title": "[Index] Article",
                "number": 101,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is True

    def test_正常系_タイトル類似で重複検出(self) -> None:
        new_item = {
            "link": "https://different-site.com/article",
            "title": "S&P 500 hits record high today",
        }
        existing_issues = [
            {
                "article_url": "https://example.com/other-article",
                "title": "[株価指数] S&P 500 hits record high today",
                "number": 50,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is True
        assert number == 50
        assert reason is not None
        assert "タイトル類似" in reason

    def test_正常系_重複なし(self) -> None:
        new_item = {
            "link": "https://example.com/new-article",
            "title": "Completely different topic about technology",
        }
        existing_issues = [
            {
                "article_url": "https://example.com/old-article",
                "title": "[マクロ経済] FRB raises interest rates",
                "number": 200,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is False
        assert number is None
        assert reason is None

    def test_正常系_空の既存Issue一覧で重複なし(self) -> None:
        new_item = {
            "link": "https://example.com/article",
            "title": "New article",
        }
        is_dup, number, reason = is_duplicate(new_item, [])
        assert is_dup is False
        assert number is None
        assert reason is None

    def test_正常系_テーマプレフィックスを除去して比較(self) -> None:
        new_item = {
            "link": "https://different-url.com/article",
            "title": "S&P 500 record high close",
        }
        existing_issues = [
            {
                "article_url": "https://other-url.com/article",
                "title": "[株価指数] S&P 500 record high close",
                "number": 300,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is True
        assert number == 300

    def test_正常系_linkが空でURLマッチしない(self) -> None:
        new_item = {
            "link": "",
            "title": "Article without URL",
        }
        existing_issues = [
            {
                "article_url": "https://example.com/article",
                "title": "[Index] Different article",
                "number": 400,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is False

    def test_正常系_article_urlが空でURLマッチしない(self) -> None:
        new_item = {
            "link": "https://example.com/article",
            "title": "New article",
        }
        existing_issues = [
            {
                "article_url": "",
                "title": "[Index] Different article",
                "number": 500,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is False

    def test_正常系_カスタム閾値で判定(self) -> None:
        new_item = {
            "link": "https://example.com/new",
            "title": "Markets up today strongly",
        }
        existing_issues = [
            {
                "article_url": "https://other.com/old",
                "title": "[Index] Markets down today",
                "number": 600,
            }
        ]
        # With low threshold, should match
        is_dup_low, _, _ = is_duplicate(new_item, existing_issues, threshold=0.3)
        # With high threshold, should not match
        is_dup_high, _, _ = is_duplicate(new_item, existing_issues, threshold=0.99)
        assert is_dup_low is True
        assert is_dup_high is False

    def test_正常系_フラグメント違いは同一記事(self) -> None:
        new_item = {
            "link": "https://example.com/article#section1",
            "title": "Article",
        }
        existing_issues = [
            {
                "article_url": "https://example.com/article#section2",
                "title": "[Index] Article",
                "number": 700,
            }
        ]
        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is True
        assert reason == "URL一致"


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Test module constants."""

    def test_正常系_TRACKING_PARAMSはfrozenset(self) -> None:
        assert isinstance(TRACKING_PARAMS, frozenset)

    def test_正常系_既存パラメータを含む(self) -> None:
        assert "utm_" in TRACKING_PARAMS
        assert "fbclid" in TRACKING_PARAMS
        assert "gclid" in TRACKING_PARAMS
        assert "ncid" in TRACKING_PARAMS

    def test_正常系_新規追加パラメータを含む(self) -> None:
        assert "ref" in TRACKING_PARAMS
        assert "source" in TRACKING_PARAMS
        assert "campaign" in TRACKING_PARAMS
        assert "si" in TRACKING_PARAMS
        assert "mc_cid" in TRACKING_PARAMS
        assert "mc_eid" in TRACKING_PARAMS
        assert "sref" in TRACKING_PARAMS
        assert "taid" in TRACKING_PARAMS
        assert "mod" in TRACKING_PARAMS
        assert "cmpid" in TRACKING_PARAMS

    def test_正常系_デフォルト類似度閾値(self) -> None:
        assert pytest.approx(0.85) == TITLE_SIMILARITY_THRESHOLD
