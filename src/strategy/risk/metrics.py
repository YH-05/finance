"""Risk metrics result dataclass.

This module provides the RiskMetricsResult dataclass that holds
the computed risk metrics for a portfolio.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RiskMetricsResult:
    """Risk metrics calculation results.

    This dataclass holds all computed risk metrics for a portfolio,
    including basic risk measures and optional benchmark-relative metrics.

    Attributes
    ----------
    volatility : float
        Annualized volatility (standard deviation of returns)
    sharpe_ratio : float
        Risk-adjusted return relative to risk-free rate
    sortino_ratio : float
        Risk-adjusted return using downside deviation
    max_drawdown : float
        Maximum peak-to-trough decline (negative value)
    var_95 : float
        95% Value at Risk (negative value)
    var_99 : float
        99% Value at Risk (negative value)
    beta : float | None
        Beta relative to benchmark (None if no benchmark)
    treynor_ratio : float | None
        Return per unit of systematic risk (None if no benchmark)
    information_ratio : float | None
        Active return per unit of tracking error (None if no benchmark)
    annualized_return : float
        Annualized return
    cumulative_return : float
        Total cumulative return over the period
    calculated_at : datetime
        Timestamp when metrics were calculated
    period_start : date
        Start date of the analysis period
    period_end : date
        End date of the analysis period

    Examples
    --------
    >>> from datetime import date, datetime
    >>> result = RiskMetricsResult(
    ...     volatility=0.15,
    ...     sharpe_ratio=1.2,
    ...     sortino_ratio=1.5,
    ...     max_drawdown=-0.10,
    ...     var_95=-0.02,
    ...     var_99=-0.03,
    ...     beta=None,
    ...     treynor_ratio=None,
    ...     information_ratio=None,
    ...     annualized_return=0.08,
    ...     cumulative_return=0.25,
    ...     calculated_at=datetime.now(),
    ...     period_start=date(2023, 1, 1),
    ...     period_end=date(2023, 12, 31),
    ... )
    >>> result.volatility
    0.15
    """

    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    var_99: float
    beta: float | None
    treynor_ratio: float | None
    information_ratio: float | None
    annualized_return: float
    cumulative_return: float
    calculated_at: datetime
    period_start: date
    period_end: date

    def __post_init__(self) -> None:
        """Log initialization of RiskMetricsResult."""
        logger.debug(
            "RiskMetricsResult initialized",
            volatility=self.volatility,
            sharpe_ratio=self.sharpe_ratio,
            period_start=str(self.period_start),
            period_end=str(self.period_end),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns
        -------
        dict[str, Any]
            Dictionary representation with ISO-formatted dates

        Examples
        --------
        >>> result = RiskMetricsResult(...)
        >>> d = result.to_dict()
        >>> isinstance(d["calculated_at"], str)
        True
        """
        logger.debug("Converting RiskMetricsResult to dict")
        return {
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "beta": self.beta,
            "treynor_ratio": self.treynor_ratio,
            "information_ratio": self.information_ratio,
            "annualized_return": self.annualized_return,
            "cumulative_return": self.cumulative_return,
            "calculated_at": self.calculated_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
        }

    def to_markdown(self) -> str:
        """Generate a markdown-formatted report.

        Returns
        -------
        str
            Markdown table with all risk metrics

        Examples
        --------
        >>> result = RiskMetricsResult(...)
        >>> md = result.to_markdown()
        >>> "Volatility" in md or "ボラティリティ" in md
        True
        """
        logger.debug("Generating markdown report")

        lines = [
            "## Risk Metrics Report",
            "",
            f"**Period**: {self.period_start} to {self.period_end}",
            f"**Calculated at**: {self.calculated_at.isoformat()}",
            "",
            "### Performance Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Annualized Return | {self.annualized_return:.2%} |",
            f"| Cumulative Return | {self.cumulative_return:.2%} |",
            "",
            "### Risk Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Volatility (ボラティリティ) | {self.volatility:.2%} |",
            f"| Sharpe Ratio (シャープレシオ) | {self.sharpe_ratio:.4f} |",
            f"| Sortino Ratio (ソルティノレシオ) | {self.sortino_ratio:.4f} |",
            f"| Max Drawdown | {self.max_drawdown:.2%} |",
            f"| VaR (95%) | {self.var_95:.2%} |",
            f"| VaR (99%) | {self.var_99:.2%} |",
        ]

        # Add benchmark-relative metrics if available
        if self.beta is not None:
            lines.extend(
                [
                    "",
                    "### Benchmark-Relative Metrics",
                    "",
                    "| Metric | Value |",
                    "|--------|-------|",
                    f"| Beta | {self.beta:.4f} |",
                ]
            )
            if self.treynor_ratio is not None:
                lines.append(f"| Treynor Ratio | {self.treynor_ratio:.4f} |")
            if self.information_ratio is not None:
                lines.append(f"| Information Ratio | {self.information_ratio:.4f} |")

        return "\n".join(lines)

    def summary(self) -> pd.DataFrame:
        """Generate a summary DataFrame of all metrics.

        Returns
        -------
        pd.DataFrame
            DataFrame with metric names as index and values as data

        Examples
        --------
        >>> result = RiskMetricsResult(...)
        >>> df = result.summary()
        >>> isinstance(df, pd.DataFrame)
        True
        """
        logger.debug("Generating summary DataFrame")

        data = {
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "beta": self.beta,
            "treynor_ratio": self.treynor_ratio,
            "information_ratio": self.information_ratio,
            "annualized_return": self.annualized_return,
            "cumulative_return": self.cumulative_return,
        }

        df = pd.DataFrame.from_dict(data, orient="index", columns=pd.Index(["Value"]))
        df.index.name = "Metric"

        logger.debug(
            "Summary DataFrame created",
            metrics_count=len(df),
        )

        return df
