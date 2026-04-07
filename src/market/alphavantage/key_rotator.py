"""API key rotator for the Alpha Vantage module.

This module provides ``KeyRotator``, a usage-based key rotation manager
for the Alpha Vantage API free tier.  Multiple API keys are cycled through
as each key exhausts its daily request quota (default 25 req/day/key).

Design Notes
------------
- Keys are resolved from ``ALPHA_VANTAGE_API_KEYS`` (comma-separated) first,
  then fall back to ``ALPHA_VANTAGE_API_KEY`` (single key).
- Key values are never written to log output; only the zero-based ``key_index``
  is logged (CWE-312 prevention).
- Thread-safety is provided via ``threading.Lock`` for concurrent use.

See Also
--------
market.alphavantage.constants : ``ALPHA_VANTAGE_API_KEYS_ENV``,
    ``ALPHA_VANTAGE_API_KEY_ENV``, ``DEFAULT_DAILY_LIMIT_PER_KEY``.
market.alphavantage.errors : ``AlphaVantageRateLimitError``.
"""

from __future__ import annotations

import os
import threading
from typing import Final

from market.alphavantage.constants import (
    ALPHA_VANTAGE_API_KEY_ENV,
    ALPHA_VANTAGE_API_KEYS_ENV,
    DEFAULT_DAILY_LIMIT_PER_KEY,
)
from market.alphavantage.errors import AlphaVantageRateLimitError
from utils_core.logging import get_logger

logger = get_logger(__name__)

# Minimum character length for a valid Alpha Vantage API key.
# Keys shorter than this are almost certainly truncated or mistyped.
_MIN_KEY_LENGTH: Final[int] = 10


def _check_key_lengths(keys: list[str]) -> None:
    """Raise ValueError if any key is shorter than _MIN_KEY_LENGTH.

    Parameters
    ----------
    keys : list[str]
        Resolved, non-empty list of API key strings.

    Raises
    ------
    ValueError
        If any key has fewer than ``_MIN_KEY_LENGTH`` characters.
        Key values are not included in the error message (CWE-312).
    """
    short_indices = [i for i, k in enumerate(keys) if len(k) < _MIN_KEY_LENGTH]
    if short_indices:
        lengths = [len(keys[i]) for i in short_indices]
        raise ValueError(
            f"Alpha Vantage API key(s) at index {short_indices} are too short "
            f"(lengths: {lengths}, minimum: {_MIN_KEY_LENGTH} characters). "
            "Verify that the full key value is configured."
        )


def _resolve_keys(keys: list[str] | None) -> list[str]:
    """Resolve API keys from argument or environment variables.

    Parameters
    ----------
    keys : list[str] | None
        Explicit key list.  If ``None``, falls back to environment variables.

    Returns
    -------
    list[str]
        Non-empty list of API key strings.

    Raises
    ------
    ValueError
        If no keys can be resolved from any source.
    """
    if keys is not None:
        resolved = [k.strip() for k in keys if k.strip()]
        if not resolved:
            raise ValueError(
                "No Alpha Vantage API keys provided. "
                f"Set {ALPHA_VANTAGE_API_KEYS_ENV} or {ALPHA_VANTAGE_API_KEY_ENV}."
            )
        _check_key_lengths(resolved)
        return resolved

    # Try multi-key env var first
    multi = os.environ.get(ALPHA_VANTAGE_API_KEYS_ENV, "").strip()
    if multi:
        resolved = [k.strip() for k in multi.split(",") if k.strip()]
        if resolved:
            _check_key_lengths(resolved)
            logger.debug(
                "Resolved API keys from environment",
                env_var=ALPHA_VANTAGE_API_KEYS_ENV,
                key_count=len(resolved),
            )
            return resolved

    # Fall back to single-key env var
    single = os.environ.get(ALPHA_VANTAGE_API_KEY_ENV, "").strip()
    if single:
        _check_key_lengths([single])
        logger.debug(
            "Resolved single API key from environment",
            env_var=ALPHA_VANTAGE_API_KEY_ENV,
        )
        return [single]

    raise ValueError(
        "No Alpha Vantage API keys found. "
        f"Set {ALPHA_VANTAGE_API_KEYS_ENV} (comma-separated) "
        f"or {ALPHA_VANTAGE_API_KEY_ENV} environment variable."
    )


