# P1-006: FailureRecord, WorkflowResult モデル作成

## 概要

ワークフロー実行結果を表すモデルを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-005: PublicationStatus, PublishedArticle モデル作成

## 成果物

- `src/news/models.py`（追記）

## 実装内容

```python
from datetime import datetime
from pydantic import BaseModel

class FailureRecord(BaseModel):
    """失敗記録"""
    url: str
    title: str
    stage: str  # "extraction", "summarization", "publication"
    error: str

class WorkflowResult(BaseModel):
    """ワークフロー実行結果"""
    # 件数
    total_collected: int
    total_extracted: int
    total_summarized: int
    total_published: int
    total_duplicates: int

    # エラー詳細
    extraction_failures: list[FailureRecord]
    summarization_failures: list[FailureRecord]
    publication_failures: list[FailureRecord]

    # 処理時間
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float

    # 成功した記事
    published_articles: list[PublishedArticle]
```

## 受け入れ条件

- [ ] `FailureRecord` Pydantic モデルが定義されている
- [ ] フィールド: url, title, stage, error
- [ ] `WorkflowResult` Pydantic モデルが定義されている
- [ ] 件数フィールド: total_collected, total_extracted, total_summarized, total_published, total_duplicates
- [ ] エラー詳細: extraction_failures, summarization_failures, publication_failures
- [ ] 処理時間: started_at, finished_at, elapsed_seconds
- [ ] published_articles: list[PublishedArticle]
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: WorkflowResult（実行結果）セクション
