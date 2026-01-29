# P1-005: PublicationStatus, PublishedArticle モデル作成

## 概要

Issue 公開結果を表すモデルを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-004: StructuredSummary, SummarizedArticle モデル作成

## 成果物

- `src/news/models.py`（追記）

## 実装内容

```python
from enum import StrEnum
from pydantic import BaseModel

class PublicationStatus(StrEnum):
    """公開ステータス"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"    # 要約失敗時
    DUPLICATE = "duplicate"  # 重複検出時

class PublishedArticle(BaseModel):
    """Publisherから出力される記事"""
    summarized: SummarizedArticle
    issue_number: int | None
    issue_url: str | None
    publication_status: PublicationStatus
    error_message: str | None = None
```

## 受け入れ条件

- [ ] `PublicationStatus` StrEnum が定義されている（SUCCESS, FAILED, SKIPPED, DUPLICATE）
- [ ] `PublishedArticle` Pydantic モデルが定義されている
- [ ] フィールド: summarized, issue_number, issue_url, publication_status, error_message
- [ ] SummarizedArticle との関連が正しく設定されている
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: PublishedArticle（Issue作成後）セクション
