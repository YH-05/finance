# エラーメッセージパターン集

具体的で解決策を示すエラーメッセージの実装パターンです。

## 基本原則

1. **具体的な値を含める**: 何が問題かを明確に
2. **解決策を示す**: どうすれば良いかを提示
3. **コンテキストを保持**: エラーチェーンで原因を追跡可能に

## バリデーションエラー

### 型チェック

```python
# 悪い例
raise TypeError("Invalid type")

# 良い例
raise TypeError(
    f"Expected str or bytes, got {type(value).__name__}"
)

# より良い例（期待値と実際の値）
raise TypeError(
    f"Argument 'data' must be str or bytes, "
    f"got {type(data).__name__}: {data!r}"
)
```

### 値の範囲チェック

```python
# 悪い例
raise ValueError("Invalid value")

# 良い例
raise ValueError(
    f"retry_count must be between 1 and 10, got {retry_count}"
)

# 境界値を明示
raise ValueError(
    f"page_size must be positive and <= 100, got {page_size}"
)
```

### 必須フィールドのチェック

```python
# 悪い例
raise ValueError("Missing required field")

# 良い例
raise ValueError(
    f"Required field 'email' is missing. "
    f"Provided fields: {list(data.keys())}"
)

# 複数フィールドの場合
missing_fields = {"name", "email"} - set(data.keys())
if missing_fields:
    raise ValueError(
        f"Missing required fields: {', '.join(sorted(missing_fields))}"
    )
```

### フォーマットチェック

```python
# 悪い例
raise ValueError("Invalid email")

# 良い例
raise ValueError(
    f"Invalid email format: {email!r}. "
    f"Expected format: user@domain.com"
)

# 正規表現パターンを示す
raise ValueError(
    f"Invalid phone number: {phone!r}. "
    f"Expected format: +XX-XXX-XXXX-XXXX"
)
```

## リソースエラー

### ファイルが見つからない

```python
# 悪い例
raise FileNotFoundError("File not found")

# 良い例
raise FileNotFoundError(
    f"Config file not found: {path}"
)

# 解決策を示す
raise FileNotFoundError(
    f"Config file not found at {path}. "
    f"Create it by running: python -m {__package__}.init"
)

# 検索したパスを示す
raise FileNotFoundError(
    f"Could not find '{filename}' in any of: "
    f"{', '.join(search_paths)}"
)
```

### リソースが見つからない

```python
# 悪い例
raise NotFoundError("Not found")

# 良い例
class NotFoundError(Exception):
    def __init__(self, resource: str, id: str) -> None:
        super().__init__(f"{resource} not found: {id}")
        self.resource = resource
        self.id = id

raise NotFoundError("User", user_id)
# → "User not found: user-123"

# 追加情報を含める
raise NotFoundError(
    f"Task not found: {task_id}. "
    f"It may have been deleted or you don't have access."
)
```

## ネットワーク/API エラー

### 接続エラー

```python
# 悪い例
raise ConnectionError("Connection failed")

# 良い例
raise ConnectionError(
    f"Failed to connect to {host}:{port}. "
    f"Error: {original_error}"
)

# リトライ情報を含める
raise ConnectionError(
    f"Failed to connect to {url} after {retry_count} attempts. "
    f"Last error: {last_error}"
)
```

### API エラー

```python
# 悪い例
raise APIError("API error")

# 良い例
class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

raise APIError(
    f"API request failed with status {status_code}: {response.reason}",
    status_code=status_code,
    response_body=response.text,
)

# レート制限
raise RateLimitError(
    f"Rate limit exceeded. Retry after {retry_after} seconds. "
    f"Current usage: {current_usage}/{limit}"
)
```

## 設定エラー

### 環境変数

```python
# 悪い例
raise RuntimeError("Missing environment variable")

# 良い例
raise RuntimeError(
    f"Environment variable '{var_name}' is not set. "
    f"Set it by: export {var_name}=your-value"
)

# 複数の方法を示す
raise RuntimeError(
    f"API_KEY is not configured. Set it using one of:\n"
    f"  1. Environment variable: export API_KEY=your-key\n"
    f"  2. Config file: Add 'api_key' to ~/.config/myapp/config.yaml\n"
    f"  3. Command line: --api-key your-key"
)
```

### 設定値の検証

```python
# 悪い例
raise ValueError("Invalid config")

# 良い例
raise ValueError(
    f"Invalid value for 'log_level': {value!r}. "
    f"Must be one of: {', '.join(VALID_LOG_LEVELS)}"
)

# 型の問題
raise TypeError(
    f"Config 'timeout' must be int or float, "
    f"got {type(value).__name__} in {config_path}"
)
```

## カスタム例外クラス

### ドメイン例外の設計

```python
class MarketDataError(Exception):
    """市場データ操作の基底例外。"""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.__cause__ = cause


class SymbolNotFoundError(MarketDataError):
    """銘柄が見つからない。"""

    def __init__(self, symbol: str) -> None:
        super().__init__(
            f"Symbol not found: {symbol}. "
            f"Verify the ticker is valid and traded.",
            symbol=symbol,
        )


class DataFetchError(MarketDataError):
    """データ取得に失敗。"""

    def __init__(
        self,
        symbol: str,
        period: str,
        cause: Exception,
    ) -> None:
        super().__init__(
            f"Failed to fetch data for {symbol} ({period}): {cause}",
            symbol=symbol,
            cause=cause,
        )


class StaleDataError(MarketDataError):
    """データが古い。"""

    def __init__(
        self,
        symbol: str,
        last_update: datetime,
        max_age: timedelta,
    ) -> None:
        age = datetime.now() - last_update
        super().__init__(
            f"Data for {symbol} is stale. "
            f"Last update: {last_update.isoformat()} ({age} ago). "
            f"Max allowed age: {max_age}",
            symbol=symbol,
        )
```

### バリデーション例外

```python
class ValidationError(Exception):
    """入力検証エラー。"""

    def __init__(
        self,
        message: str,
        field: str,
        value: object,
        constraint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.value = value
        self.constraint = constraint

    def to_dict(self) -> dict[str, Any]:
        """API レスポンス用の辞書に変換。"""
        return {
            "error": "validation_error",
            "message": str(self),
            "field": self.field,
            "constraint": self.constraint,
        }


# 使用例
raise ValidationError(
    f"Email format is invalid: {email!r}",
    field="email",
    value=email,
    constraint="email_format",
)
```

## エラーチェーン

### from を使った例外チェーン

```python
try:
    data = json.loads(raw_data)
except json.JSONDecodeError as e:
    raise ConfigError(
        f"Failed to parse config file {path}: {e}"
    ) from e

# スタックトレースに元の例外が含まれる:
# ConfigError: Failed to parse config file config.json: ...
#
# The above exception was the direct cause of the following exception:
#
# json.JSONDecodeError: Expecting property name: line 5
```

### 原因を保持するカスタム例外

```python
class DatabaseError(Exception):
    """データベースエラー。"""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.query = query
        self.__cause__ = cause


try:
    cursor.execute(query, params)
except sqlite3.Error as e:
    raise DatabaseError(
        f"Query execution failed: {e}",
        query=query,
        cause=e,
    ) from e
```

## エラーメッセージのチェックリスト

エラーメッセージを書く際の確認項目：

- [ ] 何が問題かが明確
- [ ] 問題の値・状態が含まれている
- [ ] 期待される値・状態が示されている
- [ ] 解決策または次のアクションが示されている
- [ ] 技術的すぎず、理解可能
- [ ] センシティブな情報（パスワード等）が含まれていない