class KeyRotator:
    """Usage-based API key rotator for the Alpha Vantage free tier.

    Manages a pool of API keys and automatically rotates to the next key
    once the current key has consumed its daily request quota.

    Parameters
    ----------
    keys : list[str] | None, optional
        Explicit list of API key strings.  When ``None`` (default), keys are
        resolved from environment variables: ``ALPHA_VANTAGE_API_KEYS``
        (comma-separated) → ``ALPHA_VANTAGE_API_KEY`` (single key fallback).
    daily_limit_per_key : int, optional
        Maximum requests allowed per key per day.
        Defaults to ``DEFAULT_DAILY_LIMIT_PER_KEY`` (25).

    Raises
    ------
    ValueError
        If no keys are available from any source.

    Notes
    -----
    API key strings are held in plain text in process memory for the lifetime
    of this instance.  Treat the ``KeyRotator`` object as a secret:

    - Do not pickle, serialize, or log the instance.
    - Do not pass it to untrusted code.
    - Key *values* are never written to log output; only ``key_index`` is
      recorded (CWE-316 mitigation).

    Examples
    --------
    >>> rotator = KeyRotator(keys=["key1", "key2"], daily_limit_per_key=25)
    >>> rotator.key_count
    2
    >>> rotator.total_budget
    50
    >>> key = rotator.next_key()  # returns "key1"
    """

    def __init__(
        self,
        keys: list[str] | None = None,
        daily_limit_per_key: int = DEFAULT_DAILY_LIMIT_PER_KEY,
    ) -> None:
        self._keys: list[str] = _resolve_keys(keys)
        self._daily_limit: int = daily_limit_per_key
        # usage_counts[i] tracks how many requests have been made with keys[i]
        self._usage_counts: list[int] = [0] * len(self._keys)
        self._current_index: int = 0
        self._lock: threading.Lock = threading.Lock()

        logger.info(
            "KeyRotator initialized",
            key_count=len(self._keys),
            daily_limit_per_key=daily_limit_per_key,
            total_budget=self.total_budget,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def key_count(self) -> int:
        """Number of API keys in the pool.

        Returns
        -------
        int
            Total number of keys managed by this rotator.
        """
        return len(self._keys)

    @property
    def total_budget(self) -> int:
        """Total daily request budget across all keys.

        Returns
        -------
        int
            ``key_count * daily_limit_per_key``.
        """
        return len(self._keys) * self._daily_limit

    @property
    def remaining_budget(self) -> int:
        """Remaining request budget across all keys.

        Returns
        -------
        int
            Total budget minus the sum of all keys' usage counts.
        """
        with self._lock:
            used = sum(self._usage_counts)
        return self.total_budget - used

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def next_key(self) -> str:
        """Return the current active API key and increment its usage count.

        Automatically rotates to the next key when the current key has
        exhausted its daily quota.

        Returns
        -------
        str
            The API key string to use for the next request.

        Raises
        ------
        AlphaVantageRateLimitError
            When all keys have exhausted their daily budgets.

        Notes
        -----
        Key values are not logged.  Only ``key_index`` is recorded.
        """
        with self._lock:
            # Advance past any exhausted keys
            while self._current_index < len(self._keys):
                idx = self._current_index
                if self._usage_counts[idx] < self._daily_limit:
                    break
                # Current key exhausted; move to next
                logger.info(
                    "API key exhausted, rotating to next key",
                    exhausted_key_index=idx,
                    next_key_index=idx + 1,
                )
                self._current_index += 1
            else:
                # All keys exhausted
                raise AlphaVantageRateLimitError(
                    f"All {len(self._keys)} API key(s) have exhausted their "
                    f"daily budget ({self._daily_limit} req/key, "
                    f"{self.total_budget} total). "
                    "Try again tomorrow.",
                    url=None,
                    retry_after=None,
                )

            idx = self._current_index
            self._usage_counts[idx] += 1
            key = self._keys[idx]

            logger.debug(
                "Returning API key",
                key_index=idx,
                usage=self._usage_counts[idx],
                limit=self._daily_limit,
            )
            return key

    def mark_rate_limited(self) -> None:
        """Mark the current key as rate-limited and rotate immediately.

        Call this method when the API responds with a rate-limit error
        to skip the current key even if its quota is not yet exhausted.

        Notes
        -----
        Sets the current key's usage count to ``daily_limit_per_key``
        so that the next call to ``next_key()`` will advance to the
        following key.
        """
        with self._lock:
            idx = self._current_index
            if idx < len(self._keys):
                logger.warning(
                    "Key marked as rate-limited, forcing rotation",
                    key_index=idx,
                    previous_usage=self._usage_counts[idx],
                )
                # Exhaust the key so next_key() will rotate past it
                self._usage_counts[idx] = self._daily_limit


__all__ = ["KeyRotator"]
