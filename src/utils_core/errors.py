"""共通エラーハンドリングユーティリティ.

try-except-logger パターンの重複を解消するためのコンテキストマネージャを提供する。

Features
--------
- log_and_reraise: 例外をログに記録し再送出
- log_and_return: 例外をログに記録しデフォルト値を返す

Examples
--------
>>> from utils_core.errors import log_and_reraise
>>> from utils_core.logging import get_logger
>>> logger = get_logger(__name__)
>>> with log_and_reraise(logger, "data fetch", context={"url": url}):
...     response = requests.get(url)
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator


@contextmanager
def log_and_reraise(
    logger: Any,
    operation: str,
    *,
    context: dict[str, Any] | None = None,
    reraise_as: type[Exception] | None = None,
    skip_types: tuple[type[Exception], ...] = (),
    log_level: str = "error",
) -> Generator[None, None, None]:
    """例外発生時にログを出力し再送出するコンテキストマネージャ.

    Parameters
    ----------
    logger : Any
        structlog の BoundLogger インスタンス
    operation : str
        実行中の操作名（ログメッセージに使用）
    context : dict[str, Any] | None
        ログに追加するコンテキスト情報
    reraise_as : type[Exception] | None
        例外を変換する型。None の場合は元の例外をそのまま送出
    skip_types : tuple[type[Exception], ...]
        ログ出力せずそのまま再送出する例外型のタプル。
        例: ``skip_types=(CacheError,)`` で CacheError はパススルー
    log_level : str
        ログレベル（"error", "warning" など）。デフォルトは "error"

    Raises
    ------
    Exception
        キャッチした例外を再送出（reraise_as 指定時は変換後の例外）

    Examples
    --------
    >>> with log_and_reraise(logger, "cache lookup", context={"key": key}):
    ...     return cache.get(key)

    >>> with log_and_reraise(logger, "db query", reraise_as=CacheError,
    ...                      skip_types=(CacheError,)):
    ...     cursor.execute(sql)
    """
    try:
        yield
    except Exception as e:
        if skip_types and isinstance(e, skip_types):
            raise

        log_kwargs: dict[str, Any] = {
            "error": str(e),
            "exc_info": True,
        }
        if context:
            log_kwargs.update(context)

        log_fn = getattr(logger, log_level)
        log_fn(f"{operation} failed", **log_kwargs)

        if reraise_as is not None:
            raise reraise_as(f"{operation} failed: {e}") from e
        raise


@dataclass
class _ReturnContext[T]:
    """log_and_return で使用する値コンテナ."""

    value: T
    _default: T = field(repr=False)

    def __init__(self, default: T) -> None:
        self._default = default
        self.value = default


@contextmanager
def log_and_return[T](
    logger: Any,
    operation: str,
    *,
    default: T,
    context: dict[str, Any] | None = None,
    catch: tuple[type[Exception], ...] = (Exception,),
    log_level: str = "error",
) -> Generator[_ReturnContext[T], None, None]:
    """例外発生時にログを出力しデフォルト値を返すコンテキストマネージャ.

    ``return None`` パターン（例外をキャッチしてデフォルト値を返す）を
    共通化するためのコンテキストマネージャ。

    Parameters
    ----------
    logger : Any
        structlog の BoundLogger インスタンス
    operation : str
        実行中の操作名（ログメッセージに使用）
    default : T
        例外発生時に返すデフォルト値
    context : dict[str, Any] | None
        ログに追加するコンテキスト情報
    catch : tuple[type[Exception], ...]
        キャッチする例外型のタプル。デフォルトは (Exception,)
    log_level : str
        ログレベル。デフォルトは "error"

    Yields
    ------
    _ReturnContext[T]
        value 属性で結果を設定するコンテキストオブジェクト

    Examples
    --------
    >>> with log_and_return(logger, "fetch page", default=None) as ctx:
    ...     ctx.value = requests.get(url).text
    >>> return ctx.value  # 例外発生時は None
    """
    ctx = _ReturnContext(default)
    try:
        yield ctx
    except catch as e:
        log_kwargs: dict[str, Any] = {
            "error": str(e),
            "exc_info": True,
        }
        if context:
            log_kwargs.update(context)

        log_fn = getattr(logger, log_level)
        log_fn(f"{operation} failed", **log_kwargs)
        ctx.value = ctx._default
    # Non-matching exceptions propagate naturally


__all__ = [
    "log_and_reraise",
    "log_and_return",
]
