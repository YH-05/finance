"""Promoter shareholding drift detection for the NSE owner-classification pipeline.

This module compares the two most recent quarterly ``shareholdings`` rows
per symbol and flags symbols whose ``promoter_pct`` has moved enough to
warrant re-running the owner-company classification (Stage1〜3 in
``notebook/NSE/scripts/build_owner_review_sheet.py`` /
``build_nifty750_universe.py``). It reads only from the already-cached
``shareholdings`` table — no NSE API calls are made.

``shareholdings.as_on_date`` is stored as ``"DD-MMM-YYYY"`` text, so a naive
``ORDER BY as_on_date`` / ``MAX(as_on_date)`` performs a lexicographic string
comparison and misorders dates across months (e.g. ``"31-MAR-2025"`` sorts
after ``"31-DEC-2025"`` because ``"M" > "D"``). This module converts
``as_on_date`` to an ISO ``YYYY-MM-DD`` string before ranking, following the
same ``sh_iso`` CTE pattern used in the Phase 4 cell of
``notebook/NSE/nse_full_download.ipynb``.

See Also
--------
market.nse.collectors.share_holding.ShareholdingCollector : Source of the
    ``shareholdings`` rows via ``fetch_shareholding()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from utils_core.logging import get_logger

if TYPE_CHECKING:
    import sqlite3

logger = get_logger(__name__)

STAGE1_PROMOTER_THRESHOLD_PCT: float = 10.0
"""SEBI (SAST) Regulations 2011, Reg 3 の支配的取得閾値。

Owner 確定の必要条件（Stage1）として使われる promoter 保有比率の閾値。
``notebook/NSE/scripts/build_nifty750_universe.py`` の
``stage1_promoter_ge_10`` と同一の閾値。
"""

_DRIFT_QUERY = """
WITH sh_iso AS (
    SELECT
        sh.symbol,
        sh.as_on_date,
        sh.promoter_pct,
        substr(sh.as_on_date, -4) || '-'
        || CASE substr(sh.as_on_date, 4, 3)
               WHEN 'JAN' THEN '01' WHEN 'FEB' THEN '02' WHEN 'MAR' THEN '03'
               WHEN 'APR' THEN '04' WHEN 'MAY' THEN '05' WHEN 'JUN' THEN '06'
               WHEN 'JUL' THEN '07' WHEN 'AUG' THEN '08' WHEN 'SEP' THEN '09'
               WHEN 'OCT' THEN '10' WHEN 'NOV' THEN '11' WHEN 'DEC' THEN '12'
               ELSE '00'
           END
        || '-' || substr(sh.as_on_date, 1, 2) AS iso_date
    FROM shareholdings sh
),
ranked AS (
    SELECT
        symbol,
        as_on_date,
        promoter_pct,
        iso_date,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY iso_date DESC) AS rn
    FROM sh_iso
)
SELECT
    latest.symbol AS symbol,
    previous.as_on_date AS previous_as_on_date,
    latest.as_on_date AS latest_as_on_date,
    previous.promoter_pct AS previous_promoter_pct,
    latest.promoter_pct AS latest_promoter_pct
FROM ranked AS latest
JOIN ranked AS previous
    ON previous.symbol = latest.symbol AND previous.rn = 2
WHERE latest.rn = 1
ORDER BY latest.symbol
"""


def detect_promoter_drift(
    conn: sqlite3.Connection, threshold_pct: float = 1.0
) -> pd.DataFrame:
    """前回時点と比較して promoter 比率が変化した銘柄を検出する.

    銘柄ごとに ``shareholdings`` の直近2時点（最新・その前）を比較し、
    以下いずれかを満たす銘柄をオーナー判定の再実行対象として抽出する。

    1. ``abs(latest_promoter_pct - previous_promoter_pct) >= threshold_pct``
    2. ``STAGE1_PROMOTER_THRESHOLD_PCT`` (10%) を跨いだ場合（変化量が
       ``threshold_pct`` 未満でも対象。Owner 判定そのものが反転しうるため）

    直近データが1件のみの銘柄（比較対象なし）、および直近2時点のいずれかで
    ``promoter_pct`` が NULL の銘柄（比較不能）は結果から除外する。

    Parameters
    ----------
    conn : sqlite3.Connection
        ``shareholdings`` テーブルを持つ SQLite 接続
        （例: ``notebook/NSE/data/cache/nse/nse_index.db``）。
    threshold_pct : float, default 1.0
        変化ありと判定する promoter_pct 差分の閾値（パーセントポイント）。

    Returns
    -------
    pd.DataFrame
        変化ありと判定された銘柄のみを含む DataFrame。列は
        ``symbol``, ``previous_as_on_date``, ``latest_as_on_date``,
        ``previous_promoter_pct``, ``latest_promoter_pct``, ``pct_change``,
        ``crossed_stage1_threshold`` (bool)。該当銘柄が無い場合は空の
        DataFrame（列構成のみ保持）を返す。

    Examples
    --------
    >>> import sqlite3
    >>> conn = sqlite3.connect("notebook/NSE/data/cache/nse/nse_index.db")
    >>> drift = detect_promoter_drift(conn, threshold_pct=1.0)
    >>> drift[["symbol", "pct_change", "crossed_stage1_threshold"]]  # doctest: +SKIP
    """
    logger.debug("Detecting promoter drift", threshold_pct=threshold_pct)

    raw = pd.read_sql_query(_DRIFT_QUERY, conn)
    logger.debug("Fetched comparable symbols", symbol_count=len(raw))

    valid = raw["latest_promoter_pct"].notna() & raw["previous_promoter_pct"].notna()
    pct_change = (raw["latest_promoter_pct"] - raw["previous_promoter_pct"]).where(
        valid
    )

    previous_is_owner = raw["previous_promoter_pct"] >= STAGE1_PROMOTER_THRESHOLD_PCT
    latest_is_owner = raw["latest_promoter_pct"] >= STAGE1_PROMOTER_THRESHOLD_PCT
    crossed_stage1_threshold = valid & (previous_is_owner != latest_is_owner)

    changed = valid & ((pct_change.abs() >= threshold_pct) | crossed_stage1_threshold)

    result = raw.loc[
        changed,
        [
            "symbol",
            "previous_as_on_date",
            "latest_as_on_date",
            "previous_promoter_pct",
            "latest_promoter_pct",
        ],
    ].copy()
    result["pct_change"] = pct_change.loc[changed]
    result["crossed_stage1_threshold"] = crossed_stage1_threshold.loc[changed]
    result = result.reset_index(drop=True)

    logger.info(
        "Promoter drift detection completed",
        symbol_count=len(result),
        threshold_pct=threshold_pct,
    )
    return result


__all__ = ["STAGE1_PROMOTER_THRESHOLD_PCT", "detect_promoter_drift"]
