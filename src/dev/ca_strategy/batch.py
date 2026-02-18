"""Batch processing utilities with checkpoint, retry, and parallel execution.

Provides checkpoint-based resume, exponential backoff retry, and
ThreadPoolExecutor parallelism for processing large batches of items
(e.g. 300 tickers in the CA Strategy pipeline).

Features
--------
- CheckpointManager: Save/load progress to JSON for crash recovery
- BatchProcessor[T]: Generic batch processor with:
  - process_with_checkpoint(): Checkpoint-aware batch execution
  - ThreadPoolExecutor parallel processing (default max_workers=5)
  - Partial-failure tolerance (Exception stored in result dict)
  - tqdm progress bar
  - Exponential backoff retry (default max 3 attempts)

Notes
-----
ThreadPoolExecutor is used because the underlying operations are I/O-bound
(LLM API calls, file reads). ProcessPoolExecutor is avoided due to pickle
serialization issues with complex objects.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from tqdm import tqdm

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

logger = get_logger(__name__)


class CheckpointManager:
    """Manage batch processing progress via JSON checkpoint files.

    Tracks which items have been successfully processed, enabling
    crash recovery by skipping already-completed items on restart.

    Parameters
    ----------
    path : Path
        Path to the checkpoint JSON file.

    Attributes
    ----------
    _path : Path
        Checkpoint file path.
    _completed : set[str]
        Set of completed item keys.

    Examples
    --------
    >>> mgr = CheckpointManager(Path("checkpoint.json"))
    >>> mgr.mark_completed("AAPL")
    >>> mgr.save()
    >>> # Later, on restart:
    >>> mgr2 = CheckpointManager(Path("checkpoint.json"))
    >>> mgr2.load()
    >>> mgr2.is_completed("AAPL")
    True
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._completed: set[str] = set()

    @property
    def completed_keys(self) -> set[str]:
        """Return the set of completed item keys."""
        return set(self._completed)

    def mark_completed(self, key: str) -> None:
        """Mark an item key as completed.

        Parameters
        ----------
        key : str
            The item key to mark as completed.
        """
        self._completed.add(key)

    def is_completed(self, key: str) -> bool:
        """Check if an item key has been completed.

        Parameters
        ----------
        key : str
            The item key to check.

        Returns
        -------
        bool
            True if the key is in the completed set.
        """
        return key in self._completed

    def save(self) -> None:
        """Save current progress to the checkpoint JSON file.

        Creates parent directories if they do not exist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"completed": sorted(self._completed)}
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.debug(
            "Checkpoint saved",
            path=str(self._path),
            completed_count=len(self._completed),
        )

    def load(self) -> None:
        """Load progress from the checkpoint JSON file.

        If the file does not exist, the completed set remains empty
        (no exception is raised).
        """
        if not self._path.exists():
            logger.debug(
                "Checkpoint file not found, starting fresh", path=str(self._path)
            )
            return

        data = json.loads(self._path.read_text(encoding="utf-8"))
        self._completed = set(data.get("completed", []))
        logger.debug(
            "Checkpoint loaded",
            path=str(self._path),
            completed_count=len(self._completed),
        )

    def clear(self) -> None:
        """Reset all progress (clear completed keys)."""
        self._completed.clear()


class BatchProcessor[T, R]:
    """Generic batch processor with checkpoint, retry, and parallelism.

    Processes a list of items using ThreadPoolExecutor with:
    - Partial-failure tolerance (exceptions stored in result dict)
    - tqdm progress bar
    - Exponential backoff retry
    - Optional checkpoint-based resume

    Parameters
    ----------
    process_fn : Callable[[T], R]
        Function to apply to each item. Receives a single item and
        returns the result. If it raises, the exception is captured.
    max_workers : int, default=5
        Maximum number of concurrent threads.
    max_retries : int, default=3
        Maximum number of retry attempts per item.
    base_delay : float, default=1.0
        Base delay in seconds for exponential backoff.

    Examples
    --------
    >>> processor = BatchProcessor(process_fn=lambda t: len(t), max_workers=3)
    >>> results = processor.process(["AAPL", "MSFT", "GOOG"])
    >>> results
    {'AAPL': 4, 'MSFT': 4, 'GOOG': 4}
    """

    def __init__(
        self,
        process_fn: Callable[[T], R],
        max_workers: int = 5,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        self._process_fn = process_fn
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._base_delay = base_delay

    def _retry_with_backoff(self, item: T) -> R:
        """Execute process_fn with exponential backoff retry.

        Parameters
        ----------
        item : T
            The item to process.

        Returns
        -------
        R
            The result of process_fn.

        Raises
        ------
        Exception
            The last exception if all retry attempts are exhausted.
        """
        last_exception: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return self._process_fn(item)
            except (ValueError, TypeError):
                raise  # Don't retry validation errors
            except Exception as exc:
                last_exception = exc
                if attempt < self._max_retries:
                    delay = self._base_delay * (2**attempt)
                    logger.debug(
                        "Retry scheduled",
                        attempt=attempt + 1,
                        max_retries=self._max_retries,
                        delay=delay,
                        error=str(exc),
                    )
                    time.sleep(delay)
        raise last_exception  # type: ignore[misc]

    def process(
        self,
        items: list[T],
        key_fn: Callable[[T], str] | None = None,
        desc: str = "Processing",
    ) -> dict[str, R | Exception]:
        """Process items in parallel with retry and partial-failure tolerance.

        Parameters
        ----------
        items : list[T]
            Items to process.
        key_fn : Callable[[T], str] | None, default=None
            Function to extract a string key from each item.
            If None, ``str(item)`` is used.
        desc : str, default="Processing"
            Description for the tqdm progress bar.

        Returns
        -------
        dict[str, R | Exception]
            Mapping of item keys to results or exceptions.
        """
        if key_fn is None:
            key_fn = str

        results: dict[str, R | Exception] = {}

        if not items:
            return results

        total = len(items)
        logger.debug(
            "Batch processing started",
            item_count=total,
            max_workers=self._max_workers,
        )

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_key = {
                executor.submit(self._retry_with_backoff, item): key_fn(item)
                for item in items
            }

            with tqdm(total=total, desc=desc) as pbar:
                for future in as_completed(future_to_key):
                    key = future_to_key[future]
                    try:
                        results[key] = future.result()
                    except Exception as exc:
                        results[key] = exc
                        logger.warning(
                            "Batch item failed after retries",
                            key=key,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        )
                    pbar.update(1)

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failed_count = total - success_count
        logger.debug(
            "Batch processing completed",
            success=success_count,
            failed=failed_count,
        )

        return results

    def process_with_checkpoint(
        self,
        items: list[T],
        key_fn: Callable[[T], str],
        checkpoint_path: Path,
        desc: str = "Processing",
        checkpoint_interval: int = 10,
    ) -> dict[str, R | Exception]:
        """Process items with checkpoint-based resume.

        Loads existing checkpoint, skips already-completed items,
        processes remaining items in chunks, and saves checkpoint
        after each chunk for crash recovery.

        Parameters
        ----------
        items : list[T]
            All items to process (including already-completed ones).
        key_fn : Callable[[T], str]
            Function to extract a string key from each item.
        checkpoint_path : Path
            Path to the checkpoint JSON file.
        desc : str, default="Processing"
            Description for the tqdm progress bar.
        checkpoint_interval : int, default=10
            Number of items to process before saving an intermediate
            checkpoint.  Smaller values provide better crash recovery
            at the cost of more disk I/O.

        Returns
        -------
        dict[str, R | Exception]
            Mapping of item keys to results (only newly processed items).
        """
        checkpoint = CheckpointManager(checkpoint_path)
        checkpoint.load()

        # Filter out already-completed items
        pending_items = [
            item for item in items if not checkpoint.is_completed(key_fn(item))
        ]

        skipped_count = len(items) - len(pending_items)
        if skipped_count > 0:
            logger.info(
                "Resuming from checkpoint",
                total=len(items),
                skipped=skipped_count,
                pending=len(pending_items),
            )

        # Process in chunks with intermediate checkpoint saves (PERF-002)
        all_results: dict[str, R | Exception] = {}

        for chunk_start in range(0, len(pending_items), checkpoint_interval):
            chunk = pending_items[chunk_start : chunk_start + checkpoint_interval]
            chunk_results = self.process(chunk, key_fn=key_fn, desc=desc)
            all_results.update(chunk_results)

            # Save intermediate checkpoint after each chunk
            for key, value in chunk_results.items():
                if not isinstance(value, Exception):
                    checkpoint.mark_completed(key)

            checkpoint.save()

        return all_results


__all__ = [
    "BatchProcessor",
    "CheckpointManager",
]
