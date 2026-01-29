# P2-001: collectors/__init__.py 作成

## 概要

collectors パッケージの初期化ファイルを作成する。

## フェーズ

Phase 2: RSS収集

## 依存タスク

- P1-009: BaseCollector 抽象クラス作成

## 成果物

- `src/news/collectors/__init__.py`（新規作成）

## 実装内容

```python
"""記事収集モジュール

情報源別のコレクター実装を提供する。
"""

from news.collectors.base import BaseCollector

__all__ = ["BaseCollector"]
```

## 受け入れ条件

- [ ] `src/news/collectors/__init__.py` が作成されている
- [ ] BaseCollector がエクスポートされている
- [ ] pyright 型チェック成功
