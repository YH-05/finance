# factor

ファクター投資・マルチファクターモデル分析パッケージ

## 概要

このパッケージはファクター投資戦略とマルチファクターモデルの分析機能を提供します。

**現在のバージョン:** 0.1.0

<!-- AUTO-GENERATED: QUICKSTART -->
## クイックスタート

### インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

### 基本的な使い方

```python
from factor.utils import get_logger

# ログ設定
logger = get_logger(__name__)

# ログ出力
logger.info("Processing started", item_count=100)
```

### よくある使い方

#### ログ記録（構造化ログ）

```python
from factor.utils import get_logger

logger = get_logger(__name__)

# イベント記録
logger.info("data_loaded", source="api", count=50)

# エラー記録
logger.error("request_failed", status_code=500, endpoint="/data")
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
factor/
├── __init__.py
├── py.typed
├── types.py
├── core/
│   └── __init__.py
├── utils/
│   ├── __init__.py
│   └── logging_config.py
└── docs/
    └── (documentation files)
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール | 状態        | ファイル数 | 行数 |
| ---------- | ----------- | ---------- | ---- |
| `types.py` | ✅ 実装済み | 1          | 106  |
| `core/`    | ⏳ 未実装   | 1          | 2    |
| `utils/`   | ✅ 実装済み | 2          | 377  |

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### 関数

#### `get_logger(name: str) -> BoundLogger`

**説明**: 構造化ログを出力するロガーを取得する関数

**基本的な使い方**:

```python
from factor.utils import get_logger

logger = get_logger(__name__)
logger.info("event_name", key="value")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `debug(event, **kwargs)` | デバッグレベルでログを記録 | `None` |
| `info(event, **kwargs)` | 情報レベルでログを記録 | `None` |
| `warning(event, **kwargs)` | 警告レベルでログを記録 | `None` |
| `error(event, **kwargs)` | エラーレベルでログを記録 | `None` |
| `critical(event, **kwargs)` | 重大レベルでログを記録 | `None` |
| `bind(**kwargs)` | コンテキスト情報をバインド | `BoundLogger` |

---

### 型定義

ファクター分析とデータ処理の型定義。型ヒントやバリデーションに使用:

```python
from factor.types import (
    ProcessorStatus,          # ステータス型: "success" | "error" | "pending"
    ValidationStatus,         # 検証ステータス型: "valid" | "invalid" | "skipped"
    ItemDict,                 # アイテムデータの辞書型
    ConfigDict,               # 設定データの辞書型
    ProcessingResult,         # 処理結果の構造化型
    ValidationResult,         # 検証結果の構造化型
    LogLevel,                 # ログレベル: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
)
```

<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値   |
| -------------------- | ---- |
| Python ファイル数    | 5    |
| 総行数（実装コード） | 485  |
| モジュール数         | 3    |
| テストファイル数     | 0    |
| テストカバレッジ     | N/A  |

<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
