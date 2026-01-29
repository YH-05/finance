# P2-003: RSSCollector category フィールド対応

## 概要

rss-presets.json の category フィールドを ArticleSource.category にマッピングする。

## フェーズ

Phase 2: RSS収集

## 依存タスク

- P2-002: RSSCollector 基本実装

## 成果物

- `src/news/collectors/rss.py`（更新）

## 実装内容

rss-presets.json の構造：
```json
{
  "feeds": [
    {
      "id": "cnbc-markets",
      "name": "CNBC Markets",
      "url": "https://...",
      "category": "market"  // ← このフィールドを読み取る
    }
  ]
}
```

ArticleSource への設定：
```python
source = ArticleSource(
    source_type=SourceType.RSS,
    source_name=feed["name"],
    category=feed.get("category", "other"),  # デフォルト: "other"
    feed_id=feed["id"]
)
```

## 受け入れ条件

- [ ] rss-presets.json の各フィードの category を読み取る
- [ ] ArticleSource.category に正しく設定される
- [ ] category が未指定の場合は "other" がデフォルト値として設定される
- [ ] pyright 型チェック成功

## 参照

- `data/config/rss-presets.json`: RSSフィード設定（category フィールド）
- project.md: 設定ファイル - status_mapping セクション
