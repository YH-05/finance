"""Unit tests for FeedParser."""

import uuid

import pytest

from rss.core.parser import FeedParser
from rss.exceptions import FeedParseError
from rss.types import FeedItem

# Sample RSS 2.0 feed
RSS_SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample RSS Feed</title>
    <link>https://example.com</link>
    <description>This is a sample RSS feed</description>
    <item>
      <title>First Article</title>
      <link>https://example.com/article1</link>
      <pubDate>Mon, 14 Jan 2026 10:00:00 GMT</pubDate>
      <description>This is the first article summary.</description>
      <author>author@example.com</author>
    </item>
    <item>
      <title>Second Article</title>
      <link>https://example.com/article2</link>
      <pubDate>Mon, 14 Jan 2026 11:00:00 GMT</pubDate>
      <description>This is the second article summary.</description>
    </item>
  </channel>
</rss>
"""

# Sample Atom feed
ATOM_SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Sample Atom Feed</title>
  <link href="https://example.com"/>
  <id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</id>
  <updated>2026-01-14T12:00:00Z</updated>
  <entry>
    <title>Atom Entry 1</title>
    <link href="https://example.com/atom1"/>
    <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
    <updated>2026-01-14T10:00:00Z</updated>
    <summary>Atom entry summary</summary>
    <content type="html">&lt;p&gt;Atom entry content&lt;/p&gt;</content>
    <author>
      <name>John Doe</name>
    </author>
  </entry>
  <entry>
    <title>Atom Entry 2</title>
    <link href="https://example.com/atom2"/>
    <id>urn:uuid:1225c695-cfb8-4ebb-bbbb-80da344efa6a</id>
    <published>2026-01-14T11:00:00Z</published>
    <summary>Second Atom entry</summary>
  </entry>
</feed>
"""

# Minimal RSS feed (without optional fields)
MINIMAL_RSS_SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Minimal Feed</title>
    <link>https://example.com</link>
    <item>
      <title>Minimal Item</title>
      <link>https://example.com/minimal</link>
    </item>
  </channel>
