# P3-001: extractors/__init__.py 作成

## 概要

extractors パッケージの初期化ファイルを作成する。

## フェーズ

Phase 3: 本文抽出

## 依存タスク

- P1-010: BaseExtractor 抽象クラス作成

## 成果物

- `src/news/extractors/__init__.py`（新規作成）

## 実装内容

```python
"""本文抽出モジュール

記事URLから本文を抽出するエクストラクター実装を提供する。
"""

from news.extractors.base import BaseExtractor

__all__ = ["BaseExtractor"]
```

## 受け入れ条件

- [ ] `src/news/extractors/__init__.py` が作成されている
- [ ] BaseExtractor がエクスポートされている
- [ ] pyright 型チェック成功
