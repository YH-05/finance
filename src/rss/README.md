# rss

RSS/Atomフィード管理パッケージ

## 概要

このパッケージは、RSS/Atomフィードの取得、パース、管理機能を提供します。

**主な機能:**
- フィード取得・パース
- エントリー管理
- 更新監視

**現在のバージョン:** 0.1.0

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->
```
rss/
├── __init__.py
├── py.typed
├── types.py
├── core/
│   └── __init__.py
└── utils/
    ├── __init__.py
    └── logging_config.py
```
<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|-----------|-----|
| `types.py` | ✅ 実装済み | 1 | 106 |
| `core/` | ⏳ 未実装 | 1 | 3 |
| `utils/` | ✅ 実装済み | 2 | 367 |

<!-- END: IMPLEMENTATION -->

## 公開API

<!-- AUTO-GENERATED: API -->

### 関数

```python
from rss import (
    get_logger,
)
```

<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目 | 値 |
|-----|---|
| Pythonファイル数 | 5 |
| 総行数（実装コード） | 349 |
| モジュール数 | 3 |
| テストファイル数 | 5 |
| テストカバレッジ | N/A |

<!-- END: STATS -->

## 使用例

```python
from rss import get_logger

logger = get_logger(__name__)
# 実装が進むと、ここに具体的な使用例が追加されます
```

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

-   `template/src/template_package/README.md` - テンプレート実装の詳細
-   `docs/development-guidelines.md` - 開発ガイドライン
