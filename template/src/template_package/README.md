# template_package

Python開発テンプレートのリファレンス実装パッケージ。新規プロジェクト作成時のベースとなる構造・パターン・ベストプラクティスを提供します。

## 概要

このパッケージは、Pythonプロジェクトの標準的な構造とコーディングパターンを示すテンプレートです。実装時は`src/project_name/`にコピーして使用します。

**主な特徴:**

- PEP 695準拠の型定義
- structlogによる構造化ロギング
- パフォーマンス計測ツール
- NumPy形式のDocstring

## ディレクトリ構成

```
template_package/
├── __init__.py          # 公開API定義
├── py.typed             # PEP 561マーカー（型チェック対象）
├── types.py             # 型定義の集約
├── core/                # コアビジネスロジック
│   ├── __init__.py
│   └── example.py       # 実装例（ExampleClass, process_data）
└── utils/               # ユーティリティ関数
    ├── __init__.py
    ├── helpers.py       # 汎用ヘルパー関数
    ├── logging_config.py # 構造化ロギング設定
    └── profiling.py     # パフォーマンス計測ツール
```

## モジュール詳細

### types.py

プロジェクト全体で使用する型定義を集約。

| 型 | 用途 |
|---|------|
| `ItemDict` | アイテムデータのTypedDict |
| `ConfigDict` | 設定データのTypedDict |
| `ProcessorStatus` | 処理状態のLiteral型 |
| `JSONValue` | JSON互換値の再帰的型 |
| `LogEvent` | ログイベントのTypedDict |

### core/example.py

ビジネスロジックの実装パターンを示すサンプル。

| クラス/関数 | 役割 |
|------------|------|
| `ExampleClass` | データ管理クラス（追加・取得・クリア） |
| `ExampleConfig` | 設定用dataclass |
| `DataProcessor` | 処理インターフェース（Protocol） |
| `process_data()` | データ処理関数の実装例 |

### utils/helpers.py

汎用ユーティリティ関数。

| 関数 | 機能 |
|-----|------|
| `load_json()` | JSONファイル読み込み |
| `save_json()` | JSONファイル書き込み |
| `chunk_list()` | リスト分割（ジェネリック型） |
| `flatten_dict()` | ネストした辞書をフラット化 |

### utils/logging_config.py

structlogを使用した構造化ロギング。

| 関数/変数 | 機能 |
|----------|------|
| `get_logger()` | ロガー取得（モジュール名自動付与） |
| `configure_logging()` | ロギング設定（JSON/コンソール切替） |

### utils/profiling.py

パフォーマンス計測ツール。

| デコレータ/関数 | 機能 |
|---------------|------|
| `@profile` | 詳細プロファイリング（cProfile使用） |
| `@timeit` | 実行時間計測 |
| `profile_context()` | コンテキストマネージャ形式の計測 |
| `Timer` | 手動タイマークラス |

## 公開API

`__init__.py`で定義された公開API:

```python
from template_package import (
    ExampleClass,
    ExampleConfig,
    process_data,
    get_logger,
)
```

## 使用例

### 基本的な使用

```python
from template_package import ExampleClass, get_logger

logger = get_logger(__name__)

# クラスの使用
example = ExampleClass(max_items=100)
example.add_item({"id": 1, "name": "test", "value": 42})
items = example.get_items()

logger.info("処理完了", item_count=len(items))
```

### パフォーマンス計測

```python
from template_package.utils.profiling import profile, timeit

@timeit
def my_function():
    # 実行時間が計測される
    ...

@profile
def heavy_computation():
    # 詳細なプロファイル情報が出力される
    ...
```

## 設計意図

### レイヤー構造

```
types.py      → 型定義（他モジュールから参照される）
core/         → ビジネスロジック（types.pyとutils/に依存）
utils/        → 共通ユーティリティ（types.pyに依存）
```

### 拡張ポイント

1. **新しいコアモジュール追加**: `core/`に新規ファイル作成
2. **型定義追加**: `types.py`に追加
3. **ユーティリティ追加**: `utils/`に新規ファイルまたは既存ファイルに追加
4. **公開API追加**: `__init__.py`の`__all__`に追加

### ロギング設計

循環インポートを避けるため、遅延初期化パターンを使用:

```python
def _get_logger() -> Any:
    try:
        from ..utils.logging_config import get_logger
        return get_logger(__name__, module="example")
    except ImportError:
        import logging
        return logging.getLogger(__name__)
```

## 関連ドキュメント

- `docs/coding-standards.md` - コーディング規約
- `docs/testing-strategy.md` - テスト戦略
- `docs/development-process.md` - 開発プロセス
- `template/tests/` - テスト実装例

## 更新履歴

このREADME.mdは、モジュール構造や公開APIに変更があった場合に更新してください。

更新トリガー:
- 新規モジュール追加時
- 公開API変更時
- 設計パターン変更時
