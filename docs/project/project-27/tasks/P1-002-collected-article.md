# P1-002: CollectedArticle モデル作成

## 概要

Collector から出力される記事モデルを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-001: SourceType, ArticleSource モデル作成

## 成果物

- `src/news/models.py`（追記）

## 実装内容

```python
from datetime import datetime
from pydantic import BaseModel, HttpUrl

class CollectedArticle(BaseModel):
    """Collectorから出力される記事"""
    url: HttpUrl
    title: str
    published: datetime | None
    raw_summary: str | None  # 情報源の要約（RSSのsummary等）
    source: ArticleSource
    collected_at: datetime
```

## 受け入れ条件

- [ ] `CollectedArticle` Pydantic モデルが定義されている
- [ ] フィールド: url (HttpUrl), title, published, raw_summary, source, collected_at
- [ ] ArticleSource との関連が正しく設定されている
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: CollectedArticle（収集直後）セクション
