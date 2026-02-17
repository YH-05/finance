# リファクタリング計画: 構造化ログ・エラーハンドリング統一

## Context

`src/edgar/` は構造化ログ（structlog）を模範的に使用しているが、他パッケージでは `print()` が大量に残存し、ログファイルに記録されない・ログレベル制御が効かない状態。本計画では、優先度の高い5つの対象を段階的にリファクタリングし、`utils_core.logging.get_logger` ベースの構造化ログとエラーハンドリングを統一する。

## 決定事項

- **news/orchestrator.py**: ProgressCallback パターン（Protocol + ConsoleProgressCallback + SilentCallback）を導入
- **market/factset/factset_utils.py**: 全 print() を全面修正

## 実行戦略

**チーム並列実行**: 5つのPhaseは互いに独立（異なるパッケージ）なので、4ワーカーで並列実行する。

| ワーカー | 担当Phase | 対象ファイル |
|---------|----------|------------|
| Worker A | Phase 1 (edgar) | 5ファイル（軽微な編集） |
| Worker B | Phase 2 (news) | orchestrator.py + 新規 progress.py |
| Worker C | Phase 3 (factset) | factset_utils.py, factset_downloaded_data_utils.py, price.py |
| Worker D | Phase 4+5 (tsa + reporting) | tsa.py, market_report_utils.py, us_treasury.py |

完了後、`make check-all` で一括品質確認。

## 対象と規模（探索結果で検証済み）

| # | 対象 | print() 数 | エラー処理問題 | 深刻度 |
|---|------|-----------|---------------|--------|
| 1 | `src/edgar/` | 0 | 8箇所（軽微） | 低 |
| 2 | `src/news/orchestrator.py` | 37 | エラーハンドリングは良好 | **高** |
| 3 | `src/market/factset/factset_utils.py` | **178** | 7箇所 | **高** |
| 4 | `src/market/factset/factset_downloaded_data_utils.py` | 6 | 良好（rollback済み） | 中 |
| 5 | `src/market/alternative/tsa.py` | 18 | 3箇所 | 中 |
| 6 | `src/analyze/reporting/market_report_utils.py` | 4 | 1箇所 | 中 |
| 7 | `src/analyze/reporting/us_treasury.py` | 2 | `import logging` → `get_logger` | 中 |
| 8 | `src/market/factset/price.py` | 0 | `import logging` → `get_logger` | 低 |

---

## Phase 1: edgar パッケージ（軽微な改善）

既に高品質だが、以下の統一性向上を実施。

### 1-1. `exc_info=True` の追加（4箇所）

| ファイル | 行 | 現状 | 修正 |
|---------|-----|------|------|
| `extractors/_helpers.py` | ~51 | `logger.warning("Failed to get accession number", error=str(e))` | `exc_info=True` 追加 |
| `extractors/_helpers.py` | ~122 | `logger.warning("Failed to extract text from filing", ...)` | `exc_info=True` 追加 |
| `extractors/section.py` | ~358 | `logger.warning("Failed to save section text to cache", ...)` | `exc_info=True` 追加 |
| `batch.py` | ~95 | `logger.warning("Batch task failed", key=key, error=str(exc), ...)` | `exc_info=True` 追加 |

### 1-2. cache/manager.py: 例外発生前の警告ログ追加（4箇所）

`CacheError` を raise する前に `logger.warning()` を追加:

| 行 | 関数 | 追加内容 |
|----|------|---------|
| ~141 | `_init_db()` | `logger.warning("Failed to initialize cache database", error=str(e), exc_info=True)` |
| ~214 | `get_cached_text()` | `logger.warning("Failed to get cached text", filing_id=filing_id, exc_info=True)` |
| ~282 | `save_text()` | `logger.warning("Failed to save text to cache", filing_id=filing_id, exc_info=True)` |
| ~338 | `clear_expired()` | `logger.warning("Failed to clear expired cache entries", exc_info=True)` |

### 1-3. エントリ/出口ログの追加（4箇所）

| ファイル | 関数 | 追加内容 |
|---------|------|---------|
| `batch.py` | `_run_batch()` | 開始/完了の debug ログ（アイテム数、成功/失敗数） |
| `cache/manager.py` | `_init_db()` | スキーマ初期化の debug ログ |
| `extractors/text.py` | `_clean_text()` | テキスト長の debug ログ |
| `extractors/section.py` | `_find_section_positions()` | パターン数・結果数の debug ログ |

---

## Phase 2: news/orchestrator.py（本番ワークフロー）

### 2-1. ProgressCallback パターン導入

