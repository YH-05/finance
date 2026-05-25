"""File downloader for FRASER PDF / TXT assets.

This module exposes :class:`FraserDownloader`, a thread-safe helper for
streaming FRASER asset files to disk with atomic rename semantics. The
downloader uses standard-library primitives only (``tempfile``,
``pathlib``, ``threading``) and intentionally avoids external locking
libraries such as ``filelock`` — see PR1 HF1 review notes.

Key behaviours
--------------
- Stream downloads via ``httpx.stream`` so large PDFs do not load fully
  into memory.
- Write into ``tempfile.NamedTemporaryFile`` in the **same** target
  directory, then ``Path.replace()`` to ensure atomic publish on POSIX
  and Windows (same-volume requirement satisfied because the temp file
  lives next to the destination).
- Clean up the tmp file via ``finally`` so HTTP failures never leave
  ``*.tmp`` debris.
- Serialise concurrent downloads of the **same** ``item_id`` via an
  ``item_id``-keyed ``threading.Lock`` dictionary; different items run
  in parallel.

See Also
--------
market.fraser.session : Underlying :class:`FraserSession` used for HTTP.
market.fraser.errors : :class:`FraserDownloadError` raised on failure.
"""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path
from typing import IO, TYPE_CHECKING, Literal

import httpx

from market.fraser.errors import FraserDownloadError
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.fraser.models import FraserItem
    from market.fraser.session import FraserSession

logger = get_logger(__name__)

# Default download chunk size (bytes). 8 KiB matches Python's default
# socket read buffer and keeps memory pressure low.
_DEFAULT_CHUNK_SIZE: int = 8192

# Filename suffix used while the download is in progress. The suffix is
# only visible if a process dies between ``NamedTemporaryFile`` creation
# and ``Path.replace()``; ``finally`` cleanup removes it otherwise.
_TMP_SUFFIX: str = ".tmp"


