"""Phase 4 portfolio construction for the CA Strategy pipeline.

Builds a portfolio from ranked stock scores and benchmark sector weights.
Sector allocation follows the benchmark; intra-sector weights are
score-proportional.

Algorithm
---------
1. For each benchmark sector, compute target stock count:
   ``count = round(target_size * sector_weight)``
2. Select the top-N stocks by aggregate_score within each sector
3. Assign intra-sector weights proportional to each stock's score
4. Scale intra-sector weights so total sector weight matches benchmark
5. Normalize all weights to sum to 1.0

Output
------
Returns a PortfolioResult with:
- ``holdings``: list[PortfolioHolding]
- ``sector_allocations``: list[SectorAllocation]
- ``as_of_date``: date
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date  # noqa: TC003 - required at runtime
from typing import TypedDict

from utils_core.logging import get_logger

from .types import BenchmarkWeight, PortfolioHolding, PortfolioResult, SectorAllocation


class RankedStock(TypedDict):
    """Type definition for a ranked stock entry from SectorNeutralizer output.

    Attributes
    ----------
    ticker : str
        Ticker symbol (e.g. "AAPL").
    aggregate_score : float
        Aggregate score in [0.0, 1.0] computed by ScoreAggregator.
    gics_sector : str
        GICS sector classification (e.g. "Information Technology").
    sector_rank : int
        Within-sector rank after sector neutralization (1 = highest Z-score).
    claim_count : int
        Number of scored claims contributing to aggregate_score. Must be >= 0.
    structural_weight : float
        Fraction of competitive_advantage claims in [0.0, 1.0].
    """

    ticker: str
    aggregate_score: float
    gics_sector: str
    sector_rank: int
    claim_count: int
    structural_weight: float


logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_TARGET_SIZE: int = 30
"""Default number of stocks in the portfolio."""

_MIN_STOCKS_PER_SECTOR: int = 1
"""Minimum number of stocks per sector (if sector has any candidates)."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
class PortfolioBuilder:
    """Build a portfolio from ranked stock scores and benchmark weights.

    Parameters
    ----------
    target_size : int, default=30
        Target number of stocks in the portfolio.

    Examples
    --------
    >>> builder = PortfolioBuilder(target_size=30)
    >>> result = builder.build(ranked, benchmark, date(2015, 9, 30))
    >>> sum(h.weight for h in result.holdings)
    1.0
    """

    def __init__(self, target_size: int = _DEFAULT_TARGET_SIZE) -> None:
        self._target_size = target_size
        logger.debug("PortfolioBuilder initialized", target_size=target_size)

    def build(
        self,
        ranked: list[RankedStock],
        benchmark: list[BenchmarkWeight],
        as_of_date: date,
    ) -> PortfolioResult:
        """Construct a portfolio from ranked stocks and benchmark weights.

        Parameters
        ----------
        ranked : list[RankedStock]
            Ranked stock data with keys: ticker, aggregate_score,
            gics_sector, sector_rank, claim_count, structural_weight.
        benchmark : list[BenchmarkWeight]
            Benchmark sector weights.
        as_of_date : date
            As-of date for the portfolio.

        Returns
        -------
        PortfolioResult
            Portfolio result with holdings, sector_allocations, as_of_date.
        """
        if not ranked:
            logger.info("No ranked stocks provided, returning empty portfolio")
            return PortfolioResult(
                holdings=[],
                sector_allocations=[],
                as_of_date=as_of_date,
            )

        # Build benchmark weight map
        benchmark_map = {bw.sector: bw.weight for bw in benchmark}
        logger.debug(
            "Benchmark weights loaded",
            sector_count=len(benchmark_map),
        )

        # Group ranked stocks by sector
        stocks_by_sector: dict[str, list[RankedStock]] = defaultdict(list)
        for stock in ranked:
            sector = stock["gics_sector"]
            if sector in benchmark_map:
                stocks_by_sector[sector].append(stock)

        # Sort each sector by score descending
        for sector in stocks_by_sector:
            stocks_by_sector[sector].sort(
                key=lambda s: s["aggregate_score"],
                reverse=True,
            )

        # Compute stock counts per sector
        sector_counts = self._compute_sector_counts(
            benchmark_map=benchmark_map,
            stocks_by_sector=stocks_by_sector,
        )

        # Select stocks and compute weights
        holdings: list[PortfolioHolding] = []
        sector_allocations: list[SectorAllocation] = []

        for sector, count in sector_counts.items():
            if count == 0:
                continue

            available = stocks_by_sector.get(sector, [])
            selected = available[:count]

            if not selected:
                continue

            # Compute score-proportional weights within sector
            sector_weight = benchmark_map[sector]
            sector_holdings = self._build_sector_holdings(
                selected=selected,
                sector=sector,
                sector_weight=sector_weight,
            )
            holdings.extend(sector_holdings)

            actual_weight = sum(h.weight for h in sector_holdings)
            sector_allocations.append(
                SectorAllocation(
                    sector=sector,
                    benchmark_weight=benchmark_map[sector],
                    actual_weight=actual_weight,
                    stock_count=len(sector_holdings),
                )
            )

        # Normalize all weights to sum to 1.0
        holdings = self._normalize_weights(holdings)

        # Update sector allocations with normalized weights
        sector_allocations = self._update_sector_allocations(
            holdings=holdings,
            benchmark_map=benchmark_map,
        )

        logger.info(
            "Portfolio built",
            holdings_count=len(holdings),
            sectors=len(sector_allocations),
            total_weight=sum(h.weight for h in holdings),
        )

        return PortfolioResult(
            holdings=holdings,
            sector_allocations=sector_allocations,
            as_of_date=as_of_date,
        )

    # -----------------------------------------------------------------------
    # Internal methods
    # -----------------------------------------------------------------------
    def _compute_sector_counts(
        self,
        benchmark_map: dict[str, float],
        stocks_by_sector: dict[str, list[RankedStock]],
    ) -> dict[str, int]:
        """Compute how many stocks to select from each sector.

        Parameters
        ----------
        benchmark_map : dict[str, float]
            Sector to benchmark weight mapping.
        stocks_by_sector : dict[str, list[RankedStock]]
            Available stocks grouped by sector.

        Returns
        -------
        dict[str, int]
            Sector to stock count mapping.
        """
        raw_counts: dict[str, float] = {}
        for sector, weight in benchmark_map.items():
            available = len(stocks_by_sector.get(sector, []))
            if available > 0:
                raw_counts[sector] = self._target_size * weight

        # Round using largest-remainder method to ensure total matches target
        counts = self._largest_remainder_round(raw_counts)

        # Ensure minimum stocks per sector and cap at available
        for sector in counts:
            available = len(stocks_by_sector.get(sector, []))
            counts[sector] = max(
                _MIN_STOCKS_PER_SECTOR,
                min(counts[sector], available),
            )

        return counts

    @staticmethod
    def _largest_remainder_round(
        raw: dict[str, float],
    ) -> dict[str, int]:
        """Round fractional counts preserving the total.

        Uses the largest-remainder method (Hamilton's method) to
        distribute integer counts proportionally.

        Parameters
        ----------
        raw : dict[str, float]
            Sector to fractional count mapping.

        Returns
        -------
        dict[str, int]
            Sector to integer count mapping.
        """
        if not raw:
            return {}

        total = round(sum(raw.values()))
        floors = {k: math.floor(v) for k, v in raw.items()}
        remainders = {k: v - math.floor(v) for k, v in raw.items()}

        current_total = sum(floors.values())
        deficit = total - current_total

        # Distribute remaining slots to sectors with largest remainders
        sorted_sectors = sorted(
            remainders.keys(),
            key=lambda k: remainders[k],
            reverse=True,
        )
        for i in range(min(deficit, len(sorted_sectors))):
            floors[sorted_sectors[i]] += 1

        return floors

    def _build_sector_holdings(
        self,
        selected: list[RankedStock],
        sector: str,
        sector_weight: float,
    ) -> list[PortfolioHolding]:
        """Build holdings for a single sector with score-proportional weights.

        Parameters
        ----------
        selected : list[RankedStock]
            Selected stocks for this sector (sorted by score desc).
        sector : str
            Sector name.
        sector_weight : float
            Target sector weight from benchmark.

        Returns
        -------
        list[PortfolioHolding]
            Holdings for this sector.
        """
        total_score = sum(s["aggregate_score"] for s in selected)

        holdings: list[PortfolioHolding] = []
        for stock in selected:
            score = stock["aggregate_score"]
            if total_score > 0:
                intra_weight = (score / total_score) * sector_weight
            else:
                intra_weight = sector_weight / len(selected)

            holdings.append(
                PortfolioHolding(
                    ticker=stock["ticker"],
                    weight=intra_weight,
                    sector=sector,
                    score=score,
                    rationale_summary=f"Sector rank {stock['sector_rank']}, "
                    f"score {score:.2f}",
                )
            )

        return holdings

    @staticmethod
    def _normalize_weights(
        holdings: list[PortfolioHolding],
    ) -> list[PortfolioHolding]:
        """Normalize all holding weights to sum to 1.0.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Holdings with unnormalized weights.

        Returns
        -------
        list[PortfolioHolding]
            Holdings with weights summing to 1.0.
        """
        if not holdings:
            return []

        total = sum(h.weight for h in holdings)
        if total == 0:
            return holdings

        return [
            PortfolioHolding(
                ticker=h.ticker,
                weight=h.weight / total,
                sector=h.sector,
                score=h.score,
                rationale_summary=h.rationale_summary,
            )
            for h in holdings
        ]

    @staticmethod
    def _update_sector_allocations(
        holdings: list[PortfolioHolding],
        benchmark_map: dict[str, float],
    ) -> list[SectorAllocation]:
        """Recompute sector allocations from normalized holdings.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Normalized holdings.
        benchmark_map : dict[str, float]
            Benchmark sector weights.

        Returns
        -------
        list[SectorAllocation]
            Updated sector allocations.
        """
        sector_weights: dict[str, float] = defaultdict(float)
        sector_counts: dict[str, int] = defaultdict(int)
        for h in holdings:
            sector_weights[h.sector] += h.weight
            sector_counts[h.sector] += 1

        allocations: list[SectorAllocation] = []
        for sector in sorted(sector_weights):
            allocations.append(
                SectorAllocation(
                    sector=sector,
                    benchmark_weight=benchmark_map.get(sector, 0.0),
                    actual_weight=sector_weights[sector],
                    stock_count=sector_counts[sector],
                )
            )

        return allocations


__all__ = ["PortfolioBuilder", "RankedStock"]
