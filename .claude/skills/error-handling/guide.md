# Error Handling 詳細ガイド

## 例外階層の設計原則

### 基底例外クラスの設計

すべてのパッケージは固有の基底例外クラスを持つべきです。

```python
class PackageError(Exception):
    """パッケージ固有の基底例外

    このクラスを継承することで：
    - パッケージのすべての例外を一括で catch 可能
    - 外部から見た明確な境界を提供
    - 例外の分類とハンドリングが容易に
    """
    pass
```

### 例外の分類

例外は以下のカテゴリに分類することを推奨します：

| カテゴリ | 説明 | 例 |
|---------|------|-----|
| Validation | 入力検証エラー | 不正なパラメータ、フォーマットエラー |
| Data | データ関連エラー | データ未発見、データ破損 |
| Network | ネットワークエラー | 接続失敗、タイムアウト |
| Configuration | 設定エラー | 設定ファイル不正、環境変数未設定 |
| Authorization | 認証・認可エラー | 認証失敗、権限不足 |

### 例外階層の深さ

**推奨**: 2〜3 階層まで

```
# 推奨
PackageError
├── DataError
│   ├── NotFoundError
│   └── FetchError
└── NetworkError

# 非推奨（深すぎる）
PackageError
└── DataError
    └── FetchError
        └── HTTPFetchError
            └── HTTP500Error
                └── InternalServerError
```

## エラーメッセージのベストプラクティス

### 良いエラーメッセージの要素

1. **何が起きたか**（What happened）
2. **なぜ問題なのか**（Why it's a problem）
3. **どう解決するか**（How to fix it）

```python
# 悪い例
raise ValueError("Invalid input")

# 良い例
raise ValueError(
    f"Expected positive integer for 'count', got {count}. "
    f"Provide a value greater than 0."
)
```

### コンテキスト情報の含め方

```python
# 悪い例
raise FetchError("Failed to fetch data")

# 良い例
raise FetchError(
    f"Failed to fetch price data for symbol '{symbol}' "
    f"from {source}: {original_error}"
)
```

### 機密情報の除外

エラーメッセージに以下を含めないこと：

- パスワード、API キー
- 内部システムパス（本番環境）
- スタックトレースの詳細（エンドユーザー向け）
- 顧客の個人情報

```python
# 悪い例
raise AuthError(f"Failed to authenticate with API key: {api_key}")

# 良い例
raise AuthError(
    "Failed to authenticate. Check that your API key is valid."
)
```

## エラーコードの設計

### ErrorCode Enum の設計

```python
from enum import Enum

class ErrorCode(str, Enum):
    """エラーコードの列挙型

    命名規則:
    - UPPER_SNAKE_CASE
    - カテゴリ_詳細 の形式

    値:
    - str 継承により JSON シリアライズが容易
    """

    # 汎用
    UNKNOWN = "UNKNOWN"

    # ネットワーク関連
    NETWORK_ERROR = "NETWORK_ERROR"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_CONNECTION_REFUSED = "NETWORK_CONNECTION_REFUSED"

    # API 関連
    API_ERROR = "API_ERROR"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_AUTH_FAILED = "API_AUTH_FAILED"

    # データ関連
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_INVALID = "DATA_INVALID"
    DATA_CORRUPTED = "DATA_CORRUPTED"

    # バリデーション関連
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
```

### エラーコードの使い分け

```python
try:
    response = api_client.fetch(symbol)
except HTTPError as e:
    if e.status_code == 429:
        code = ErrorCode.API_RATE_LIMIT
    elif e.status_code == 401:
        code = ErrorCode.API_AUTH_FAILED
    elif e.status_code >= 500:
        code = ErrorCode.API_ERROR
    else:
        code = ErrorCode.UNKNOWN

    raise DataFetchError(
        f"Failed to fetch data for {symbol}",
        code=code,
        cause=e,
    )
```

## 例外チェーンの活用

### from e の使用

```python
try:
    data = external_api.fetch(symbol)
except HTTPError as e:
    # 例外チェーンを保持
    raise DataFetchError(
        f"Failed to fetch data for {symbol}",
        cause=e,
    ) from e
```

### スタックトレースの可読性

```python
# 例外チェーンがある場合のスタックトレース例
Traceback (most recent call last):
  File "api_client.py", line 50, in fetch
    response = requests.get(url)
  ...
requests.exceptions.ConnectionError: Connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "service.py", line 100, in get_data
    return api_client.fetch(symbol)
  ...
DataFetchError: Failed to fetch data for AAPL
```

## コンテキスト情報の収集

### details フィールドの活用

```python
class DataFetchError(MarketAnalysisError):
    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        source: str | None = None,
        **kwargs,
    ) -> None:
        details = kwargs.pop("details", {}) or {}
        if symbol:
            details["symbol"] = symbol
        if source:
            details["source"] = source

        super().__init__(message, details=details, **kwargs)
```

### to_dict() によるシリアライズ

```python
def to_dict(self) -> dict[str, Any]:
    """例外を辞書に変換（API レスポンス用）"""
    result = {
        "error_type": self.__class__.__name__,
        "code": self.code.value,
        "message": self.message,
        "details": self.details,
    }

    if self.cause:
        result["cause"] = {
            "type": type(self.cause).__name__,
            "message": str(self.cause),
        }

    return result
```

## ハンドリングパターン

### 特定の例外を catch

```python
# 悪い例
try:
    result = process_data(data)
except Exception:
    logger.error("Something went wrong")
    raise

# 良い例
try:
    result = process_data(data)
except ValidationError as e:
    logger.warning("Validation failed", error=str(e), field=e.field)
    raise
except DataFetchError as e:
    logger.error("Data fetch failed", error=str(e), symbol=e.symbol)
    raise
```

### 例外の変換

```python
def public_api_method(symbol: str) -> DataFrame:
    """外部向け API メソッド

    内部例外を外部向け例外に変換
    """
    try:
        return internal_fetch(symbol)
    except InternalDatabaseError as e:
        # 内部の詳細を隠蔽
        raise DataError("Data is temporarily unavailable") from e
    except InternalAPIError as e:
        raise DataFetchError(
            f"Failed to fetch data for {symbol}",
            symbol=symbol,
        ) from e
```

### finally の活用

```python
def process_with_cleanup(resource: Resource) -> Result:
    """リソースのクリーンアップを保証"""
    try:
        return resource.process()
    except ProcessingError as e:
        logger.error("Processing failed", error=str(e))
        raise
    finally:
        # 成功・失敗に関わらず実行
        resource.cleanup()
```

## テストでの例外検証

### pytest.raises の使用

```python
import pytest

def test_raises_validation_error_for_invalid_input():
    with pytest.raises(ValidationError) as exc_info:
        process_data(invalid_data)

    assert "expected positive integer" in str(exc_info.value)
    assert exc_info.value.field == "count"

def test_raises_with_correct_error_code():
    with pytest.raises(DataFetchError) as exc_info:
        fetch_data("INVALID_SYMBOL")

    assert exc_info.value.code == ErrorCode.DATA_NOT_FOUND
```

### 例外の属性検証

```python
def test_exception_contains_context():
    with pytest.raises(DataFetchError) as exc_info:
        fetch_data("AAPL")

    error = exc_info.value
    assert error.symbol == "AAPL"
    assert error.source == "yfinance"
    assert error.details["symbol"] == "AAPL"
```

## 参考リンク

- [Python 公式ドキュメント - 例外](https://docs.python.org/3/library/exceptions.html)
- [PEP 3134 - Exception Chaining](https://peps.python.org/pep-3134/)
