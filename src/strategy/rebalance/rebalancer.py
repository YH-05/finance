"""Rebalancer class for portfolio drift detection and rebalancing analysis.

This module provides the Rebalancer class which detects portfolio drift,
calculates rebalancing costs, and provides timing analysis for rebalancing.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from strategy.errors import NormalizationWarning, ValidationError
from strategy.rebalance.types import DriftResult

if TYPE_CHECKING:
    from strategy.portfolio import Portfolio


# AIDEV-NOTE: 遅延初期化でロガーを取得（循環インポート回避）
def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from strategy.utils.logging_config import get_logger

        return get_logger(__name__, module="rebalancer")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class Rebalancer:
    """リバランス分析クラス.

    ポートフォリオの配分ドリフト検出、コスト計算、
    タイミング分析を提供する。

    Parameters
    ----------
    portfolio : Portfolio
        分析対象のポートフォリオ

    Attributes
    ----------
    portfolio : Portfolio
        分析対象のポートフォリオ

    Examples
    --------
    >>> from strategy import Portfolio
    >>> portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])
    >>> rebalancer = Rebalancer(portfolio)
    >>> drift = rebalancer.detect_drift(
    ...     target_weights={"VOO": 0.6, "BND": 0.4}
    ... )
    """

    # AIDEV-NOTE: 重み合計の許容誤差
    _WEIGHT_TOLERANCE = 1e-9

    def __init__(self, portfolio: Portfolio) -> None:
        """Initialize Rebalancer with a portfolio.

        Parameters
        ----------
        portfolio : Portfolio
            分析対象のポートフォリオ
        """
        logger.debug(
            "Creating Rebalancer",
            portfolio_name=portfolio.name,
            holdings_count=len(portfolio),
        )

        self._portfolio = portfolio

        logger.info(
            "Rebalancer created",
            portfolio_name=portfolio.name,
            tickers=portfolio.tickers,
        )

    @property
    def portfolio(self) -> Portfolio:
        """分析対象のポートフォリオを返す.

        Returns
        -------
        Portfolio
            分析対象のポートフォリオ
        """
        return self._portfolio

    def detect_drift(
        self,
        target_weights: dict[str, float],
        threshold: float = 0.05,
    ) -> list[DriftResult]:
        """配分ドリフトを検出.

        現在のポートフォリオの配分と目標配分との差異を計算し、
        各銘柄のドリフト結果を返す。

        Parameters
        ----------
        target_weights : dict[str, float]
            目標配分比率（ティッカー -> 比率）
        threshold : float, default=0.05
            リバランス推奨の閾値（絶対値、デフォルト: 0.05 = 5%）
            ドリフトの絶対値がこの閾値以上の場合、
            requires_rebalance が True になる

        Returns
        -------
        list[DriftResult]
            各銘柄のドリフト分析結果

        Raises
        ------
        ValidationError
            target_weights が空の場合
        ValueError
            target_weights にポートフォリオにない銘柄が含まれる場合

        Examples
        --------
        >>> rebalancer = Rebalancer(Portfolio([("VOO", 0.65), ("BND", 0.35)]))
        >>> results = rebalancer.detect_drift(
        ...     target_weights={"VOO": 0.6, "BND": 0.4},
        ...     threshold=0.05,
        ... )
        >>> for r in results:
        ...     print(f"{r.ticker}: drift={r.drift:.2%}")
        VOO: drift=5.00%
        BND: drift=-5.00%
        """
        logger.debug(
            "Detecting drift",
            target_weights=target_weights,
            threshold=threshold,
            portfolio_tickers=self._portfolio.tickers,
        )

        # Validate target_weights
        if not target_weights:
            logger.error("target_weights is empty")
            msg = "target_weights cannot be empty"
            raise ValidationError(msg, code="REBALANCER_001")

        # Check for unknown tickers
        portfolio_tickers = set(self._portfolio.tickers)
        target_tickers = set(target_weights.keys())
        unknown_tickers = target_tickers - portfolio_tickers

        if unknown_tickers:
            logger.error(
                "Unknown tickers in target_weights",
                unknown_tickers=list(unknown_tickers),
                portfolio_tickers=list(portfolio_tickers),
            )
            msg = f"Tickers {unknown_tickers} not in portfolio"
            raise ValueError(msg)

        # Warn if target weights don't sum to 1.0
        total_target_weight = sum(target_weights.values())
        if abs(total_target_weight - 1.0) > self._WEIGHT_TOLERANCE:
            logger.warning(
                "Target weights do not sum to 1.0",
                total_target_weight=total_target_weight,
                difference=total_target_weight - 1.0,
            )
            warnings.warn(
                f"sum of target_weights ({total_target_weight:.6f}) does not equal 1.0",
                NormalizationWarning,
                stacklevel=2,
            )

        # Get current weights
        current_weights = self._portfolio.weights

        # Calculate drift for each ticker in target_weights
        results: list[DriftResult] = []

        for ticker, target_weight in target_weights.items():
            current_weight = current_weights.get(ticker, 0.0)

            # Calculate drift
            drift = current_weight - target_weight

            # Calculate drift percent
            if abs(target_weight) > self._WEIGHT_TOLERANCE:
                drift_percent = (drift / target_weight) * 100
            # target_weight is 0, handle division by zero
            elif drift > 0:
                drift_percent = float("inf")
            elif drift < 0:
                drift_percent = float("-inf")
            else:
                drift_percent = 0.0

            # Determine if rebalance is required
            requires_rebalance = abs(drift) >= threshold

            result = DriftResult(
                ticker=ticker,
                target_weight=target_weight,
                current_weight=current_weight,
                drift=drift,
                drift_percent=drift_percent,
                requires_rebalance=requires_rebalance,
            )
            results.append(result)

            logger.debug(
                "Drift calculated for ticker",
                ticker=ticker,
                target_weight=target_weight,
                current_weight=current_weight,
                drift=drift,
                drift_percent=drift_percent,
                requires_rebalance=requires_rebalance,
            )

        logger.info(
            "Drift detection completed",
            total_tickers=len(results),
            rebalance_needed_count=sum(1 for r in results if r.requires_rebalance),
        )

        return results
