# P1-003: ExtractionStatus, ExtractedArticle モデル作成

## 概要

本文抽出結果を表すモデルを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-002: CollectedArticle モデル作成

## 成果物

- `src/news/models.py`（追記）

## 実装内容

```python
from enum import StrEnum
from pydantic import BaseModel

class ExtractionStatus(StrEnum):
    """本文抽出ステータス"""
    SUCCESS = "success"
    FAILED = "failed"
    PAYWALL = "paywall"
    TIMEOUT = "timeout"

class ExtractedArticle(BaseModel):
    """Extractorから出力される記事"""
    collected: CollectedArticle
    body_text: str | None
    extraction_status: ExtractionStatus
    extraction_method: str  # "trafilatura", "fallback" 等
    error_message: str | None = None
```

## 受け入れ条件

- [ ] `ExtractionStatus` StrEnum が定義されている（SUCCESS, FAILED, PAYWALL, TIMEOUT）
- [ ] `ExtractedArticle` Pydantic モデルが定義されている
- [ ] フィールド: collected, body_text, extraction_status, extraction_method, error_message
- [ ] CollectedArticle との関連が正しく設定されている
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: ExtractedArticle（本文抽出後）セクション