class FraserDownloader:
    """Stream FRASER PDF / TXT assets to disk with atomic rename.

    Parameters
    ----------
    session : FraserSession
        Authenticated FRASER session. The downloader reuses the
        session's underlying ``httpx.Client`` so that polite delays and
        rate limiting still apply.
    base_dir : Path
        Filesystem root for downloads (default:
        ``Path("data/raw/fraser")``). All ``download_with_meta`` writes
        are placed under this root.
    chunk_size : int
        Stream chunk size in bytes (default: 8192). Exposed for testing.

    Examples
    --------
    >>> session = FraserSession()  # doctest: +SKIP
    >>> dl = FraserDownloader(session)  # doctest: +SKIP
    >>> dl.download(  # doctest: +SKIP
    ...     "https://fraser.stlouisfed.org/files/doc/1001.pdf",
    ...     Path("data/raw/fraser/fomc/minutes/2024-01-31_1001.pdf"),
    ... )
    """

    def __init__(
        self,
        session: FraserSession,
        base_dir: Path = Path("data/raw/fraser"),
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
    ) -> None:
        self._session: FraserSession = session
        self.base_dir: Path = Path(base_dir)
        self._chunk_size: int = chunk_size

        # Per-item locks (created lazily) plus a master lock that guards
        # the dict itself. This mirrors the standard "lock for the lock
        # registry" pattern used in concurrent caches.
        self._locks: dict[int, threading.Lock] = {}
        self._locks_master: threading.Lock = threading.Lock()

        logger.debug(
            "FraserDownloader initialised",
            base_dir=str(self.base_dir),
            chunk_size=self._chunk_size,
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def download(
        self,
        url: str,
        target_path: Path,
        *,
        force: bool = False,
    ) -> Path:
        """Stream ``url`` to ``target_path`` with atomic rename semantics.

        Skips the download entirely when ``target_path`` already exists
        and ``force`` is ``False``. Otherwise the bytes are streamed into
        a same-directory ``tempfile.NamedTemporaryFile`` and atomically
        published via ``Path.replace()`` on success.

        Parameters
        ----------
        url : str
            Source URL (must be an HTTPS FRASER URL — the session layer
            enforces this).
        target_path : Path
            Destination path on disk. Parent directories are created on
            demand.
        force : bool
            When ``True``, re-download even if the destination already
            exists.

        Returns
        -------
        Path
            The destination ``target_path``.

        Raises
        ------
        FraserDownloadError
            On any HTTP / I/O failure. The temporary file is always
            removed in the failure path.
        """
        target_path = Path(target_path)
        if target_path.exists() and not force:
            logger.debug(
                "Download skipped (exists, force=False)",
                target=str(target_path),
            )
            return target_path

        target_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=target_path.parent,
                delete=False,
                suffix=_TMP_SUFFIX,
                prefix=f"{target_path.stem}_",
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                self._stream_to(url, tmp_file)

            # Atomic publish (same-volume rename guaranteed by tmp dir).
            tmp_path.replace(target_path)
            logger.info(
                "Download succeeded",
                url=url,
                target=str(target_path),
                bytes=target_path.stat().st_size,
            )
            # ``tmp_path`` has been moved; suppress finally cleanup.
            tmp_path = None
            return target_path

        except FraserDownloadError:
            # Already a domain error from ``_stream_to`` — re-raise.
            raise
        except (OSError, httpx.HTTPError) as exc:
            logger.error(
                "Download failed",
                url=url,
                target=str(target_path),
                error=str(exc),
                exc_info=True,
            )
            raise FraserDownloadError(
                message=f"Failed to download {url}: {exc}",
                url=url,
                cause=exc,
            ) from exc
        finally:
            # ``tmp_path`` is None after a successful replace; otherwise
            # remove the residue so partial downloads never linger.
            if tmp_path is not None:
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError as cleanup_exc:
                    logger.warning(
                        "Failed to clean up temp file",
                        tmp_path=str(tmp_path),
                        error=str(cleanup_exc),
                    )

    def download_with_meta(
        self,
        item: FraserItem,
        doc_subdir: str,
        *,
        prefer: Literal["txt", "pdf"] = "txt",
        force: bool = False,
    ) -> tuple[Path, Path]:
        """Download an item's primary asset and write its metadata sidecar.

        Acquires the per-``item_id`` lock so that concurrent callers do
        not redundantly download the same item. Different items still
        run in parallel.

        Parameters
        ----------
        item : FraserItem
            Validated item model. Must have ``location`` populated with
            at least one URL matching ``prefer`` (or the fallback
            format).
        doc_subdir : str
            Subdirectory under :attr:`base_dir` (e.g.,
            ``"fomc/minutes"``).
        prefer : str
            Preferred format, ``"txt"`` or ``"pdf"``. The other format
            is used as fallback if the preferred is missing.
        force : bool
            Re-download even if the file already exists on disk.

        Returns
        -------
        tuple[Path, Path]
            ``(asset_path, metadata_path)``. The metadata sidecar is a
            JSON dump of the item model.

        Raises
        ------
        FraserDownloadError
            When the item has no usable URL or the download fails.
        """
        lock = self._get_or_create_lock(item.item_id)
        try:
            with lock:
                url, ext = self._select_url(item, prefer=prefer)

                target_dir = self.base_dir / doc_subdir
                asset_filename = f"{item.date.isoformat()}_{item.item_id}.{ext}"
                asset_path = target_dir / asset_filename
                meta_path = (
                    target_dir / f"{item.date.isoformat()}_{item.item_id}.meta.json"
                )

                self.download(url, asset_path, force=force)

                target_dir.mkdir(parents=True, exist_ok=True)
                meta_payload = item.model_dump_json(indent=2, by_alias=False)
                meta_path.write_text(meta_payload, encoding="utf-8")

                logger.debug(
                    "Meta sidecar written",
                    meta_path=str(meta_path),
                    item_id=item.item_id,
                )
                return asset_path, meta_path
        finally:
            # Release the per-item lock entry so a long-running batch does
            # not accumulate one Lock object per processed item_id.
            self._release_lock(item.item_id)

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _get_or_create_lock(self, item_id: int) -> threading.Lock:
        """Return the lock associated with ``item_id``, creating if needed.

        Parameters
        ----------
        item_id : int
            FRASER item identifier.

        Returns
        -------
        threading.Lock
            The per-item lock instance.
        """
        with self._locks_master:
            lock = self._locks.get(item_id)
            if lock is None:
                lock = threading.Lock()
                self._locks[item_id] = lock
            return lock

    def _release_lock(self, item_id: int) -> None:
        """Drop the per-``item_id`` lock entry after the download settles.

        Prevents unbounded growth of ``self._locks`` when a long-running
        batch processes many distinct items. Safe to call even when the
        entry is missing (no-op).
        """
        with self._locks_master:
            self._locks.pop(item_id, None)

    def _stream_to(self, url: str, tmp_file: IO[bytes]) -> None:
        """Stream ``url`` into the open ``tmp_file`` handle.

        Uses :meth:`FraserSession.stream` so the SSRF / HTTPS guards are
        enforced consistently with regular API calls (CWE-918). Status
        codes are checked via ``response.raise_for_status()`` before
        writing any bytes so that error pages are never persisted.

        Parameters
        ----------
        url : str
            Source URL.
        tmp_file : IO[bytes]
            Open writable binary file object (typically the handle
            returned by :class:`tempfile.NamedTemporaryFile`).

        Raises
        ------
        FraserValidationError
            If ``url`` fails SSRF / HTTPS validation.
        FraserDownloadError
            On HTTP / I/O failure.
        """
        try:
            with self._session.stream(url) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes(chunk_size=self._chunk_size):
                    if chunk:
                        tmp_file.write(chunk)
        except httpx.HTTPStatusError as exc:
            raise FraserDownloadError(
                message=(f"HTTP {exc.response.status_code} while downloading {url}"),
                url=url,
                cause=exc,
            ) from exc
        except httpx.HTTPError as exc:
            raise FraserDownloadError(
                message=f"HTTP error while downloading {url}: {exc}",
                url=url,
                cause=exc,
            ) from exc

    @staticmethod
    def _select_url(
        item: FraserItem, *, prefer: Literal["txt", "pdf"]
    ) -> tuple[str, str]:
        """Pick a URL from ``item.location`` honouring the ``prefer`` flag.

        Falls back to the other format when the preferred one is
        unavailable.

        Parameters
        ----------
        item : FraserItem
            Item whose ``location`` carries PDF / TXT URLs.
        prefer : str
            ``"txt"`` or ``"pdf"``.

        Returns
        -------
        tuple[str, str]
            ``(url, extension)``.

        Raises
        ------
        FraserDownloadError
            When the item has no URLs of either format.
        """
        if item.location is None:
            raise FraserDownloadError(
                message=f"Item {item.item_id} has no location",
                url="",
                cause=None,
            )

        txt_urls = item.location.text_url or []
        pdf_urls = item.location.pdf_url or []

        if prefer == "txt":
            if txt_urls:
                return txt_urls[0], "txt"
            if pdf_urls:
                return pdf_urls[0], "pdf"
        elif prefer == "pdf":
            if pdf_urls:
                return pdf_urls[0], "pdf"
            if txt_urls:
                return txt_urls[0], "txt"

        raise FraserDownloadError(
            message=(
                f"Item {item.item_id} has no usable URL "
                f"(prefer={prefer!r}, pdf={len(pdf_urls)}, txt={len(txt_urls)})"
            ),
            url="",
            cause=None,
        )


__all__ = ["FraserDownloader"]
