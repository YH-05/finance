# P10-007: RSSCollectorにドメインフィルタリング

## 概要

RSSCollectorの収集処理でブロックドメインの記事をフィルタリングする。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/collectors/rss.py` | ドメインフィルタリング追加 |

### 実装詳細

```python
# src/news/collectors/rss.py

class RSSCollector(BaseCollector):
    """RSSフィードからの記事収集。"""

    def __init__(
        self,
        config: NewsWorkflowConfig,
    ) -> None:
        self._config = config
        self._domain_filter = config.domain_filtering
        # ...

    async def collect(
        self,
        max_age_hours: int = 168,
    ) -> list[CollectedArticle]:
        """RSSフィードから記事を収集。"""
        all_articles = await self._fetch_all_feeds(max_age_hours)

        # ドメインフィルタリング
        filtered_articles = self._filter_blocked_domains(all_articles)

        return filtered_articles

    def _filter_blocked_domains(
        self,
        articles: list[CollectedArticle],
    ) -> list[CollectedArticle]:
        """ブロックドメインの記事を除外。

        Parameters
        ----------
        articles : list[CollectedArticle]
            フィルタリング前の記事リスト。

        Returns
        -------
        list[CollectedArticle]
            フィルタリング後の記事リスト。
        """
        if not self._domain_filter.enabled:
            return articles

        filtered = []
        blocked_count = 0

        for article in articles:
            url = str(article.url)
            if self._domain_filter.is_blocked(url):
                blocked_count += 1
                if self._domain_filter.log_blocked:
                    logger.debug(
                        "Blocked domain article skipped",
                        url=url,
                        title=article.title[:50],
                    )
            else:
                filtered.append(article)

        if blocked_count > 0:
            logger.info(
                "Filtered blocked domain articles",
                blocked_count=blocked_count,
                remaining_count=len(filtered),
            )

        return filtered
```

## 受け入れ条件

- [ ] ブロックドメインの記事が収集結果から除外される
- [ ] 除外数がログに出力される
- [ ] `log_blocked=True` 時に個別の除外ログが出力される
- [ ] フィルタリング無効時は全て収集される
- [ ] 単体テストが通る

## テストケース

```python
class TestRSSCollectorDomainFilter:
    def test_blocks_configured_domains(self, collector):
        """設定されたドメインがブロックされる。"""
        articles = [
            CollectedArticle(url="https://seekingalpha.com/article/1", ...),
            CollectedArticle(url="https://cnbc.com/article/2", ...),
        ]

        filtered = collector._filter_blocked_domains(articles)

        assert len(filtered) == 1
        assert "cnbc.com" in str(filtered[0].url)

    def test_disabled_filtering_allows_all(self, collector_disabled):
        """無効時は全て通過する。"""
        articles = [
            CollectedArticle(url="https://seekingalpha.com/article/1", ...),
        ]

        filtered = collector_disabled._filter_blocked_domains(articles)

        assert len(filtered) == 1
```

## 依存関係

- 依存先: P10-006
- ブロック: P10-016

## 見積もり

- 作業時間: 20分
- 複雑度: 低
