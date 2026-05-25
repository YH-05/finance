"""Property-based tests for ``market.fraser.downloader``.

Verifies the atomic-rename invariant that underpins
:meth:`FraserDownloader.download`:

- On success, ``target_path`` exists and equals the full concatenation
  of all streamed chunks.
- On failure, ``target_path`` does **not** exist and no ``*.tmp``
  residue is left in the destination directory.

Together these properties prove that callers never observe a partially
written file at the target location.

See Also
--------
market.fraser.downloader : Module under test.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from market.fraser.downloader import FraserDownloader
from market.fraser.errors import FraserDownloadError


def _unique_subdir(tmp_path: Path) -> Path:
    """Return a fresh, isolated sub-directory under ``tmp_path``.

    Hypothesis reuses the same ``tmp_path`` for every generated example
    (function-scoped fixtures are not reset between draws). Using a
    UUID-named sub-directory per call gives each example its own
    isolated workspace so leftover ``*.tmp`` glob scans never see
    files written by an earlier example.
    """
    sub = tmp_path / f"hyp_{uuid.uuid4().hex}"
    sub.mkdir(parents=True, exist_ok=True)
    return sub


# =============================================================================
# Test helpers
# =============================================================================


class _FakeStreamContext:
    """Minimal context manager mimicking ``httpx.Client.stream``."""

    def __init__(self, chunks: list[bytes], raise_at: int | None) -> None:
        self._chunks = chunks
        self._raise_at = raise_at

    def __enter__(self) -> "_FakeStreamContext":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_bytes(self, chunk_size: int = 8192) -> Any:
        for index, chunk in enumerate(self._chunks):
            if self._raise_at is not None and index >= self._raise_at:
                raise httpx.ReadError("simulated mid-stream failure")
            yield chunk


def _make_downloader(
    chunks: list[bytes],
    *,
    raise_at: int | None = None,
) -> FraserDownloader:
    """Build a :class:`FraserDownloader` with a stub session."""
    session = MagicMock()
    client = MagicMock()
    client.stream.return_value = _FakeStreamContext(chunks, raise_at)
    session._client = client
    return FraserDownloader(session=session)


def _residual_tmp_files(directory: Path, stem: str) -> list[Path]:
    """Return any ``*.tmp`` files matching the temp-file naming pattern."""
    return list(directory.glob(f"{stem}_*.tmp"))


# =============================================================================
# Property tests
# =============================================================================


class TestDownloadAtomicRenameProperty:
    """Atomic-rename invariant under varied chunk streams."""

    @given(
        chunks=st.lists(
            st.binary(min_size=1, max_size=1024),
            min_size=1,
            max_size=8,
        ),
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_プロパティ_成功時_target_pathが完全な内容を持つ(
        self,
        tmp_path: Path,
        chunks: list[bytes],
    ) -> None:
        """Successful download writes the exact concatenation of all chunks."""
        workspace = _unique_subdir(tmp_path)
        downloader = _make_downloader(chunks)
        target = workspace / "ok.bin"

        result = downloader.download(
            "https://fraser.stlouisfed.org/files/doc/x.bin", target
        )

        assert result == target
        assert target.exists()
        assert target.read_bytes() == b"".join(chunks)
        # No tmp residue lingers in the destination directory.
        assert _residual_tmp_files(workspace, target.stem) == []

    @given(
        chunks=st.lists(
            st.binary(min_size=1, max_size=1024),
            min_size=2,
            max_size=8,
        ),
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_プロパティ_途中失敗時_target_pathが存在しない(
        self,
        tmp_path: Path,
        chunks: list[bytes],
    ) -> None:
        """A mid-stream failure leaves no target file and no tmp residue."""
        workspace = _unique_subdir(tmp_path)
        # Raise mid-stream so the rename never happens.
        raise_at = max(1, len(chunks) // 2)
        downloader = _make_downloader(chunks, raise_at=raise_at)
        target = workspace / "broken.bin"

        with pytest.raises(FraserDownloadError):
            downloader.download("https://fraser.stlouisfed.org/files/doc/x.bin", target)

        assert not target.exists()
        # No partial ``*.tmp`` residue in the destination directory.
        assert _residual_tmp_files(workspace, target.stem) == []


class TestDownloadSkipExistingProperty:
    """``force=False`` should skip download whenever target already exists."""

    @given(
        existing_bytes=st.binary(min_size=0, max_size=64),
        chunks=st.lists(st.binary(min_size=1, max_size=32), min_size=1, max_size=4),
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_プロパティ_既存ファイル_force_Falseで書き換えなし(
        self,
        tmp_path: Path,
        existing_bytes: bytes,
        chunks: list[bytes],
    ) -> None:
        workspace = _unique_subdir(tmp_path)
        target = workspace / "preexisting.bin"
        target.write_bytes(existing_bytes)

        client = MagicMock()
        client.stream = MagicMock(
            side_effect=AssertionError("should not be called when force=False"),
        )
        session = MagicMock()
        session._client = client
        downloader = FraserDownloader(session=session)

        result = downloader.download(
            "https://fraser.stlouisfed.org/files/doc/x.bin",
            target,
            force=False,
        )

        assert result == target
        assert target.read_bytes() == existing_bytes
        # The mocked client must NEVER have been touched.
        client.stream.assert_not_called()


# =============================================================================
# Mid-stream-failure cleanup property (additional safety guard)
# =============================================================================


class TestDownloadCleanupOnUnlinkErrorProperty:
    """Even when ``unlink`` fails, the call still raises FraserDownloadError."""

    @given(
        chunks=st.lists(st.binary(min_size=1, max_size=32), min_size=2, max_size=4),
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_プロパティ_途中失敗_unlink失敗でもFraserDownloadError(
        self,
        tmp_path: Path,
        chunks: list[bytes],
    ) -> None:
        """A unlink() OSError in finally must not mask the FraserDownloadError."""
        workspace = _unique_subdir(tmp_path)
        downloader = _make_downloader(chunks, raise_at=1)
        target = workspace / "broken.bin"

        original_unlink = Path.unlink

        def _flaky_unlink(self: Path, missing_ok: bool = False) -> None:
            # Only break temp files; keep regular unlinks working.
            if self.suffix == ".tmp":
                raise OSError("simulated unlink failure")
            original_unlink(self, missing_ok=missing_ok)

        with (
            patch.object(Path, "unlink", _flaky_unlink),
            pytest.raises(FraserDownloadError),
        ):
            downloader.download("https://fraser.stlouisfed.org/files/doc/x.bin", target)

        # target_path still must not exist (rename never happened).
        assert not target.exists()
