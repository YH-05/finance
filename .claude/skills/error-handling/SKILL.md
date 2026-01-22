---
name: error-handling
description: |
  Python エラーハンドリングパターンのナレッジベースを提供するスキル。
  シンプル/リッチパターンの選択ガイド、リトライ戦略、ロギング統合を提供。
  エラー設計時、例外クラス作成時、エラーハンドリング実装時にプロアクティブに使用。
allowed-tools: Read
---

# Error Handling

Python エラーハンドリングパターンのナレッジベースを提供するスキルです。

## 目的

このスキルは以下を提供します：

- **パターン選択ガイド**: シンプル/リッチパターンの使い分け
- **例外階層設計**: ドメイン固有の例外クラス設計
- **リトライ戦略**: 指数バックオフ、フォールバック
- **ロギング統合**: structlog との連携パターン

## いつ使用するか

### プロアクティブ使用（自動で検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討：

1. **新しいパッケージ・モジュールの作成**
   - `exceptions.py` または `errors.py` の作成時
   - 例外クラスの設計時

2. **エラーハンドリングの実装**
   - try/except ブロックの実装時
   - エラーメッセージの設計時
   - リトライロジックの実装時

3. **外部 API 連携**
   - HTTP クライアントの実装時
   - レート制限への対応時
   - タイムアウト処理の実装時

### 明示的な使用（ユーザー要求）

- 「エラーハンドリングのパターンを教えて」
- 「例外クラスを設計したい」
- 「リトライ処理を実装したい」

## パターン選択ガイド

### 判断基準

| 条件 | 推奨パターン |
|------|-------------|
| 内部ライブラリ、シンプルな例外 | シンプルパターン |
| 外部 API 連携、詳細情報必要 | リッチパターン |
| エラーのシリアライズ必要 | リッチパターン |
| CLI ツール | シンプルパターン |
| REST API サーバー | リッチパターン |

### シンプルパターン（RSS 方式）

**特徴**:
- 継承のみで実装、追加フィールドなし
- メッセージは `raise` 時に文字列で渡す
- Docstring で Parameters を明示（IDE ヒント用）

**使用例**:
```python
# 例外定義
class RSSError(Exception):
    """RSS パッケージの基底例外"""
    pass

class FeedNotFoundError(RSSError):
    """フィードが見つからない場合の例外"""
    pass

# 使用
raise FeedNotFoundError(f"Feed '{feed_id}' not found")
```

**適用場面**:
- 内部ライブラリ
- エラー情報のシリアライズが不要
- シンプルなエラー処理で十分

### リッチパターン（Market Analysis 方式）

**特徴**:
- エラーコード（Enum）による分類
- 詳細情報を保持する `details` フィールド
- `cause` による例外チェーン
- `to_dict()` でシリアライズ可能

**使用例**:
```python
# 例外定義
class MarketAnalysisError(Exception):
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause

# 使用
raise DataFetchError(
    "Failed to fetch data",
    symbol="AAPL",
    source="yfinance",
    code=ErrorCode.API_ERROR,
    cause=original_exception,
)
```

**適用場面**:
- 外部 API との連携
- エラーの分類・集計が必要
- REST API でエラーレスポンスを返す
- 詳細なデバッグ情報が必要

## 例外階層の基本構造

```
PackageError (基底例外)
├── ValidationError (入力検証エラー)
├── DataError (データ関連エラー)
│   ├── NotFoundError (データが見つからない)
│   └── FetchError (データ取得失敗)
├── NetworkError (ネットワークエラー)
│   ├── TimeoutError (タイムアウト)
│   └── RateLimitError (レート制限)
└── ConfigurationError (設定エラー)
```

## リトライ戦略

### 基本パターン

```python
import time
from typing import TypeVar, Callable

T = TypeVar("T")

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """指数バックオフでリトライ"""
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                "Retry attempt",
                attempt=attempt + 1,
                delay=delay,
                error=str(e),
            )
            time.sleep(delay)
    raise RuntimeError("Unreachable")
```

