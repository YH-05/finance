"""REGIME_SWITCHING/_helpers.py の単体テスト."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_helpers():
    """notebook/REGIME_SWITCHING/_helpers.py をモジュールとしてロード."""
    here = Path(__file__).resolve()
    repo_root = (
        here.parent.parent.parent.parent
    )  # tests/notebook/regime_switching/ → repo
    helpers_path = repo_root / "notebook" / "REGIME_SWITCHING" / "_helpers.py"
    spec = importlib.util.spec_from_file_location("regime_helpers", helpers_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestModuleConstants:
    def test_PKG_DIR_は_REGIME_SWITCHING_ディレクトリを指す(self) -> None:
        helpers = _load_helpers()
        assert helpers.PKG_DIR.name == "REGIME_SWITCHING"
        assert helpers.PKG_DIR.is_dir()

    def test_DATA_DIR_は_PKG_DIR_配下の_data(self) -> None:
        helpers = _load_helpers()
        assert helpers.DATA_DIR == helpers.PKG_DIR / "data"

    def test_FRED_SERIES_IDS_は7系列を含む(self) -> None:
        helpers = _load_helpers()
        expected = {
            "INDPRO",
            "ICSA",
            "T10YIE",
            "CPIAUCSL",
            "STLFSI4",
            "BAA10Y",
            "T10Y2Y",
        }
        assert set(helpers.FRED_SERIES_IDS) == expected
