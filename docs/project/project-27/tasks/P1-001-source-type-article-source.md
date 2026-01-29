# P1-001: SourceType, ArticleSource モデル作成

## 概要

情報源を抽象化するための基本モデルを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

なし（開始可能）

## 成果物

- `src/news/models.py`（新規作成、部分実装）

## 実装内容

```python
from enum import StrEnum
from pydantic import BaseModel

class SourceType(StrEnum):
    """情報源タイプ"""
    RSS = "rss"
    YFINANCE = "yfinance"
    SCRAPE = "scrape"

class ArticleSource(BaseModel):
    """記事の情報源メタデータ"""
    source_type: SourceType
    source_name: str       # "CNBC Markets", "NVDA" 等
    category: str          # "market", "yf_ai_stock" 等（マッピング用）
    feed_id: str | None = None  # RSSの場合のフィードID
```

## 受け入れ条件

- [ ] `SourceType` StrEnum が定義されている（RSS, YFINANCE, SCRAPE）
- [ ] `ArticleSource` Pydantic モデルが定義されている
- [ ] フィールド: source_type, source_name, category, feed_id
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: データモデル（パイプライン型）セクション
