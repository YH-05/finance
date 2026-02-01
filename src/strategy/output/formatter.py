"""Result formatter for risk metrics output.

This module provides the ResultFormatter class to convert
RiskMetricsResult to various output formats.
"""

from typing import Any

import pandas as pd
from utils_core.logging import get_logger

from ..risk.metrics import RiskMetricsResult

logger = get_logger(__name__)


class ResultFormatter:
    """Formatter for converting RiskMetricsResult to various output formats.

    This class provides methods to convert risk analysis results to
    DataFrame, dictionary (JSON-serializable), Markdown, and HTML formats.

    Attributes
    ----------
    result : RiskMetricsResult | None
        The risk metrics result to format. Can be set at initialization
        or passed to individual methods.

    Examples
    --------
    >>> from datetime import date, datetime
    >>> from strategy.risk.metrics import RiskMetricsResult
    >>> result = RiskMetricsResult(
    ...     volatility=0.15,
    ...     sharpe_ratio=1.2,
    ...     sortino_ratio=1.5,
    ...     max_drawdown=-0.10,
    ...     var_95=-0.02,
    ...     var_99=-0.03,
    ...     beta=1.1,
    ...     treynor_ratio=0.08,
    ...     information_ratio=0.5,
    ...     annualized_return=0.08,
    ...     cumulative_return=0.25,
    ...     calculated_at=datetime.now(),
    ...     period_start=date(2023, 1, 1),
    ...     period_end=date(2023, 12, 31),
    ... )
    >>> formatter = ResultFormatter()
    >>> df = formatter.to_dataframe(result)
    >>> isinstance(df, pd.DataFrame)
    True
    """

    def __init__(self, result: RiskMetricsResult | None = None) -> None:
        """Initialize ResultFormatter.

        Parameters
        ----------
        result : RiskMetricsResult | None, default=None
            Optional risk metrics result to format. If provided, it can be
            used with _repr_html_ for direct display in notebooks.
        """
        self._result = result
        logger.debug(
            "ResultFormatter initialized",
            has_result=result is not None,
        )

    @property
    def result(self) -> RiskMetricsResult | None:
        """Get the stored RiskMetricsResult.

        Returns
        -------
        RiskMetricsResult | None
            The stored result or None if not set.
        """
        return self._result

    @result.setter
    def result(self, value: RiskMetricsResult | None) -> None:
        """Set the RiskMetricsResult.

        Parameters
        ----------
        value : RiskMetricsResult | None
            The result to store.
        """
        self._result = value
        logger.debug(
            "ResultFormatter result updated",
            has_result=value is not None,
        )

    def to_dataframe(self, result: RiskMetricsResult) -> pd.DataFrame:
        """Convert RiskMetricsResult to pandas DataFrame.

        Parameters
        ----------
        result : RiskMetricsResult
            The risk metrics result to convert.

        Returns
        -------
        pd.DataFrame
            DataFrame with metric names as index and values as data.

        Raises
        ------
        TypeError
            If result is not a RiskMetricsResult instance.

        Examples
        --------
        >>> formatter = ResultFormatter()
        >>> df = formatter.to_dataframe(result)
        >>> 'volatility' in df.index
        True
        """
        if not isinstance(result, RiskMetricsResult):
            logger.error(
                "Invalid result type for to_dataframe",
                expected="RiskMetricsResult",
                received=type(result).__name__,
            )
            raise TypeError(f"Expected RiskMetricsResult, got {type(result).__name__}")

        logger.debug(
            "Converting RiskMetricsResult to DataFrame",
            period_start=str(result.period_start),
            period_end=str(result.period_end),
        )

        data = {
            "volatility": result.volatility,
            "sharpe_ratio": result.sharpe_ratio,
            "sortino_ratio": result.sortino_ratio,
            "max_drawdown": result.max_drawdown,
            "var_95": result.var_95,
            "var_99": result.var_99,
            "beta": result.beta,
            "treynor_ratio": result.treynor_ratio,
            "information_ratio": result.information_ratio,
            "annualized_return": result.annualized_return,
            "cumulative_return": result.cumulative_return,
        }

        df = pd.DataFrame.from_dict(data, orient="index", columns=pd.Index(["Value"]))
        df.index.name = "Metric"

        logger.debug(
            "DataFrame created successfully",
            metrics_count=len(df),
            has_benchmark_metrics=result.beta is not None,
        )

        return df

    def to_dict(self, result: RiskMetricsResult) -> dict[str, Any]:
        """Convert RiskMetricsResult to JSON-serializable dictionary.

        Parameters
        ----------
        result : RiskMetricsResult
            The risk metrics result to convert.

        Returns
        -------
        dict[str, Any]
            Dictionary with all metrics and ISO-formatted date strings.

        Raises
        ------
        TypeError
            If result is not a RiskMetricsResult instance.

        Examples
        --------
        >>> formatter = ResultFormatter()
        >>> d = formatter.to_dict(result)
        >>> isinstance(d['calculated_at'], str)
        True
        """
        if not isinstance(result, RiskMetricsResult):
            logger.error(
                "Invalid result type for to_dict",
                expected="RiskMetricsResult",
                received=type(result).__name__,
            )
            raise TypeError(f"Expected RiskMetricsResult, got {type(result).__name__}")

        logger.debug(
            "Converting RiskMetricsResult to dict",
            period_start=str(result.period_start),
            period_end=str(result.period_end),
        )

        result_dict: dict[str, Any] = {
            "volatility": result.volatility,
            "sharpe_ratio": result.sharpe_ratio,
            "sortino_ratio": result.sortino_ratio,
            "max_drawdown": result.max_drawdown,
            "var_95": result.var_95,
            "var_99": result.var_99,
            "beta": result.beta,
            "treynor_ratio": result.treynor_ratio,
            "information_ratio": result.information_ratio,
            "annualized_return": result.annualized_return,
            "cumulative_return": result.cumulative_return,
            "calculated_at": result.calculated_at.isoformat(),
            "period_start": result.period_start.isoformat(),
            "period_end": result.period_end.isoformat(),
        }

        logger.debug(
            "Dict created successfully",
            keys_count=len(result_dict),
        )

        return result_dict

    def to_markdown(self, result: RiskMetricsResult) -> str:
        """Convert RiskMetricsResult to Markdown-formatted report.

        Parameters
        ----------
        result : RiskMetricsResult
            The risk metrics result to convert.

        Returns
        -------
        str
            Markdown-formatted string with tables and headers.

        Raises
        ------
        TypeError
            If result is not a RiskMetricsResult instance.

        Examples
        --------
        >>> formatter = ResultFormatter()
        >>> md = formatter.to_markdown(result)
        >>> '|' in md
        True
        """
        if not isinstance(result, RiskMetricsResult):
            logger.error(
                "Invalid result type for to_markdown",
                expected="RiskMetricsResult",
                received=type(result).__name__,
            )
            raise TypeError(f"Expected RiskMetricsResult, got {type(result).__name__}")

        logger.debug(
            "Converting RiskMetricsResult to Markdown",
            period_start=str(result.period_start),
            period_end=str(result.period_end),
        )

        lines = [
            "## Risk Metrics Report",
            "",
            f"**Period**: {result.period_start} to {result.period_end}",
            f"**Calculated at**: {result.calculated_at.isoformat()}",
            "",
            "### Performance Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Annualized Return | {result.annualized_return:.2%} |",
            f"| Cumulative Return | {result.cumulative_return:.2%} |",
            "",
            "### Risk Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Volatility | {result.volatility:.2%} |",
            f"| Sharpe Ratio | {result.sharpe_ratio:.4f} |",
            f"| Sortino Ratio | {result.sortino_ratio:.4f} |",
            f"| Max Drawdown | {result.max_drawdown:.2%} |",
            f"| VaR (95%) | {result.var_95:.2%} |",
            f"| VaR (99%) | {result.var_99:.2%} |",
        ]

        # Add benchmark-relative metrics if available
        if result.beta is not None:
            lines.extend(
                [
                    "",
                    "### Benchmark-Relative Metrics",
                    "",
                    "| Metric | Value |",
                    "|--------|-------|",
                    f"| Beta | {result.beta:.4f} |",
                ]
            )
            if result.treynor_ratio is not None:
                lines.append(f"| Treynor Ratio | {result.treynor_ratio:.4f} |")
            if result.information_ratio is not None:
                lines.append(f"| Information Ratio | {result.information_ratio:.4f} |")

        markdown = "\n".join(lines)

        logger.debug(
            "Markdown report created successfully",
            lines_count=len(lines),
            has_benchmark_section=result.beta is not None,
        )

        return markdown

    def _repr_html_(self) -> str:
        """Generate HTML representation for Jupyter/marimo notebooks.

        This method is called automatically by Jupyter and marimo
        notebooks to render the formatter as HTML.

        Returns
        -------
        str
            HTML string with styled table representation.

        Examples
        --------
        >>> formatter = ResultFormatter(result)
        >>> html = formatter._repr_html_()
        >>> '<table' in html.lower()
        True
        """
        if self._result is None:
            logger.debug("No result set for HTML representation")
            return "<p>No RiskMetricsResult set. Use ResultFormatter(result) to initialize with data.</p>"

        result = self._result

        logger.debug(
            "Generating HTML representation",
            period_start=str(result.period_start),
            period_end=str(result.period_end),
        )

        # Build HTML table with styling
        html_parts = [
            '<div style="font-family: sans-serif;">',
            '<h3 style="margin-bottom: 10px;">Risk Metrics Report</h3>',
            f"<p><strong>Period</strong>: {result.period_start} to {result.period_end}</p>",
            f"<p><strong>Calculated at</strong>: {result.calculated_at.isoformat()}</p>",
            "",
            "<h4>Performance Metrics</h4>",
            '<table style="border-collapse: collapse; margin-bottom: 20px;">',
            '<thead><tr style="background-color: #f0f0f0;">',
            '<th style="border: 1px solid #ccc; padding: 8px;">Metric</th>',
            '<th style="border: 1px solid #ccc; padding: 8px;">Value</th>',
            "</tr></thead>",
            "<tbody>",
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Annualized Return</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.annualized_return:.2%}</td></tr>',
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Cumulative Return</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.cumulative_return:.2%}</td></tr>',
            "</tbody></table>",
            "",
            "<h4>Risk Metrics</h4>",
            '<table style="border-collapse: collapse; margin-bottom: 20px;">',
            '<thead><tr style="background-color: #f0f0f0;">',
            '<th style="border: 1px solid #ccc; padding: 8px;">Metric</th>',
            '<th style="border: 1px solid #ccc; padding: 8px;">Value</th>',
            "</tr></thead>",
            "<tbody>",
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Volatility</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.volatility:.2%}</td></tr>',
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Sharpe Ratio</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.sharpe_ratio:.4f}</td></tr>',
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Sortino Ratio</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.sortino_ratio:.4f}</td></tr>',
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Max Drawdown</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.max_drawdown:.2%}</td></tr>',
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">VaR (95%)</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.var_95:.2%}</td></tr>',
            f'<tr><td style="border: 1px solid #ccc; padding: 8px;">VaR (99%)</td>'
            f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.var_99:.2%}</td></tr>',
            "</tbody></table>",
        ]

        # Add benchmark-relative metrics if available
        if result.beta is not None:
            html_parts.extend(
                [
                    "<h4>Benchmark-Relative Metrics</h4>",
                    '<table style="border-collapse: collapse;">',
                    '<thead><tr style="background-color: #f0f0f0;">',
                    '<th style="border: 1px solid #ccc; padding: 8px;">Metric</th>',
                    '<th style="border: 1px solid #ccc; padding: 8px;">Value</th>',
                    "</tr></thead>",
                    "<tbody>",
                    f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Beta</td>'
                    f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.beta:.4f}</td></tr>',
                ]
            )
            if result.treynor_ratio is not None:
                html_parts.append(
                    f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Treynor Ratio</td>'
                    f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.treynor_ratio:.4f}</td></tr>'
                )
            if result.information_ratio is not None:
                html_parts.append(
                    f'<tr><td style="border: 1px solid #ccc; padding: 8px;">Information Ratio</td>'
                    f'<td style="border: 1px solid #ccc; padding: 8px; text-align: right;">{result.information_ratio:.4f}</td></tr>'
                )
            html_parts.extend(["</tbody></table>"])

        html_parts.append("</div>")

        html = "\n".join(html_parts)

        logger.debug(
            "HTML representation created successfully",
            html_length=len(html),
            has_benchmark_section=result.beta is not None,
        )

        return html

    def __repr__(self) -> str:
        """Return string representation of formatter.

        Returns
        -------
        str
            String representation with result status.
        """
        if self._result is None:
            return "ResultFormatter(result=None)"
        return (
            f"ResultFormatter(result=RiskMetricsResult("
            f"period={self._result.period_start} to {self._result.period_end}))"
        )
