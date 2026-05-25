"""Tests for ``market.fraser.downloader`` module.

Verifies :class:`FraserDownloader` behaviour:

- ``tempfile.NamedTemporaryFile`` + ``Path.replace()`` atomic publish.
- Failed downloads do not leave ``*.tmp`` residue.
- ``item_id``-keyed ``threading.Lock`` prevents duplicate concurrent
  downloads of the same item (single HTTP call observed).
- ``download_with_meta`` writes both the asset file and the JSON
  metadata sidecar.

See Also
--------
market.fraser.downloader : Module under test.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from market.fraser.downloader import FraserDownloader
from market.fraser.errors import FraserDownloadError
from market.fraser.models import FraserItem

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_session_with_stream(
    *,
    chunks: list[bytes] | None = None,
    status_code: int = 200,
    raise_http_status: bool = False,
) -> MagicMock:
    """Return a MagicMock FraserSession whose ``_client.stream`` is controlled.

    ``_client`` is exposed as a private attribute on the real session;
    the downloader accesses it via ``session._client``.
    """
    session = MagicMock()
    client = MagicMock()
    session._client = client

    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.iter_bytes.return_value = iter(chunks or [])
    if raise_http_status:
        # Simulate ``response.raise_for_status()`` raising on 4xx/5xx.
        request = httpx.Request("GET", "https://fraser.stlouisfed.org/x")
        real_response = httpx.Response(status_code, request=request)
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=request, response=real_response
        )
    else:
        response.raise_for_status.return_value = None

    @contextmanager
    def _stream(method: str, url: str, **_: Any) -> Any:
        yield response

    client.stream.side_effect = _stream
    return session


def _make_item(
    item_id: int = 1001,
    *,
    pdf: bool = True,
    txt: bool = True,
) -> FraserItem:
    location: dict[str, list[str]] = {}
    if pdf:
        location["pdfUrl"] = [f"https://fraser.stlouisfed.org/files/{item_id}.pdf"]
    if txt:
        location["textUrl"] = [f"https://fraser.stlouisfed.org/files/{item_id}.txt"]
    payload: dict[str, Any] = {
        "itemId": item_id,
        "titleId": 677,
        "title": f"Item {item_id}",
        "date": "2024-01-31",
    }
    if location:
        payload["location"] = location
    return FraserItem.model_validate(payload)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestFraserDownloaderInit:
    def test_正常系_デフォルトbase_dir(self) -> None:
        session = MagicMock()
        dl = FraserDownloader(session)
        assert dl.base_dir == Path("data/raw/fraser")

    def test_正常系_カスタムbase_dir(self, tmp_path: Path) -> None:
        session = MagicMock()
        dl = FraserDownloader(session, base_dir=tmp_path / "fraser")
        assert dl.base_dir == tmp_path / "fraser"


# ---------------------------------------------------------------------------
# download() - atomic rename
# ---------------------------------------------------------------------------


class TestDownloadAtomic:
    def test_正常系_tempfileとPathReplaceでatomic書き込み(self, tmp_path: Path) -> None:
        chunks = [b"hello ", b"world"]
        session = _build_session_with_stream(chunks=chunks)
        dl = FraserDownloader(session, base_dir=tmp_path)

        target = tmp_path / "out" / "doc.txt"
        result = dl.download("https://fraser.stlouisfed.org/x.txt", target)

        assert result == target
        assert target.exists()
        assert target.read_bytes() == b"hello world"
        # No leftover .tmp files in the target directory.
        residual = list(target.parent.glob("*.tmp"))
        assert residual == []

    def test_正常系_targetが既存ならスキップ(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(chunks=[b"new"])
        dl = FraserDownloader(session, base_dir=tmp_path)

        target = tmp_path / "exists.txt"
        target.write_bytes(b"original")

        result = dl.download("https://fraser.stlouisfed.org/x.txt", target)
        assert result == target
        # Content remains unchanged.
        assert target.read_bytes() == b"original"
        # Streaming client was never called.
        session._client.stream.assert_not_called()

    def test_正常系_force_Trueで上書き(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(chunks=[b"new"])
        dl = FraserDownloader(session, base_dir=tmp_path)

        target = tmp_path / "exists.txt"
        target.write_bytes(b"original")

        dl.download("https://fraser.stlouisfed.org/x.txt", target, force=True)
        assert target.read_bytes() == b"new"

    def test_異常系_HTTP500でtmpファイルが残らない(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(
            chunks=[b"err"], status_code=500, raise_http_status=True
        )
        dl = FraserDownloader(session, base_dir=tmp_path)

        target = tmp_path / "out" / "doc.txt"
        with pytest.raises(FraserDownloadError):
            dl.download("https://fraser.stlouisfed.org/x.txt", target)

        # Target was never created and the .tmp file was cleaned up.
        assert not target.exists()
        residual = list((tmp_path / "out").glob("*.tmp"))
        assert residual == []

    def test_異常系_httpx_NetworkErrorでtmp清掃(self, tmp_path: Path) -> None:
        session = MagicMock()
        client = MagicMock()
        session._client = client

        @contextmanager
        def _stream(method: str, url: str, **_: Any) -> Any:
            raise httpx.ConnectError("network down")
            yield  # pragma: no cover

        client.stream.side_effect = _stream
        dl = FraserDownloader(session, base_dir=tmp_path)

        target = tmp_path / "out" / "doc.txt"
        with pytest.raises(FraserDownloadError):
            dl.download("https://fraser.stlouisfed.org/x.txt", target)
        assert not target.exists()
        residual = (
            list((tmp_path / "out").glob("*.tmp"))
            if (tmp_path / "out").exists()
            else []
        )
        assert residual == []


# ---------------------------------------------------------------------------
# Lock-based deduplication
# ---------------------------------------------------------------------------


class TestParallelDeduplication:
    def test_正常系_同一item_idの並列DLでhttp呼び出しが1回(
        self, tmp_path: Path
    ) -> None:
        # Configure the mock session so each ``stream`` call returns a
        # fresh response with the same bytes. We count how many times
        # ``stream`` is invoked across two threads using the same item.
        call_count = {"value": 0}
        call_lock = threading.Lock()

        session = MagicMock()
        client = MagicMock()
        session._client = client

        @contextmanager
        def _stream(method: str, url: str, **_: Any) -> Any:
            with call_lock:
                call_count["value"] += 1
            response = MagicMock(spec=httpx.Response)
            response.status_code = 200
            response.iter_bytes.return_value = iter([b"payload"])
            response.raise_for_status.return_value = None
            yield response

        client.stream.side_effect = _stream

        dl = FraserDownloader(session, base_dir=tmp_path)
        item = _make_item(item_id=1001, txt=True, pdf=False)

        def _worker() -> None:
            dl.download_with_meta(item, "fomc/minutes", prefer="txt")

        threads = [threading.Thread(target=_worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The second download must skip because the file exists after
        # the first call → exactly one HTTP stream invocation.
        assert call_count["value"] == 1

        target = (
            tmp_path
            / "fomc"
            / "minutes"
            / f"{item.date.isoformat()}_{item.item_id}.txt"
        )
        assert target.exists()

    def test_正常系_異なるitem_idは別ロック(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(chunks=[b"data"])
        dl = FraserDownloader(session, base_dir=tmp_path)
        lock_a = dl._get_or_create_lock(1001)
        lock_b = dl._get_or_create_lock(1002)
        assert lock_a is not lock_b

    def test_正常系_同一item_idは同じロックを返す(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(chunks=[b"data"])
        dl = FraserDownloader(session, base_dir=tmp_path)
        first = dl._get_or_create_lock(2002)
        second = dl._get_or_create_lock(2002)
        assert first is second


# ---------------------------------------------------------------------------
# download_with_meta
# ---------------------------------------------------------------------------


class TestDownloadWithMeta:
    def test_正常系_metaサイドカーが書き出される(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(chunks=[b"body"])
        dl = FraserDownloader(session, base_dir=tmp_path)
        item = _make_item(item_id=3003)

        asset_path, meta_path = dl.download_with_meta(
            item, "fomc/minutes", prefer="txt"
        )
        assert asset_path.exists()
        assert asset_path.suffix == ".txt"
        assert meta_path.exists()
        assert meta_path.suffix == ".json"
        meta_text = meta_path.read_text(encoding="utf-8")
        assert "3003" in meta_text

    def test_正常系_preferpdfで拡張子pdf(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(chunks=[b"pdf bytes"])
        dl = FraserDownloader(session, base_dir=tmp_path)
        item = _make_item(item_id=4004)
        asset_path, _ = dl.download_with_meta(item, "fomc/minutes", prefer="pdf")
        assert asset_path.suffix == ".pdf"

    def test_正常系_preferが欠落しているとフォールバック(self, tmp_path: Path) -> None:
        # prefer='txt' but only pdf is available -> falls back to pdf.
        session = _build_session_with_stream(chunks=[b"pdf only"])
        dl = FraserDownloader(session, base_dir=tmp_path)
        item = _make_item(item_id=5005, txt=False, pdf=True)
        asset_path, _ = dl.download_with_meta(item, "fomc/minutes", prefer="txt")
        assert asset_path.suffix == ".pdf"

    def test_異常系_locationなしで例外(self, tmp_path: Path) -> None:
        session = _build_session_with_stream(chunks=[b"x"])
        dl = FraserDownloader(session, base_dir=tmp_path)
        item = _make_item(item_id=6006, txt=False, pdf=False)
        with pytest.raises(FraserDownloadError):
            dl.download_with_meta(item, "fomc/minutes", prefer="txt")