### フォールバックパターン

```python
def fetch_with_fallback(symbol: str) -> DataFrame:
    """プライマリ失敗時にフォールバック"""
    try:
        return primary_source.fetch(symbol)
    except DataFetchError as e:
        logger.warning("Primary failed, trying fallback", error=str(e))
        return fallback_source.fetch(symbol)
```

## リソース

このスキルには以下のリソースが含まれています：

### ./guide.md

エラーハンドリングの詳細設計原則：

- 例外階層の設計パターン
- エラーメッセージのベストプラクティス
- エラーコードの設計
- コンテキスト情報の収集

### ./examples/simple-pattern.md

シンプルパターンの完全実装例：

- RSS パッケージの exceptions.py
- 使用例とテスト例

### ./examples/rich-pattern.md

リッチパターンの完全実装例：

- Market Analysis パッケージの errors.py
- ErrorCode Enum の設計
- to_dict() によるシリアライズ

### ./examples/retry-patterns.md

リトライ・フォールバックパターン：

- 指数バックオフ実装
- サーキットブレーカー
- フォールバック戦略

### ./examples/logging-integration.md

ロギング統合パターン：

- structlog との連携
- エラーコンテキストの収集
- トレーサビリティ確保

## 使用例

### 例1: 新規パッケージの例外設計

**状況**: 新しいパッケージに例外クラスを作成したい

**処理**:
1. パターン選択ガイドを確認
2. パッケージの用途に基づきパターンを選択
3. 例外階層を設計
4. exceptions.py / errors.py を実装

**期待される出力**:
```python
# src/my_package/exceptions.py
class MyPackageError(Exception):
    """Base exception for my_package"""
    pass

class ValidationError(MyPackageError):
    """Input validation error"""
    pass

class DataNotFoundError(MyPackageError):
    """Requested data not found"""
    pass
```

---

### 例2: リトライ処理の実装

**状況**: 外部 API 呼び出しにリトライ処理を追加したい

**処理**:
1. retry-patterns.md を参照
2. 指数バックオフパターンを選択
3. 適切なリトライ回数・遅延を設定
4. ロギングを統合

**期待される出力**:
```python
result = retry_with_backoff(
    lambda: api_client.fetch(symbol),
    max_retries=3,
    base_delay=1.0,
    exceptions=(NetworkError, RateLimitError),
)
```

---

### 例3: エラーハンドリングのレビュー

**状況**: 既存のエラーハンドリングを改善したい

**処理**:
1. 現在の実装を分析
2. パターン選択ガイドで適切なパターンを確認
3. 改善点を特定
4. リファクタリングを提案

**期待される出力**:
```markdown
## 現状分析
- 生の Exception を catch している
- エラーメッセージが不明瞭
- リトライ処理がない

## 改善提案
1. ドメイン固有の例外クラスを作成
2. エラーメッセージにコンテキストを追加
3. リトライ処理を実装
```

## 品質基準

### 必須（MUST）

- [ ] 例外クラスには適切な Docstring がある
- [ ] エラーメッセージにはコンテキスト情報が含まれる
- [ ] 基底例外クラスが定義されている
- [ ] except Exception: は使用しない（具体的な例外を catch）

### 推奨（SHOULD）

- リトライ対象の例外は明示的に指定する
- エラー発生時はログを出力する
- from e を使用して例外チェーンを保持する
- エラーコードを使用して分類する（リッチパターンの場合）

## 参照実装

| パッケージ | ファイル | パターン |
|-----------|----------|----------|
| rss | `src/rss/exceptions.py` | シンプル |
| market_analysis | `src/market_analysis/errors.py` | リッチ |

## 関連スキル

- **development-guidelines**: 開発ガイドライン（エラーハンドリングセクション）

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `.claude/rules/common-instructions.md`: ロギング・エラーハンドリングの共通指示
