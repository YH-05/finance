"""Token bucket rate limiter (thread-safe).

SEC EDGAR の ~10 req/sec/IP 制限を順守するための単純な実装。
"""

from __future__ import annotations

import threading
import time


class TokenBucket:
    """Token bucket rate limiter.

    Parameters
    ----------
    rate : float
        毎秒生成するトークン数 (= 許容 req/sec).
    capacity : int
        最大バースト許容トークン数.
    """

    def __init__(self, rate: float = 5.0, capacity: int = 10) -> None:
        self.rate = float(rate)
        self.capacity = int(capacity)
        self.tokens: float = float(capacity)
        self.last = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, n: int = 1) -> None:
        """n 個のトークンが揃うまでブロックして acquire."""
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens >= n:
                self.tokens -= n
                return
            need = n - self.tokens
            wait = need / self.rate
            self.tokens = 0
        time.sleep(wait)
