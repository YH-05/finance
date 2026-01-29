# P1-004: StructuredSummary, SummarizedArticle モデル作成

## 概要

AI 要約結果を表すモデルを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-003: ExtractionStatus, ExtractedArticle モデル作成

## 成果物

- `src/news/models.py`（追記）

## 実装内容

```python
from enum import StrEnum
from pydantic import BaseModel

class StructuredSummary(BaseModel):
    """4セクション構造化要約"""
    overview: str           # 概要: 記事の主旨
    key_points: list[str]   # キーポイント: 重要事実
    market_impact: str      # 市場影響: 投資家への示唆
    related_info: str | None = None  # 関連情報: 背景

class SummarizationStatus(StrEnum):
    """要約ステータス"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"  # 本文抽出失敗時

class SummarizedArticle(BaseModel):
    """Summarizerから出力される記事"""
    extracted: ExtractedArticle
    summary: StructuredSummary | None
    summarization_status: SummarizationStatus
    error_message: str | None = None
```

## 受け入れ条件

- [ ] `StructuredSummary` Pydantic モデルが定義されている
- [ ] フィールド: overview, key_points (list[str]), market_impact, related_info
- [ ] `SummarizationStatus` StrEnum が定義されている（SUCCESS, FAILED, TIMEOUT, SKIPPED）
- [ ] `SummarizedArticle` Pydantic モデルが定義されている
- [ ] ExtractedArticle との関連が正しく設定されている
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: SummarizedArticle（AI要約後）セクション
