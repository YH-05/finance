"""REGIME_SWITCHING 実験用の共通ユーティリティ.

データ取得・前処理・可視化の関数を提供する。notebook からは
``from _helpers import ...`` で参照する。
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# パス定数
# ---------------------------------------------------------------------------

PKG_DIR: Path = Path(__file__).resolve().parent
REPO_ROOT: Path = PKG_DIR.parent.parent
DATA_DIR: Path = PKG_DIR / "data"

FRED_WEEKLY_RAW_PARQUET: Path = DATA_DIR / "fred_weekly_raw.parquet"
FEATURES_WEEKLY_PARQUET: Path = DATA_DIR / "features_weekly.parquet"
SP500_WEEKLY_PARQUET: Path = DATA_DIR / "sp500_weekly.parquet"

# ---------------------------------------------------------------------------
# FRED 系列定義
# ---------------------------------------------------------------------------

FRED_SERIES_IDS: list[str] = [
    "INDPRO",
    "ICSA",
    "T10YIE",
    "CPIAUCSL",
    "STLFSI4",
    "BAA10Y",
    "T10Y2Y",
]

# 分析開始日（STLFSI4 と T10YIE が両方揃う時点）
DEFAULT_START_DATE: str = "2003-12-01"
