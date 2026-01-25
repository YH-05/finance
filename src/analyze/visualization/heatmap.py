"""Heatmap chart implementation for correlation visualization.

This module provides the HeatmapChart class for creating correlation
matrix heatmaps with customizable color scales and annotations.
"""

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analyze.statistics.types import CorrelationResult
from database.utils.logging_config import get_logger

from .charts import ChartBuilder, ChartConfig

logger = get_logger(__name__)


# =============================================================================
# HeatmapChart
# =============================================================================


class HeatmapChart(ChartBuilder):
    """Heatmap chart builder for correlation matrices.

    Creates heatmap visualizations with:
    - Correlation values annotated in each cell
    - Color scale from -1 (negative) to +1 (positive)
    - Customizable themes and export formats

    Parameters
    ----------
    correlation_matrix : pd.DataFrame | CorrelationResult
        Correlation matrix data. Can be a DataFrame or CorrelationResult.
    config : ChartConfig | None
        Chart configuration
    show_values : bool, default=True
        Whether to show correlation values in cells
    value_format : str, default=".2f"
        Format string for correlation values
    colorscale : str | list | None, default=None
        Custom colorscale. If None, uses "RdBu_r" (red-blue reversed)

    Examples
    --------
    >>> corr_matrix = df.corr()
    >>> chart = HeatmapChart(corr_matrix)
    >>> chart.build().save("correlation_heatmap.png")

    >>> result = CorrelationAnalyzer().analyze(data)
    >>> chart = HeatmapChart(result, config=ChartConfig(title="Correlation Matrix"))
    >>> chart.build().save("heatmap.svg")
    """

    def __init__(
        self,
        correlation_matrix: pd.DataFrame | CorrelationResult,
        config: ChartConfig | None = None,
        *,
        show_values: bool = True,
        value_format: str = ".2f",
        colorscale: str | list[list[float | str]] | None = None,
    ) -> None:
        """Initialize HeatmapChart.

        Parameters
        ----------
        correlation_matrix : pd.DataFrame | CorrelationResult
            Correlation matrix data
        config : ChartConfig | None
            Chart configuration
        show_values : bool, default=True
            Whether to show correlation values in cells
        value_format : str, default=".2f"
            Format string for correlation values
        colorscale : str | list | None, default=None
            Custom colorscale for the heatmap
        """
        super().__init__(config)

        # Handle CorrelationResult input
        if isinstance(correlation_matrix, CorrelationResult):
            self._matrix = correlation_matrix.correlation_matrix
            self._symbols = correlation_matrix.symbols
            self._method = correlation_matrix.method
        else:
            self._matrix = correlation_matrix
            self._symbols = list(correlation_matrix.columns)
            self._method = "pearson"

        self._show_values = show_values
        self._value_format = value_format
        self._colorscale = colorscale

        logger.debug(
            "HeatmapChart initialized",
            symbols=self._symbols,
            show_values=show_values,
            matrix_shape=self._matrix.shape,
        )

    def build(self) -> "HeatmapChart":
        """Build the heatmap chart.

        Returns
        -------
        HeatmapChart
            Self for method chaining

        Raises
        ------
        ValueError
            If correlation matrix is empty
        """
        logger.info(
            "Building heatmap chart",
            symbols=self._symbols,
            show_values=self._show_values,
        )

        if self._matrix.empty:
            logger.warning("Empty correlation matrix provided")
            self._figure = go.Figure()
            self._apply_theme()
            return self

        # Prepare data
        z_values = self._matrix.values
        x_labels = list(self._matrix.columns)
        y_labels = list(self._matrix.index)

        # Determine colorscale
        colorscale = self._colorscale or self._get_default_colorscale()

        # Create annotation text
        annotations = self._create_annotations(z_values, x_labels, y_labels)

        # Create heatmap
        self._figure = go.Figure(
            data=go.Heatmap(
                z=z_values,
                x=x_labels,
                y=y_labels,
                colorscale=colorscale,
                zmin=-1,
                zmax=1,
                colorbar={
                    "title": "Correlation",
                    "tickvals": [-1, -0.5, 0, 0.5, 1],
                    "ticktext": ["-1.0", "-0.5", "0.0", "0.5", "1.0"],
                },
                hoverongaps=False,
                hovertemplate=(
                    "<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>"
                ),
            )
        )

        # Add annotations if enabled
        if self._show_values:
            self._figure.update_layout(annotations=annotations)

        # Apply theme
        self._apply_theme()

        # Additional layout adjustments for heatmap
        self._figure.update_layout(
            xaxis={
                "side": "bottom",
                "tickangle": -45 if len(x_labels) > 5 else 0,
            },
            yaxis={"autorange": "reversed"},  # Match matrix orientation
        )

        logger.info(
            "Heatmap chart built",
            symbols_count=len(self._symbols),
            annotations_count=len(annotations) if self._show_values else 0,
        )

        return self

    def _get_default_colorscale(self) -> list[list[float | str]]:
        """Get default colorscale based on theme.

        Returns
        -------
        list[list[float | str]]
            Colorscale definition
        """
        # Red-Blue reversed colorscale (blue for positive, red for negative)
        return [
            [0.0, self._colors.negative],  # -1: red/negative color
            [0.5, "#FFFFFF"],  # 0: white
            [1.0, self._colors.positive],  # +1: green/positive color
        ]

    def _create_annotations(
        self,
        z_values: np.ndarray,
        x_labels: list[str],
        y_labels: list[str],
    ) -> list[dict[str, Any]]:
        """Create text annotations for each cell.

        Parameters
        ----------
        z_values : np.ndarray
            Matrix of correlation values
        x_labels : list[str]
            Column labels
        y_labels : list[str]
            Row labels

        Returns
        -------
        list[dict[str, Any]]
            List of annotation dictionaries
        """
        annotations = []

        for i, y_label in enumerate(y_labels):
            for j, x_label in enumerate(x_labels):
                value = z_values[i, j]

                # Skip NaN values
                if np.isnan(value):
                    continue

                # Determine text color based on value
                # Use dark text for light backgrounds, light text for dark backgrounds
                text_color = (
                    self._colors.text
                    if abs(value) < 0.5
                    else "#FFFFFF"
                    if value < 0
                    else "#000000"
                )

                annotations.append(
                    {
                        "x": x_label,
                        "y": y_label,
                        "text": f"{value:{self._value_format}}",
                        "font": {
                            "color": text_color,
                            "size": self.config.axis_font_size,
                        },
                        "showarrow": False,
                        "xref": "x",
                        "yref": "y",
                    }
                )

        return annotations


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "HeatmapChart",
]
