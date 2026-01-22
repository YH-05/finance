# シンプルパターン（RSS 方式）

内部ライブラリ向けのシンプルなエラーハンドリングパターンです。

## 特徴

- **継承のみで実装**: 追加フィールドなし
- **メッセージは raise 時に渡す**: Docstring で Parameters を明示
- **軽量**: コンテキスト最小限

## いつ使うか

- 内部ライブラリ
- エラー情報のシリアライズが不要
- シンプルなエラー処理で十分
- CLI ツール

## 実装例

### exceptions.py

```python
"""Custom exceptions for the package."""


class PackageError(Exception):
    """Base exception for all package errors.

    This is the base class for all custom exceptions raised by this package.
    All package-specific exceptions should inherit from this class.

    Examples
    --------
    >>> try:
    ...     raise PackageError("An error occurred")
    ... except PackageError as e:
    ...     print(f"Caught error: {e}")
    Caught error: An error occurred
    """

    pass


class ValidationError(PackageError):
    """Exception raised when input validation fails.

    Parameters
    ----------
    message : str
        Description of the validation error

    Examples
    --------
    >>> raise ValidationError("Expected positive integer, got -1")
    Traceback (most recent call last):
        ...
    ValidationError: Expected positive integer, got -1
    """

    pass


class NotFoundError(PackageError):
    """Exception raised when a resource is not found.

    Parameters
    ----------
    resource_type : str
        The type of resource that was not found
    resource_id : str
        The identifier of the resource

    Examples
    --------
    >>> raise NotFoundError("User with ID '123' not found")
    Traceback (most recent call last):
        ...
    NotFoundError: User with ID '123' not found
    """

    pass


class FetchError(PackageError):
    """Exception raised when data fetching fails.

    Parameters
    ----------
    source : str
        The source that failed
    reason : str
        The reason for failure

    Examples
    --------
    >>> raise FetchError("Failed to fetch from API: Connection timeout")
    Traceback (most recent call last):
        ...
    FetchError: Failed to fetch from API: Connection timeout
    """

    pass


class ConfigurationError(PackageError):
    """Exception raised when configuration is invalid.

    Parameters
    ----------
    config_key : str
        The configuration key that is invalid
    reason : str
        The reason why it's invalid

    Examples
    --------
    >>> raise ConfigurationError("Missing required config 'API_KEY'")
    Traceback (most recent call last):
        ...
    ConfigurationError: Missing required config 'API_KEY'
    """

    pass
```

### 使用例

```python
from my_package.exceptions import (
    NotFoundError,
    ValidationError,
    FetchError,
)


def get_user(user_id: str) -> User:
    """ユーザーを取得する

    Raises
    ------
    ValidationError
        user_id が空の場合
    NotFoundError
        ユーザーが存在しない場合
    """
    if not user_id:
        raise ValidationError("user_id cannot be empty")

    user = database.find_user(user_id)
    if user is None:
        raise NotFoundError(f"User with ID '{user_id}' not found")

    return user


def fetch_data(source: str) -> Data:
    """外部ソースからデータを取得する

    Raises
    ------
    FetchError
        データ取得に失敗した場合
    """
    try:
        return external_api.get(source)
    except ConnectionError as e:
        raise FetchError(
            f"Failed to fetch from {source}: {e}"
        ) from e
```

### エラーハンドリング

```python
def process_user_request(user_id: str) -> Response:
    try:
        user = get_user(user_id)
        return Response(success=True, data=user)

    except ValidationError as e:
        logger.warning("Validation failed", error=str(e))
        return Response(success=False, error="Invalid input")

    except NotFoundError as e:
        logger.info("User not found", user_id=user_id)
        return Response(success=False, error="User not found")

    except FetchError as e:
        logger.error("Fetch failed", error=str(e))
        return Response(success=False, error="Service unavailable")
```

## テスト例

```python
import pytest
from my_package.exceptions import NotFoundError, ValidationError


class TestGetUser:
    def test_正常系_有効なIDでユーザーを取得できる(self):
        user = get_user("valid-id")
        assert user.id == "valid-id"

    def test_異常系_空のIDでValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            get_user("")

        assert "cannot be empty" in str(exc_info.value)

    def test_異常系_存在しないIDでNotFoundError(self):
        with pytest.raises(NotFoundError) as exc_info:
            get_user("nonexistent-id")

        assert "nonexistent-id" in str(exc_info.value)
```

## 参照実装

このプロジェクトでの参照実装：

- `src/rss/exceptions.py`: RSS パッケージの例外定義

```python
# 実際の rss パッケージの例外
class RSSError(Exception):
    """Base exception for all RSS package errors."""
    pass

class FeedNotFoundError(RSSError):
    """Exception raised when a feed is not found."""
    pass

class FeedFetchError(RSSError):
    """Exception raised when fetching a feed fails."""
    pass

class InvalidURLError(RSSError):
    """Exception raised when a URL is invalid."""
    pass
```

## シンプルパターンの利点

1. **低オーバーヘッド**: 追加の属性やメソッドがないため軽量
2. **理解しやすい**: 標準の Python 例外と同じ使い方
3. **メンテナンスが容易**: コードが少ないため変更が簡単
4. **Docstring で十分**: Parameters を Docstring で説明
5. **柔軟なメッセージ**: raise 時に自由にメッセージを構成

## いつリッチパターンに移行すべきか

以下の条件が複数該当する場合は、リッチパターンへの移行を検討：

- [ ] エラーをプログラム的に分類する必要がある（エラーコード）
- [ ] エラーを JSON 等にシリアライズして返す必要がある
- [ ] エラーの詳細情報を構造化して保持したい
- [ ] エラーの統計・分析を行いたい
- [ ] 外部 API との連携でエラーレスポンスを返す