</rss>
"""

# Invalid XML
INVALID_XML = b"""<not valid xml"""

# HTML (not a feed)
HTML_CONTENT = b"""<!DOCTYPE html>
<html>
<head><title>Not a Feed</title></head>
<body><p>This is HTML, not RSS or Atom</p></body>
</html>
"""


def is_valid_uuid4(value: str) -> bool:
    """Check if a string is a valid UUID v4."""
    try:
        parsed = uuid.UUID(value, version=4)
        return str(parsed) == value
    except ValueError:
        return False


class TestFeedParserInit:
    """Test FeedParser initialization."""

    def test_init(self) -> None:
        """Test initialization."""
        parser = FeedParser()
        assert parser is not None


class TestParseRSS:
    """Test parsing RSS 2.0 feeds."""

    def test_parse_rss_feed(self) -> None:
        """Test parsing a valid RSS 2.0 feed."""
        parser = FeedParser()
        items = parser.parse(RSS_SAMPLE)

        assert len(items) == 2

        # Check first item
        item1 = items[0]
        assert item1.title == "First Article"
        assert item1.link == "https://example.com/article1"
        assert item1.summary == "This is the first article summary."
        assert item1.author == "author@example.com"
        assert item1.published is not None
        assert is_valid_uuid4(item1.item_id)
        assert item1.fetched_at is not None

        # Check second item
        item2 = items[1]
        assert item2.title == "Second Article"
        assert item2.link == "https://example.com/article2"
        assert item2.author is None  # No author in second item

    def test_parse_rss_returns_feeditem_type(self) -> None:
        """Test that parse returns FeedItem instances."""
        parser = FeedParser()
        items = parser.parse(RSS_SAMPLE)

        for item in items:
            assert isinstance(item, FeedItem)


class TestParseAtom:
    """Test parsing Atom feeds."""

    def test_parse_atom_feed(self) -> None:
        """Test parsing a valid Atom feed."""
        parser = FeedParser()
        items = parser.parse(ATOM_SAMPLE)

        assert len(items) == 2

        # Check first item
        item1 = items[0]
        assert item1.title == "Atom Entry 1"
        assert item1.link == "https://example.com/atom1"
        assert item1.summary == "Atom entry summary"
        assert item1.content == "<p>Atom entry content</p>"
        assert item1.author == "John Doe"
        assert item1.published is not None
        assert is_valid_uuid4(item1.item_id)

        # Check second item
        item2 = items[1]
        assert item2.title == "Atom Entry 2"
        assert item2.author is None  # No author in second entry


class TestParseOptionalFields:
    """Test handling of optional fields."""

    def test_parse_minimal_feed(self) -> None:
        """Test parsing a feed with minimal fields."""
        parser = FeedParser()
        items = parser.parse(MINIMAL_RSS_SAMPLE)

        assert len(items) == 1

        item = items[0]
        assert item.title == "Minimal Item"
        assert item.link == "https://example.com/minimal"
        # Optional fields should be None
        assert item.published is None
        assert item.summary is None
        assert item.content is None
        assert item.author is None

    def test_published_none_when_not_provided(self) -> None:
        """Test that published is None when not provided."""
        parser = FeedParser()
        items = parser.parse(MINIMAL_RSS_SAMPLE)

        assert items[0].published is None

    def test_summary_none_when_not_provided(self) -> None:
        """Test that summary is None when not provided."""
        parser = FeedParser()
        items = parser.parse(MINIMAL_RSS_SAMPLE)

        assert items[0].summary is None

    def test_content_none_when_not_provided(self) -> None:
        """Test that content is None when not provided."""
        parser = FeedParser()
        items = parser.parse(MINIMAL_RSS_SAMPLE)

        assert items[0].content is None

    def test_author_none_when_not_provided(self) -> None:
        """Test that author is None when not provided."""
        parser = FeedParser()
        items = parser.parse(MINIMAL_RSS_SAMPLE)

        assert items[0].author is None


class TestItemIdGeneration:
    """Test UUID v4 item_id generation."""

    def test_item_id_is_uuid4(self) -> None:
        """Test that item_id is a valid UUID v4."""
        parser = FeedParser()
        items = parser.parse(RSS_SAMPLE)

        for item in items:
            assert is_valid_uuid4(item.item_id)

    def test_item_ids_are_unique(self) -> None:
        """Test that each item gets a unique item_id."""
        parser = FeedParser()
        items = parser.parse(RSS_SAMPLE)

        item_ids = [item.item_id for item in items]
        assert len(item_ids) == len(set(item_ids))


class TestParseErrors:
    """Test error handling."""

    def test_parse_invalid_xml_raises_error(self) -> None:
        """Test that invalid XML raises FeedParseError."""
        parser = FeedParser()

        with pytest.raises(FeedParseError):
            parser.parse(INVALID_XML)

    def test_parse_html_raises_error(self) -> None:
        """Test that HTML content raises FeedParseError."""
        parser = FeedParser()

        with pytest.raises(FeedParseError):
            parser.parse(HTML_CONTENT)

    def test_parse_empty_content_raises_error(self) -> None:
        """Test that empty content raises FeedParseError."""
        parser = FeedParser()

        with pytest.raises(FeedParseError):
            parser.parse(b"")

    def test_parse_random_bytes_raises_error(self) -> None:
        """Test that random bytes raise FeedParseError."""
        parser = FeedParser()

        with pytest.raises(FeedParseError):
            parser.parse(b"\x00\x01\x02\x03\x04\x05")


class TestParseLogging:
    """Test logging behavior of parse method.

    Note: Logging tests verify that the method executes without errors.
    structlog logging behavior depends on global configuration which can
    vary based on test execution order. These tests verify correct execution
    rather than specific log output.
    """

    def test_parse_executes_with_logging(self) -> None:
        """Test that parse executes with logging enabled."""
        parser = FeedParser()

        # Execute method - should not raise any exceptions
        # Logging is enabled internally, this verifies no errors occur
        items = parser.parse(RSS_SAMPLE)

        # Verify the method executed correctly
        assert len(items) == 2


# Sample contents for validation testing
PLAIN_TEXT_CONTENT = b"This is plain text, not XML or RSS/Atom feed."
JSON_CONTENT = b'{"data": "This is JSON content"}'
HTML_WITHOUT_FEED = b"""<!DOCTYPE html>
<html>
<head><title>Not a Feed</title></head>
<body><p>This is just HTML, no RSS or Atom elements</p></body>
</html>
"""

# XML that looks valid but has no RSS/Atom elements
XML_NO_FEED_ELEMENTS = b"""<?xml version="1.0" encoding="UTF-8"?>
<document>
    <title>Just XML</title>
    <content>This XML has no RSS or Atom elements</content>
