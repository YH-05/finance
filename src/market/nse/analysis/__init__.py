"""NSE universe analysis utilities.

This subpackage contains analysis functions for NSE investment universe
snapshots, such as detecting membership changes between two universe
DataFrames (index reconstitution diffing) and detecting promoter
shareholding drift that warrants re-running owner classification.

Public API
----------
UniverseDiff
    Result of comparing two universe snapshots (added/removed/unchanged).
diff_universe
    Compare two universe DataFrames and detect symbol-level changes.
STAGE1_PROMOTER_THRESHOLD_PCT
    SEBI (SAST) Regulations 2011, Reg 3 の支配的取得閾値（Owner Stage1 判定）。
detect_promoter_drift
    Detect symbols whose promoter_pct changed enough to require owner
    re-classification.
"""

from market.nse.analysis.promoter_drift import (
    STAGE1_PROMOTER_THRESHOLD_PCT,
    detect_promoter_drift,
)
from market.nse.analysis.universe_diff import UniverseDiff, diff_universe

__all__ = [
    "STAGE1_PROMOTER_THRESHOLD_PCT",
    "UniverseDiff",
    "detect_promoter_drift",
    "diff_universe",
]
