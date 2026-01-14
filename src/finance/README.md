# finance

共通インフラパッケージ（データベース・ユーティリティ）

## 概要

financeパッケージは、プロジェクト全体で使用される共通インフラストラクチャを提供します。

**主な機能:**
- SQLiteクライアント（OLTP: トランザクション処理）
- DuckDBクライアント（OLAP: 分析クエリ）
- 構造化ロギング

**現在のバージョン:** 0.1.0

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->
```
finance/
├── __init__.py
├── py.typed
├── types.py
├── db/
│   ├── __init__.py
│   ├── connection.py
│   ├── duckdb_client.py
│   ├── sqlite_client.py
│   └── migrations/
│       ├── __init__.py
│       ├── runner.py
│       └── versions/
│           └── 20250111_000000_initial_schema.sql
└── utils/
    ├── __init__.py
    └── logging_config.py
```
<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|-----------|-----|
| `types.py` | ✅ 実装済み | 1 | 30 |
| `db/` | ✅ 実装済み | 6 | 342 |
| `utils/` | ✅ 実装済み | 2 | 273 |

<!-- END: IMPLEMENTATION -->

## 公開API

<!-- AUTO-GENERATED: API -->

### 関数

```python
from finance import (
    get_logger,
)
```

<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目 | 値 |
|-----|---|
| Pythonファイル数 | 10 |
| 総行数（実装コード） | 649 |
| モジュール数 | 2 |
| テストファイル数 | 3 |

<!-- END: STATS -->

## 使用例

```python
from finance import get_logger

logger = get_logger(__name__)
logger.info("Processing started", item_count=100)
```

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
