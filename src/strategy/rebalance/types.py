"""Type definitions for the rebalance module.

This module contains data classes and type definitions used by
the rebalance module for drift detection and rebalancing analysis.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DriftResult:
    """配分ドリフトの分析結果.

    ポートフォリオの現在の配分と目標配分との差異を表す。
    frozen=True により不変オブジェクトとして扱われる。

    Parameters
    ----------
    ticker : str
        ティッカーシンボル
    target_weight : float
        目標配分比率（0.0 - 1.0）
    current_weight : float
        現在の配分比率（0.0 - 1.0）
    drift : float
        乖離幅（current_weight - target_weight）
    drift_percent : float
        乖離率（drift / target_weight * 100）
        target_weight が 0 の場合は inf または -inf
    requires_rebalance : bool
        リバランス推奨フラグ
        閾値を超えた場合に True

    Examples
    --------
    >>> result = DriftResult(
    ...     ticker="VOO",
    ...     target_weight=0.6,
    ...     current_weight=0.65,
    ...     drift=0.05,
    ...     drift_percent=8.33,
    ...     requires_rebalance=True,
    ... )
    >>> result.ticker
    'VOO'
    >>> result.requires_rebalance
    True
    """

    ticker: str
    target_weight: float
    current_weight: float
    drift: float
    drift_percent: float
    requires_rebalance: bool