`print()` はユーザー向けCLI出力とデバッグ用ログの2つの役割を担っている。これを分離する。

**新規ファイル**: `src/news/progress.py`

```python
from typing import Protocol

class ProgressCallback(Protocol):
    def on_stage_start(self, stage: str, description: str) -> None: ...
    def on_progress(self, current: int, total: int, message: str, is_error: bool = False) -> None: ...
    def on_stage_complete(self, stage: str, success: int, total: int, extra: str = "") -> None: ...
    def on_workflow_complete(self, result: Any) -> None: ...

class ConsoleProgressCallback:
    """現在の print() 出力を再現するデフォルト実装"""
    # 現行の print() ロジックをそのまま移植

class SilentCallback:
    """テスト・バッチジョブ用の無音実装"""
    # 全メソッドが no-op
```

### 2-2. orchestrator.py の修正

**修正対象ファイル**: `src/news/orchestrator.py`

**現状**: `get_logger(__name__, module="orchestrator")` は既にインポート済み（L55, L60）。ヘルパーメソッド3つ（`_log_stage_start`, `_log_progress`, `_log_stage_complete`）も既存。エラーハンドリングは良好（`logger.error()` 使用済み）。

**修正内容**:
1. `__init__` に `progress_callback: ProgressCallback | None = None` パラメータ追加
2. ヘルパーメソッド3つを修正:
   - `_log_stage_start()` → `logger.info()` + `callback.on_stage_start()`（現行の print 3つを移行）
   - `_log_progress()` → `logger.info/error()` + `callback.on_progress()`（現行の print 1つを移行）
   - `_log_stage_complete()` → `logger.info()` + `callback.on_stage_complete()`（現行の print 1つを移行）
3. 直接 print() 箇所を構造化ログ + コールバックに置換:
   - `_print_config()` (4箇所, L337-342) → `logger.info("Workflow config", ...)` + callback
   - `_run_collection()` (6箇所, L362-391) → `logger.info/debug` + callback
   - `_run_extraction()` (1箇所, L421) → `logger.info` + callback
   - `_run_summarization()` (1箇所, L449) → `logger.info` + callback
   - `_run_per_category_publishing()` (5箇所, L500-524) → `logger.info` + callback
4. `_print_final_summary()` (15箇所, L664-697) → `logger.info()` + `callback.on_workflow_complete()`

---

## Phase 3: market/factset/（レガシーコード大規模修正）

### 3-1. factset_utils.py

**修正対象ファイル**: `src/market/factset/factset_utils.py`

#### ステップ 1: ロガー追加
```python
from utils_core.logging import get_logger
logger = get_logger(__name__)
```

#### ステップ 2: クリティカルなエラーハンドラ修正（7箇所）

全 `except Exception as e:` ブロック（L1065, L1253, L1455, L1528, L1790, L2055, L2181）の print → `logger.error(..., exc_info=True)`

| 行 | 現状 | 修正 |
|----|------|------|
| ~1065 | `print(f"❌ {table_name}: {e}")` | `logger.error("Table save failed", table=table_name, error=str(e), exc_info=True)` |
| ~1253 | 同上パターン | 同上 |
| ~1455 | `except Exception as e:` | `logger.error(...)` + exc_info |
| ~1528 | `except Exception as e:` | `logger.error(...)` + exc_info |
| ~1790 | `print(f"❌ エラー: {e}")` | `logger.error(...)` + raise維持 |
| ~2055 | `print(f"❌ Error processing ...")` | `logger.error(...)` + exc_info |
| ~2181 | `print(f"❌ Critical Error ...")` | `logger.critical(...)` + exc_info |

#### ステップ 3: バッチ統計 print ブロックの置換（3箇所×~15行）

`insert_active_returns_optimized`, `insert_active_returns_optimized_sqlite`, `store_to_database_batch` の各関数にある15行前後の print ブロックを、1つの `logger.info()` に集約。

```python
# Before: 15行の print
print("=" * 60)
print("📊 バッチ保存完了統計")
print(f"   成功: {len(results['success'])}/{len(df_dict)}テーブル")
...

# After: 1つの構造化ログ
logger.info(
    "Batch save completed",
    success_count=len(results["success"]),
    total_tables=len(df_dict),
    failed_count=len(results["failed"]),
    total_rows=results["total_rows"],
    prep_time_sec=round(results["prep_time"], 2),
    save_time_sec=round(results["save_time"], 2),
)
```

#### ステップ 4: ファイルエクスポート通知（~12箇所）
`print(f"A file has been exported -> {path}")` → `logger.info("File exported", path=str(path))`

