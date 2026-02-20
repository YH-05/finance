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
import statistics
from pathlib import Path
from typing import TYPE_CHECKING

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from datetime import date

    from .types import (
        EvaluationResult,
        PortfolioHolding,
        PortfolioResult,
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
        portfolio: PortfolioResult,
        claims: dict[str, list[ScoredClaim]],
        scores: dict[str, StockScore],
        output_dir: Path,
        evaluation: EvaluationResult | None = None,
    ) -> None:
        """Generate all output files.

        Parameters
        ----------
        portfolio : PortfolioResult
            Portfolio result from PortfolioBuilder.build().
        claims : dict[str, list[ScoredClaim]]
            Scored claims per ticker from Phase 2.
        scores : dict[str, StockScore]
            Aggregated stock scores from Phase 3.
        output_dir : Path
            Directory to write output files.
        evaluation : EvaluationResult | None, optional
            Strategy evaluation result.  When provided, writes
            ``evaluation_summary.md`` and ``evaluation_results.json``.
            Default None preserves backward-compatible behavior.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        holdings: list[PortfolioHolding] = portfolio.holdings
        sector_allocations: list[SectorAllocation] = portfolio.sector_allocations
        as_of_date = portfolio.as_of_date

        logger.info(
            "Generating output files",
            output_dir=str(output_dir),
            holdings_count=len(holdings),
            has_evaluation=evaluation is not None,
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

        files_created = 4
        if evaluation is not None:
            self._write_evaluation_summary(
                evaluation=evaluation,
                output_dir=output_dir,
            )
            self._write_evaluation_results(
                evaluation=evaluation,
                output_dir=output_dir,
            )
            files_created += 2

        logger.info(
            "Output generation completed",
            output_dir=str(output_dir),
            files_created=files_created,
        )

    # -----------------------------------------------------------------------
    # JSON output
    # -----------------------------------------------------------------------
    def _write_json(
        self,
        holdings: list[PortfolioHolding],
        sector_allocations: list[SectorAllocation],
        as_of_date: date,
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
        as_of_date: date,
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
            lines.append(f"- **Mean**: {statistics.fmean(score_values):.4f}")
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

    # -----------------------------------------------------------------------
    # Evaluation output
    # -----------------------------------------------------------------------
    def _write_evaluation_summary(
        self,
        evaluation: EvaluationResult,
        output_dir: Path,
    ) -> None:
        """Write evaluation_summary.md with performance, correlation, and transparency.

        Parameters
        ----------
        evaluation : EvaluationResult
            Strategy evaluation result.
        output_dir : Path
            Output directory.
        """
        perf = evaluation.performance
        corr = evaluation.analyst_correlation
        trans = evaluation.transparency

        lines: list[str] = []
        lines.append("# Strategy Evaluation Summary")
        lines.append("")
        lines.append(f"**Threshold**: {evaluation.threshold:.2f}")
        lines.append(f"**Portfolio Size**: {evaluation.portfolio_size}")
        lines.append("")

        # Performance section
        lines.append("## Performance Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Sharpe Ratio | {perf.sharpe_ratio:.4f} |")
        lines.append(f"| Max Drawdown | {perf.max_drawdown:.2%} |")
        lines.append(f"| Beta | {perf.beta:.4f} |")
        lines.append(f"| Information Ratio | {perf.information_ratio:.4f} |")
        lines.append(f"| Cumulative Return | {perf.cumulative_return:.2%} |")
        lines.append("")

        # Analyst correlation section
        lines.append("## Analyst Correlation")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Sample Size | {corr.sample_size} |")
        if corr.spearman_correlation is not None:
            lines.append(f"| Spearman Correlation | {corr.spearman_correlation:.4f} |")
            lines.append(f"| P-Value | {corr.p_value:.4f} |")
        else:
            lines.append("| Spearman Correlation | N/A (insufficient data) |")
        if corr.hit_rate is not None:
            lines.append(f"| Hit Rate (Top 20%) | {corr.hit_rate:.2%} |")
        else:
            lines.append("| Hit Rate (Top 20%) | N/A |")
        lines.append("")

        # Transparency section
        lines.append("## Transparency Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Mean Claim Count | {trans.mean_claim_count:.2f} |")
        lines.append(f"| Mean Structural Weight | {trans.mean_structural_weight:.4f} |")
        lines.append(f"| Coverage Rate | {trans.coverage_rate:.2%} |")
        lines.append("")

        output_path = output_dir / "evaluation_summary.md"
        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.debug("Evaluation summary written", path=str(output_path))

    def _write_evaluation_results(
        self,
        evaluation: EvaluationResult,
        output_dir: Path,
    ) -> None:
        """Write evaluation_results.json with structured evaluation data.

        Parameters
        ----------
        evaluation : EvaluationResult
            Strategy evaluation result.
        output_dir : Path
            Output directory.
        """
        perf = evaluation.performance
        corr = evaluation.analyst_correlation
        trans = evaluation.transparency

        data = {
            "threshold": evaluation.threshold,
            "portfolio_size": evaluation.portfolio_size,
            "performance": {
                "sharpe_ratio": round(perf.sharpe_ratio, 6),
                "max_drawdown": round(perf.max_drawdown, 6),
                "beta": round(perf.beta, 6),
                "information_ratio": round(perf.information_ratio, 6),
                "cumulative_return": round(perf.cumulative_return, 6),
            },
            "analyst_correlation": {
                "spearman_correlation": (
                    round(corr.spearman_correlation, 6)
                    if corr.spearman_correlation is not None
                    else None
                ),
                "sample_size": corr.sample_size,
                "p_value": (
                    round(corr.p_value, 6) if corr.p_value is not None else None
                ),
                "hit_rate": (
                    round(corr.hit_rate, 6) if corr.hit_rate is not None else None
                ),
            },
            "transparency": {
                "mean_claim_count": round(trans.mean_claim_count, 4),
                "mean_structural_weight": round(trans.mean_structural_weight, 4),
                "coverage_rate": round(trans.coverage_rate, 4),
            },
        }

        output_path = output_dir / "evaluation_results.json"
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug("Evaluation results written", path=str(output_path))


__all__ = ["OutputGenerator"]
