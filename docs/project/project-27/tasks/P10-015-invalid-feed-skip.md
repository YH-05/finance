# P10-015: 無効フィードスキップとログ

## 概要

無効なフィードを安全にスキップし、他のフィードの処理を継続する。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/collectors/rss.py` | 無効フィードスキップ処理 |
| `src/news/models.py` | `FeedError` モデル追加 |

### 実装詳細

```python
# src/news/models.py

class FeedError(BaseModel):
    """フィードエラー情報。"""

    feed_url: str
    feed_name: str
    error: str
    error_type: str  # "validation", "fetch", "parse"
    timestamp: datetime


# src/news/collectors/rss.py

class RSSCollector(BaseCollector):
    """RSSフィードからの記事収集。"""

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._feed_errors: list[FeedError] = []

    @property
    def feed_errors(self) -> list[FeedError]:
        """収集中に発生したフィードエラー。"""
        return self._feed_errors.copy()

    async def collect(
        self,
        max_age_hours: int = 168,
    ) -> list[CollectedArticle]:
        """RSSフィードから記事を収集。

        無効なフィードはスキップし、他のフィードの処理を継続する。
        """
        self._feed_errors.clear()
        all_articles: list[CollectedArticle] = []

        for feed in self._feeds:
            try:
                articles = await self._collect_from_feed(feed, max_age_hours)
                all_articles.extend(articles)

            except FeedValidationError as e:
                self._record_feed_error(feed, e, "validation")
                continue  # 次のフィードへ

            except FeedFetchError as e:
                self._record_feed_error(feed, e, "fetch")
                continue

            except FeedParseError as e:
                self._record_feed_error(feed, e, "parse")
                continue

        # サマリーログ
        if self._feed_errors:
            logger.warning(
                "Some feeds failed during collection",
                total_feeds=len(self._feeds),
                failed_feeds=len(self._feed_errors),
                error_types=self._count_error_types(),
            )

        logger.info(
            "RSS collection completed",
            total_articles=len(all_articles),
            successful_feeds=len(self._feeds) - len(self._feed_errors),
            failed_feeds=len(self._feed_errors),
        )

        return all_articles

    def _record_feed_error(
        self,
        feed: FeedConfig,
        error: Exception,
        error_type: str,
    ) -> None:
        """フィードエラーを記録。"""
        feed_error = FeedError(
            feed_url=feed.url,
            feed_name=feed.name,
            error=str(error),
            error_type=error_type,
            timestamp=datetime.now(timezone.utc),
        )
        self._feed_errors.append(feed_error)

        logger.error(
            "Feed collection failed, skipping",
            feed_url=feed.url,
            feed_name=feed.name,
            error_type=error_type,
            error=str(error),
        )

    def _count_error_types(self) -> dict[str, int]:
        """エラータイプ別の件数を集計。"""
        counts: dict[str, int] = {}
        for error in self._feed_errors:
            counts[error.error_type] = counts.get(error.error_type, 0) + 1
        return counts
```

### WorkflowResultへの統合

```python
# src/news/models.py

class WorkflowResult(BaseModel):
    """ワークフロー実行結果。"""

    # 既存フィールド
    total_collected: int
    total_extracted: int
    # ...

    # 追加
    feed_errors: list[FeedError] = Field(default_factory=list)
```

## 受け入れ条件

- [ ] 無効フィードがスキップされ、他のフィード処理が継続する
- [ ] エラー情報が `feed_errors` に記録される
- [ ] サマリーログにエラー件数が出力される
- [ ] WorkflowResultにフィードエラーが含まれる
- [ ] 単体テストが通る

## テストケース

```python
class TestInvalidFeedSkip:
    @pytest.mark.asyncio
    async def test_invalid_feed_is_skipped(self, collector, mocker):
        """無効フィードがスキップされる。"""
        mocker.patch.object(
            collector, "_collect_from_feed",
            side_effect=[
                FeedValidationError("Invalid format"),
                [CollectedArticle(...)],  # 2つ目は成功
            ]
        )

        articles = await collector.collect()

        assert len(articles) == 1  # 1つは成功
        assert len(collector.feed_errors) == 1  # 1つは失敗

    @pytest.mark.asyncio
    async def test_all_feeds_fail_returns_empty(self, collector, mocker):
        """全フィード失敗時は空リストを返す。"""
        mocker.patch.object(
            collector, "_collect_from_feed",
            side_effect=FeedFetchError("Network error")
        )

        articles = await collector.collect()

        assert len(articles) == 0
        assert len(collector.feed_errors) > 0
```

## 依存関係

- 依存先: P10-014
- ブロック: P10-016

## 見積もり

- 作業時間: 30分
- 複雑度: 中
