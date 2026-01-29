# P2-004: RSSCollector 日時フィルタリング実装

## 概要

max_age_hours パラメータに基づいて古い記事をフィルタリングする。

## フェーズ

Phase 2: RSS収集

## 依存タスク

- P2-002: RSSCollector 基本実装

## 成果物

- `src/news/collectors/rss.py`（更新）

## 実装内容

```python
from datetime import datetime, timedelta, timezone

async def collect(
    self,
    max_age_hours: int = 168,
) -> list[CollectedArticle]:
    articles = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    for feed in feeds:
        for item in feed.items:
            # published が None の場合は含める（収集時刻を使用）
            if item.published is None:
                published = None
            elif item.published < cutoff_time:
                continue  # 古い記事はスキップ
            else:
                published = item.published

            articles.append(CollectedArticle(
                url=item.link,
                title=item.title,
                published=published,
                raw_summary=item.summary,
                source=source,
                collected_at=datetime.now(timezone.utc)
            ))

    return articles
```

## 受け入れ条件

- [ ] `collect(max_age_hours=168)` で 7 日以内の記事のみ取得
- [ ] published が None の記事は含める（スキップしない）
- [ ] タイムゾーン処理が正しい（UTC で比較）
- [ ] pyright 型チェック成功

## 参照

- project.md: 設定ファイル - filtering.max_age_hours
