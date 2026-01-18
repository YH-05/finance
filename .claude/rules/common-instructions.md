# 共通指示

## ロギング（必須）

全コードにログを実装すること。

```python
from finance.utils.logging_config import get_logger

logger = get_logger(__name__)

def process_data(data: list) -> list:
    logger.debug("Processing started", item_count=len(data))
    try:
        result = transform(data)
        logger.info("Processing completed", output_count=len(result))
        return result
    except Exception as e:
        logger.error("Processing failed", error=str(e), exc_info=True)
        raise
```

## 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| LOG_LEVEL | ログレベル | INFO |
| LOG_FORMAT | フォーマット (json/text) | text |
| PROJECT_ENV | 環境 (development/production) | development |

## エラーハンドリング

```python
# カスタム例外クラス
class ValidationError(Exception):
    def __init__(self, message: str, field: str, value: object) -> None:
        super().__init__(message)
        self.field = field
        self.value = value

# エラーハンドリングパターン
async def get_task(id: str) -> Task:
    try:
        task = await repository.find_by_id(id)
        if task is None:
            raise NotFoundError("Task", id)
        return task
    except NotFoundError:
        logger.warning(f"タスクが見つかりません: {id}")
        raise
    except Exception as e:
        raise DatabaseError("タスクの取得に失敗しました", cause=e) from e
```

## 実装フロー

1. format → lint → typecheck → test
2. 新機能は TDD 必須
3. 全コードにログ必須
4. 重い処理はプロファイル実施

## template/ 参照パターン

実装前に必ず参照すること。template/ は変更・削除禁止。

| 実装対象 | 参照先 |
|----------|--------|
| モジュール概要 | `template/src/template_package/README.md` |
| クラス/関数 | `template/src/template_package/core/example.py` |
| 型定義 | `template/src/template_package/types.py` |
| ユーティリティ | `template/src/template_package/utils/helpers.py` |
| ロギング設定 | `template/src/template_package/utils/logging_config.py` |
| プロファイリング | `template/src/template_package/utils/profiling.py` |
| 単体テスト | `template/tests/unit/` |
| プロパティテスト | `template/tests/property/` |
| 統合テスト | `template/tests/integration/` |
| フィクスチャ | `template/tests/conftest.py` |

## プロファイリング使用例

```python
from finance.utils.profiling import profile, timeit, profile_context

@profile  # 詳細プロファイリング
def heavy_function():
    ...

@timeit  # 実行時間計測
def timed_function():
    ...

with profile_context("処理名"):  # コンテキスト計測
    ...
```

## 効率化テクニック

### コミュニケーション記法

```
→  処理フロー      analyze → fix → test
|  選択/区切り     option1 | option2
&  並列/結合       task1 & task2
»  シーケンス      step1 » step2
@  参照/場所       @file:line
```

### 実行パターン

- **並列**: 依存なし & 競合なし → 複数ファイル読込、独立テスト
- **バッチ**: 同種操作 → 一括フォーマット、インポート修正
- **逐次**: 依存あり | 状態変更 → DB マイグレ、段階的リファクタ

### エラーリカバリー

- **リトライ**: max 3回、指数バックオフ
- **フォールバック**: 高速手法 → 確実な手法
- **状態復元**: チェックポイント » ロールバック
