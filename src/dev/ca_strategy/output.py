"""Phase 5 output generation for the CA Strategy pipeline.

Generates portfolio output files from the constructed portfolio:

Output Files
------------
- ``portfolio_weights.json``: Holdings, sector allocation, data sources
- ``portfolio_weights.csv``: Excel-viewable holdings format
- ``portfolio_summary.md``: Sector allocation table, selection criteria,
  score distribution summary
- ``rationale/{TICKER}_rationale.md``: Per-stock rationale with CA
  evaluation, SEC evidence, and CAGR connection quality
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from .types import (
        PortfolioHolding,
        ScoredClaim,
        SectorAllocation,
        StockScore,
    )

logger = get_logger(__name__)


class OutputGenerator:
    """Generate portfolio output files.

    Produces JSON, CSV, Markdown summary, and per-stock rationale files
    from portfolio construction results.

    Examples
    --------
    >>> gen = OutputGenerator()
    >>> gen.generate_all(portfolio, claims, scores, Path("output"))
    """

    def generate_all(
        self,
        portfolio: dict,
        claims: dict[str, list[ScoredClaim]],
        scores: dict[str, StockScore],
        output_dir: Path,
    ) -> None:
        """Generate all output files.

        Parameters
        ----------
        portfolio : dict
            Portfolio result from PortfolioBuilder.build() with keys:
            holdings, sector_allocations, as_of_date.
        claims : dict[str, list[ScoredClaim]]
            Scored claims per ticker from Phase 2.
        scores : dict[str, StockScore]
            Aggregated stock scores from Phase 3.
        output_dir : Path
            Directory to write output files.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        holdings: list[PortfolioHolding] = portfolio["holdings"]
        sector_allocations: list[SectorAllocation] = portfolio["sector_allocations"]
        as_of_date = portfolio["as_of_date"]

        logger.info(
            "Generating output files",
            output_dir=str(output_dir),
            holdings_count=len(holdings),
        )

        self._write_json(
            holdings=holdings,
            sector_allocations=sector_allocations,
            as_of_date=as_of_date,
            output_dir=output_dir,
        )

        self._write_csv(
            holdings=holdings,
            output_dir=output_dir,
        )

        self._write_summary(
            holdings=holdings,
            sector_allocations=sector_allocations,
            as_of_date=as_of_date,
            scores=scores,
            output_dir=output_dir,
        )

        self._write_rationales(
            holdings=holdings,
            claims=claims,
            scores=scores,
            output_dir=output_dir,
        )

        logger.info(
            "Output generation completed",
            output_dir=str(output_dir),
            files_created=4,
        )

    # -----------------------------------------------------------------------
    # JSON output
    # -----------------------------------------------------------------------
    def _write_json(
        self,
        holdings: list[PortfolioHolding],
        sector_allocations: list[SectorAllocation],
        as_of_date: object,
        output_dir: Path,
    ) -> None:
        """Write portfolio_weights.json.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Portfolio holdings.
        sector_allocations : list[SectorAllocation]
            Sector allocation data.
        as_of_date : date
            Portfolio as-of date.
        output_dir : Path
            Output directory.
        """
        data = {
            "as_of_date": str(as_of_date),
            "holdings": [
                {
                    "ticker": h.ticker,
                    "weight": round(h.weight, 6),
                    "sector": h.sector,
                    "score": round(h.score, 4),
                    "rationale_summary": h.rationale_summary,
                }
                for h in holdings
            ],
            "sector_allocation": [
                {
                    "sector": sa.sector,
                    "benchmark_weight": round(sa.benchmark_weight, 4),
                    "actual_weight": round(sa.actual_weight, 4),
                    "stock_count": sa.stock_count,
                }
                for sa in sector_allocations
            ],
            "data_sources": {
                "benchmark": "MSCI Kokusai (MSCI World ex Japan)",
                "scoring": "CA Strategy Phase 1-3",
                "universe": "300 stocks, MSCI Kokusai constituents",
            },
        }

        output_path = output_dir / "portfolio_weights.json"
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug("JSON written", path=str(output_path))

    # -----------------------------------------------------------------------
    # CSV output
    # -----------------------------------------------------------------------
    def _write_csv(
        self,
        holdings: list[PortfolioHolding],
        output_dir: Path,
    ) -> None:
        """Write portfolio_weights.csv for Excel viewing.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Portfolio holdings.
        output_dir : Path
            Output directory.
        """
        output_path = output_dir / "portfolio_weights.csv"
        fieldnames = ["ticker", "weight", "sector", "score", "rationale_summary"]

        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for h in holdings:
                writer.writerow(
                    {
                        "ticker": h.ticker,
                        "weight": f"{h.weight:.6f}",
                        "sector": h.sector,
                        "score": f"{h.score:.4f}",
                        "rationale_summary": h.rationale_summary,
                    }
                )

        logger.debug("CSV written", path=str(output_path), rows=len(holdings))

    # -----------------------------------------------------------------------
    # Markdown summary
    # -----------------------------------------------------------------------
    def _write_summary(
        self,
        holdings: list[PortfolioHolding],
        sector_allocations: list[SectorAllocation],
        as_of_date: object,
        scores: dict[str, StockScore],
        output_dir: Path,
    ) -> None:
        """Write portfolio_summary.md with sector allocation table.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Portfolio holdings.
        sector_allocations : list[SectorAllocation]
            Sector allocation data.
        as_of_date : date
            Portfolio as-of date.
        scores : dict[str, StockScore]
            Stock scores for distribution analysis.
        output_dir : Path
            Output directory.
        """
        lines: list[str] = []
        lines.append("# Portfolio Summary")
        lines.append("")
        lines.append(f"**As of Date**: {as_of_date}")
        lines.append(f"**Total Holdings**: {len(holdings)}")
        lines.append("")

        # Sector allocation table
        lines.append("## Sector Allocation")
        lines.append("")
        lines.append("| Sector | Benchmark Weight | Actual Weight | Stocks |")
        lines.append("|--------|-----------------|---------------|--------|")
        for sa in sector_allocations:
            lines.append(
                f"| {sa.sector} | {sa.benchmark_weight:.2%} | "
                f"{sa.actual_weight:.2%} | {sa.stock_count} |"
            )
        lines.append("")

        # Holdings table
        lines.append("## Holdings")
        lines.append("")
        lines.append("| Ticker | Weight | Sector | Score |")
        lines.append("|--------|--------|--------|-------|")
        sorted_holdings = sorted(holdings, key=lambda h: h.weight, reverse=True)
        for h in sorted_holdings:
            lines.append(
                f"| {h.ticker} | {h.weight:.2%} | {h.sector} | {h.score:.2f} |"
            )
        lines.append("")

        # Score distribution
        if scores:
            lines.append("## Score Distribution")
            lines.append("")
            score_values = [s.aggregate_score for s in scores.values()]
            lines.append(f"- **Mean**: {_mean(score_values):.4f}")
            lines.append(f"- **Min**: {min(score_values):.4f}")
            lines.append(f"- **Max**: {max(score_values):.4f}")
            lines.append(f"- **Count**: {len(score_values)}")
            lines.append("")

        # Selection criteria
        lines.append("## Selection Criteria")
        lines.append("")
        lines.append("- Sector allocation follows MSCI Kokusai benchmark weights")
        lines.append(
            "- Within each sector, top-N stocks by aggregate score are selected"
        )
        lines.append("- Intra-sector weights are proportional to stock scores")
        lines.append("")

        output_path = output_dir / "portfolio_summary.md"
        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.debug("Summary written", path=str(output_path))

    # -----------------------------------------------------------------------
    # Per-stock rationale files
    # -----------------------------------------------------------------------
    def _write_rationales(
        self,
        holdings: list[PortfolioHolding],
        claims: dict[str, list[ScoredClaim]],
        scores: dict[str, StockScore],
        output_dir: Path,
    ) -> None:
        """Write rationale/{TICKER}_rationale.md for each holding.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Portfolio holdings.
        claims : dict[str, list[ScoredClaim]]
            Scored claims per ticker.
        scores : dict[str, StockScore]
            Stock scores per ticker.
        output_dir : Path
            Output directory.
        """
        rationale_dir = output_dir / "rationale"
        rationale_dir.mkdir(parents=True, exist_ok=True)

        for holding in holdings:
            ticker = holding.ticker
            ticker_claims = claims.get(ticker, [])
            ticker_score = scores.get(ticker)

            content = self._build_rationale(
                holding=holding,
                claims=ticker_claims,
                score=ticker_score,
            )

            output_path = rationale_dir / f"{ticker}_rationale.md"
            output_path.write_text(content, encoding="utf-8")

        logger.debug(
            "Rationale files written",
            count=len(holdings),
            directory=str(rationale_dir),
        )

    def _build_rationale(
        self,
        holding: PortfolioHolding,
        claims: list[ScoredClaim],
        score: StockScore | None,
    ) -> str:
        """Build rationale markdown content for a single stock.

        Parameters
        ----------
        holding : PortfolioHolding
            The portfolio holding.
        claims : list[ScoredClaim]
            Scored claims for this ticker.
        score : StockScore | None
            Aggregated score for this ticker.

        Returns
        -------
        str
            Markdown content for the rationale file.
        """
        lines: list[str] = []
        lines.append(f"# {holding.ticker} - Investment Rationale")
        lines.append("")

        # Summary section
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Ticker**: {holding.ticker}")
        lines.append(f"- **Sector**: {holding.sector}")
        lines.append(f"- **Portfolio Weight**: {holding.weight:.2%}")
        lines.append(f"- **Score**: {holding.score}")
        lines.append(f"- **Rationale**: {holding.rationale_summary}")
        lines.append("")

        # Score details
        if score is not None:
            lines.append("## Score Details")
            lines.append("")
            lines.append(f"- **Aggregate Score**: {score.aggregate_score:.4f}")
            lines.append(f"- **Claim Count**: {score.claim_count}")
            lines.append(f"- **Structural Weight**: {score.structural_weight:.4f}")
            lines.append("")

        # CA Evaluation (claims)
        lines.append("## Competitive Advantage Evaluation")
        lines.append("")
        if claims:
            for i, claim in enumerate(claims, 1):
                lines.append(f"### Claim {i}: {claim.claim_type}")
                lines.append("")
                lines.append(f"- **Claim**: {claim.claim}")
                lines.append(f"- **Evidence**: {claim.evidence}")
                lines.append(f"- **Final Confidence**: {claim.final_confidence:.0%}")
                if claim.adjustments:
                    lines.append("- **Adjustments**:")
                    for adj in claim.adjustments:
                        lines.append(
                            f"  - {adj.source}: {adj.adjustment:+.0%} ({adj.reasoning})"
                        )
                lines.append("")
        else:
            lines.append("No claims available for this ticker.")
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def _mean(values: list[float]) -> float:
    """Compute arithmetic mean.

    Parameters
    ----------
    values : list[float]
        Input values.

    Returns
    -------
    float
        Arithmetic mean, or 0.0 if empty.
    """
    if not values:
        return 0.0
    return sum(values) / len(values)


__all__ = ["OutputGenerator"]