</document>
"""


class TestFeedContentValidation:
    """Test _validate_feed_content method (P10-014).

    These tests verify the enhanced feed format validation logic
    that detects invalid feeds early with detailed error messages.
    """

    def test_正常系_有効なRSSフィードはvalid(self) -> None:
        """有効なRSS 2.0フィードは検証をパスする。"""
        parser = FeedParser()
        result = parser._validate_feed_content(RSS_SAMPLE)

        assert result.is_valid is True
        assert result.error is None

    def test_正常系_有効なAtomフィードはvalid(self) -> None:
        """有効なAtomフィードは検証をパスする。"""
        parser = FeedParser()
        result = parser._validate_feed_content(ATOM_SAMPLE)

        assert result.is_valid is True
        assert result.error is None

    def test_異常系_空コンテンツでinvalid(self) -> None:
        """空のコンテンツは無効として検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(b"")

        assert result.is_valid is False
        assert result.error is not None
        assert "Empty" in result.error or "empty" in result.error.lower()

    def test_異常系_空白のみコンテンツでinvalid(self) -> None:
        """空白のみのコンテンツも無効として検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(b"   \n\t  ")

        assert result.is_valid is False
        assert result.error is not None
        assert "Empty" in result.error or "empty" in result.error.lower()

    def test_異常系_プレーンテキストでinvalid(self) -> None:
        """プレーンテキストは非XMLコンテンツとして検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(PLAIN_TEXT_CONTENT)

        assert result.is_valid is False
        assert result.error is not None
        assert "XML" in result.error

    def test_異常系_JSONコンテンツでinvalid(self) -> None:
        """JSONコンテンツは非XMLとして検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(JSON_CONTENT)

        assert result.is_valid is False
        assert result.error is not None
        assert "XML" in result.error

    def test_異常系_RSS要素のないHTMLでinvalid(self) -> None:
        """RSS/Atom要素のないHTMLは無効として検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(HTML_WITHOUT_FEED)

        assert result.is_valid is False
        assert result.error is not None
        assert "RSS" in result.error or "Atom" in result.error

    def test_異常系_RSS要素のないXMLでinvalid(self) -> None:
        """RSS/Atom要素のないXMLは無効として検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(XML_NO_FEED_ELEMENTS)

        assert result.is_valid is False
        assert result.error is not None
        assert "RSS" in result.error or "Atom" in result.error


class TestFeedContentValidationWithContentType:
    """Test _validate_feed_content with optional content_type parameter."""

    def test_異常系_JSONのContentTypeでinvalid(self) -> None:
        """application/json Content-Typeは無効として検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(
            RSS_SAMPLE,
            content_type="application/json",
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "Content-Type" in result.error

    def test_正常系_XMLのContentTypeでvalid(self) -> None:
        """application/xml Content-Typeは有効。"""
        parser = FeedParser()
        result = parser._validate_feed_content(
            RSS_SAMPLE,
            content_type="application/xml",
        )

        assert result.is_valid is True

    def test_正常系_RSSのContentTypeでvalid(self) -> None:
        """application/rss+xml Content-Typeは有効。"""
        parser = FeedParser()
        result = parser._validate_feed_content(
            RSS_SAMPLE,
            content_type="application/rss+xml",
        )

        assert result.is_valid is True

    def test_正常系_AtomのContentTypeでvalid(self) -> None:
        """application/atom+xml Content-Typeは有効。"""
        parser = FeedParser()
        result = parser._validate_feed_content(
            ATOM_SAMPLE,
            content_type="application/atom+xml",
        )

        assert result.is_valid is True

    def test_正常系_TextXMLのContentTypeでvalid(self) -> None:
        """text/xml Content-Typeは有効。"""
        parser = FeedParser()
        result = parser._validate_feed_content(
            RSS_SAMPLE,
            content_type="text/xml",
        )

        assert result.is_valid is True

    def test_正常系_TextHTMLでRSS要素ありならvalid(self) -> None:
        """text/html Content-Typeでもフィード要素があれば有効。"""
        parser = FeedParser()
        result = parser._validate_feed_content(
            RSS_SAMPLE,
            content_type="text/html",
        )

        assert result.is_valid is True

    def test_正常系_ContentType未指定でvalid(self) -> None:
        """Content-Type未指定の場合はコンテンツのみで判定。"""
        parser = FeedParser()
        result = parser._validate_feed_content(RSS_SAMPLE)

        assert result.is_valid is True

    def test_異常系_画像のContentTypeでinvalid(self) -> None:
        """image/png Content-Typeは無効として検出される。"""
        parser = FeedParser()
        result = parser._validate_feed_content(
            RSS_SAMPLE,
            content_type="image/png",
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "Content-Type" in result.error


class TestFeedValidationResultType:
    """Test FeedValidationResult type structure."""

    def test_FeedValidationResult型が存在する(self) -> None:
        """FeedValidationResult型がrss.typesからインポートできる。"""
        from rss.types import FeedValidationResult

        # 型が存在することを確認
        assert FeedValidationResult is not None

    def test_FeedValidationResultにis_validフィールドがある(self) -> None:
        """FeedValidationResultにはis_validフィールドがある。"""
        from rss.types import FeedValidationResult

        result = FeedValidationResult(is_valid=True, error=None)
        assert hasattr(result, "is_valid")
        assert result.is_valid is True

    def test_FeedValidationResultにerrorフィールドがある(self) -> None:
        """FeedValidationResultにはerrorフィールドがある。"""
        from rss.types import FeedValidationResult

        result = FeedValidationResult(is_valid=False, error="Test error")
        assert hasattr(result, "error")
        assert result.error == "Test error"