#### ステップ 5: 進捗表示（~60箇所）
`print("⏳ ...")`, `print("✅ ...")` → `logger.debug()` / `logger.info()`

#### ステップ 6: 欠損値分析ブロック（~40行）
各ファクターの欠損統計を dict に集約し `logger.info("Missing value analysis", stats=...)` で出力。

#### ステップ 7: 装飾的 print の削除（~37箇所）
`print("=" * 60)` → 削除

### 3-2. factset_downloaded_data_utils.py

1. `from utils_core.logging import get_logger` + `logger = get_logger(__name__)` 追加
2. 6箇所の `print()` → `logger.info/warning`（`verbose` パラメータは `logger.debug` にマッピング）
3. エラーハンドリングは良好（`conn.rollback()` + `finally` 既存）→ `exc_info=True` 追加のみ

### 3-3. price.py

1. `import logging` → `from utils_core.logging import get_logger`
2. `logging.error(f"An error occured: {e}.")` → `logger.error(..., exc_info=True)` + `raise`

---

## Phase 4: market/alternative/tsa.py

**修正対象ファイル**: `src/market/alternative/tsa.py`（print 18箇所、ログインポートなし）

1. `from utils_core.logging import get_logger` + `logger = get_logger(__name__)` 追加
2. 18箇所の `print()` → 構造化ログ:
   - エラー系（L98-103, L142-146）→ `logger.error(..., exc_info=True)`
   - 情報系（データ保存成功等）→ `logger.info(...)`
   - 表示系（L115-129 `display_data_info` 内）→ `print` 維持（ユーザー向けCLI表示）+ `logger.debug` 追加
3. エラーハンドリング修正:
   - `except Exception` で `return None` → 予期しないエラーは `raise`
   - DB操作に `conn.rollback()` 追加
   - `table.find("tbody")` の None チェック追加

---

## Phase 5: analyze/reporting/（レポートモジュール）

### 5-1. market_report_utils.py

**現状**: ログインポートなし、print 4箇所

1. `from utils_core.logging import get_logger` + `logger = get_logger(__name__)` 追加
2. 4箇所の `print()` → `logger.error/warning`（L151-154 のEPSエラー等）
3. `get_eps_historical_data` の `except Exception` に `exc_info=True` 追加
4. `calculate_kalman_beta` の pykalman 欠落警告をログに変更

### 5-2. us_treasury.py

**現状**: `import logging` 使用（L5）、`logging.warning/error` で直接呼び出し（L40, L47）、print 2箇所

1. `import logging` → `from utils_core.logging import get_logger` + `logger = get_logger(__name__)`
2. `logging.warning(...)` → `logger.warning(...)` に修正
3. `logging.error(...)` → `logger.error(..., exc_info=True)` に修正
4. 2箇所の `print()` → `logger.warning/error`
5. `load_fred_series_id_json` のエラー分離（httpx vs JSON）

---

## 実装順序（チーム並列実行）

4ワーカーで並列実行 → 全完了後に `make check-all`:

```
Worker A: Phase 1 (edgar)          → 5ファイル軽微な編集
Worker B: Phase 2 (news)           → progress.py 新規作成 + orchestrator.py 大規模修正
Worker C: Phase 3 (factset)        → factset_utils.py(178 print), downloaded_data_utils.py, price.py
Worker D: Phase 4+5 (tsa+reporting) → tsa.py, market_report_utils.py, us_treasury.py
```

全ワーカー完了後に `make check-all` で品質確認。

---

## 検証方法

1. **全完了後に `make check-all`**（format, lint, typecheck, test）
2. **既存テストの通過**: 既存テストが全て通ることを確認
3. **news/orchestrator の後方互換**: `ConsoleProgressCallback` が現行の print 出力と同一であることを確認

---

## 修正対象ファイル一覧

| ファイル | 操作 |
|---------|------|
| `src/edgar/extractors/_helpers.py` | 編集 |
| `src/edgar/extractors/section.py` | 編集 |
| `src/edgar/extractors/text.py` | 編集 |
| `src/edgar/batch.py` | 編集 |
| `src/edgar/cache/manager.py` | 編集 |
| `src/news/progress.py` | **新規作成** |
| `src/news/orchestrator.py` | 編集 |
| `src/market/factset/factset_utils.py` | 編集 |
| `src/market/factset/factset_downloaded_data_utils.py` | 編集 |
| `src/market/factset/price.py` | 編集 |
| `src/market/alternative/tsa.py` | 編集 |
| `src/analyze/reporting/market_report_utils.py` | 編集 |
| `src/analyze/reporting/us_treasury.py` | 編集 |
