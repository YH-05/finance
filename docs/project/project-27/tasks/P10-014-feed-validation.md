# P10-014: フィード形式検証強化

## 概要

RSSフィードの形式検証を強化し、無効なフィードを早期に検出する。

## 背景

2026-01-31のログで2件の「Invalid feed format」が発生。詳細なエラー情報が不足しており、原因特定が困難。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/rss/core/parser.py` | 検証ロジック強化、詳細ログ追加 |

### 実装詳細

```python
# src/rss/core/parser.py

class FeedParser:
    """RSSフィードパーサー。"""

    async def parse(self, feed_url: str) -> FeedParseResult:
        """フィードをパースする。

        Parameters
        ----------
        feed_url : str
            フィードURL。

        Returns
        -------
        FeedParseResult
            パース結果。
        """
        try:
            response = await self._fetch_feed(feed_url)

            # コンテンツ検証
            validation_result = self._validate_feed_content(
                content=response.text,
                url=feed_url,
                content_type=response.headers.get("content-type", ""),
            )

            if not validation_result.is_valid:
                logger.error(
                    "Invalid feed format",
                    url=feed_url,
                    content_type=response.headers.get("content-type"),
                    validation_error=validation_result.error,
                    content_preview=response.text[:200] if response.text else None,
                )
                return FeedParseResult(
                    url=feed_url,
                    entries=[],
                    error=validation_result.error,
                )

            # パース実行
            feed = feedparser.parse(response.text)

            # feedparserのエラーチェック
            if feed.bozo:
                logger.warning(
                    "Feed parsing warning",
                    url=feed_url,
                    bozo_exception=str(feed.bozo_exception),
                )

            # ...

        except Exception as e:
            logger.error(
                "Feed fetch failed",
                url=feed_url,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _validate_feed_content(
        self,
        content: str,
        url: str,
        content_type: str,
    ) -> FeedValidationResult:
        """フィードコンテンツを検証。

        Parameters
        ----------
        content : str
            フィードコンテンツ。
        url : str
            フィードURL。
        content_type : str
            Content-Typeヘッダー。

        Returns
        -------
        FeedValidationResult
            検証結果。
        """
        # 1. 空コンテンツチェック
        if not content or not content.strip():
            return FeedValidationResult(
                is_valid=False,
                error="Empty feed content",
            )

        # 2. Content-Typeチェック
        valid_content_types = [
            "application/rss+xml",
            "application/atom+xml",
            "application/xml",
            "text/xml",
            "text/html",  # 一部サイトはHTMLで返す
        ]

        content_type_lower = content_type.lower()
        if not any(ct in content_type_lower for ct in valid_content_types):
            return FeedValidationResult(
                is_valid=False,
                error=f"Invalid Content-Type: {content_type}",
            )

        # 3. XMLシグネチャチェック
        content_stripped = content.strip()
        if not content_stripped.startswith("<?xml") and not content_stripped.startswith("<"):
            return FeedValidationResult(
                is_valid=False,
                error="Content does not appear to be XML",
            )

        # 4. RSS/Atom要素チェック
        has_rss = "<rss" in content or "<channel>" in content
        has_atom = "<feed" in content and "xmlns" in content

        if not has_rss and not has_atom:
            return FeedValidationResult(
                is_valid=False,
                error="No RSS or Atom elements found",
            )

        return FeedValidationResult(is_valid=True, error=None)


@dataclass
class FeedValidationResult:
    """フィード検証結果。"""

    is_valid: bool
    error: str | None
```

## 受け入れ条件

- [ ] 空コンテンツが検出される
- [ ] 不正なContent-Typeが検出される
- [ ] 非XMLコンテンツが検出される
- [ ] RSS/Atom要素の欠落が検出される
- [ ] 詳細なエラーログが出力される（URL、Content-Type、プレビュー）
- [ ] 単体テストが通る

## テストケース

```python
class TestFeedValidation:
    def test_empty_content_is_invalid(self, parser):
        """空コンテンツは無効。"""
        result = parser._validate_feed_content("", "https://example.com", "text/xml")

        assert not result.is_valid
        assert "Empty" in result.error

    def test_json_content_type_is_invalid(self, parser):
        """JSONのContent-Typeは無効。"""
        result = parser._validate_feed_content(
            "<rss>...</rss>",
            "https://example.com",
            "application/json"
        )

        assert not result.is_valid
        assert "Content-Type" in result.error

    def test_html_without_feed_is_invalid(self, parser):
        """RSS要素のないHTMLは無効。"""
        result = parser._validate_feed_content(
            "<html><body>Not a feed</body></html>",
            "https://example.com",
            "text/html"
        )

        assert not result.is_valid
        assert "No RSS or Atom" in result.error
```

## 依存関係

- 依存先: P10-002
- ブロック: P10-015

## 見積もり

- 作業時間: 30分
- 複雑度: 中
