"""REGIME_SWITCHING 実験用の共通ユーティリティ.

データ取得・前処理・可視化の関数を提供する。notebook からは
``from _helpers import ...`` で参照する。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from market.fred import HistoricalCache
from utils_core.logging import get_logger

logger = get_logger(__name__, module="regime_switching.helpers")

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


def load_fred_weekly(
    start: str = DEFAULT_START_DATE,
    series_ids: list[str] | None = None,
    cache: HistoricalCache | None = None,
) -> pd.DataFrame:
    """FRED の指定系列を取得し W-FRI 週次に揃えた DataFrame を返す.

    Parameters
    ----------
    start : str
        分析開始日 (YYYY-MM-DD).
    series_ids : list[str] | None
        取得する FRED series ID のリスト. None なら ``FRED_SERIES_IDS`` 全件.
    cache : HistoricalCache | None
        テスト時に差し替え可能. None なら新規生成.

    Returns
    -------
    pd.DataFrame
        インデックスが週末金曜の DatetimeIndex、各列が FRED 系列値.
    """
    ids = list(series_ids) if series_ids is not None else list(FRED_SERIES_IDS)
    cache = cache if cache is not None else HistoricalCache()

    series_frames: dict[str, pd.DataFrame] = {}
    for sid in ids:
        logger.info("Loading FRED series", series_id=sid)
        result = cache.sync_series(sid)
        if not result.get("success", False):
            logger.warning(
                "FRED sync failed; using existing cache if available",
                series_id=sid,
                error=result.get("error"),
            )
        df = cache.get_series_df(sid)
        if df is None:
            raise RuntimeError(f"FRED series {sid} could not be loaded from cache")
        series_frames[sid] = df

    # 全系列を W-FRI に揃える: 週末金曜の最終値を取り、月次系列は ffill で埋める
    aligned: dict[str, pd.Series] = {}
    for sid, df in series_frames.items():
        weekly = df["value"].resample("W-FRI").last().ffill()
        aligned[sid] = weekly

    combined = pd.concat(aligned, axis=1)
    combined.columns = list(aligned.keys())
    combined = combined.loc[combined.index >= pd.Timestamp(start)]
    combined = combined.dropna(how="any")  # 全系列が揃う週のみ残す

    logger.info(
        "FRED weekly data loaded",
        n_rows=len(combined),
        date_range=[str(combined.index.min().date()), str(combined.index.max().date())],
    )
    return combined
