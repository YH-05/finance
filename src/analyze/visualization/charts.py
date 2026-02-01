"""Chart builder base module for creating financial visualizations.

This module provides the abstract base class for building charts using Plotly,
with support for themes, common layouts, and export functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio
from utils_core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class ChartTheme(str, Enum):
    """Chart theme options.

    Attributes
    ----------
    LIGHT : str
        Light theme with white background
    DARK : str
        Dark theme with dark background
    """

    LIGHT = "light"
    DARK = "dark"


class ExportFormat(str, Enum):
    """Export format options.

    Attributes
    ----------
    PNG : str
        PNG image format
    SVG : str
        SVG vector format
    HTML : str
        Interactive HTML format
    """

    PNG = "png"
    SVG = "svg"
    HTML = "html"


# Japanese font stack - prioritize common Japanese fonts
JAPANESE_FONT_STACK = (
    "Hiragino Sans, Hiragino Kaku Gothic ProN, "
    "Noto Sans JP, Yu Gothic, Meiryo, sans-serif"
)

# Default chart dimensions
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 600


# =============================================================================
# Theme Definitions
# =============================================================================


@dataclass(frozen=True)
class ThemeColors:
    """Color palette for a chart theme.

    Parameters
    ----------
    background : str
        Background color
    paper : str
        Paper/plot area background color
    text : str
        Primary text color
    grid : str
        Grid line color
    axis : str
        Axis line color
    positive : str
        Color for positive values (e.g., price increase)
    negative : str
        Color for negative values (e.g., price decrease)
    accent : str
        Accent color for highlights
    series_colors : tuple[str, ...]
        Default color sequence for data series
    """

    background: str
    paper: str
    text: str
    grid: str
    axis: str
    positive: str
    negative: str
    accent: str
    series_colors: tuple[str, ...] = field(
        default_factory=lambda: (
            "#636EFA",
            "#EF553B",
            "#00CC96",
            "#AB63FA",
            "#FFA15A",
            "#19D3F3",
            "#FF6692",
            "#B6E880",
        )
    )


LIGHT_THEME_COLORS = ThemeColors(
    background="#FFFFFF",
    paper="#FFFFFF",
    text="#2E2E2E",
    grid="#E5E5E5",
    axis="#2E2E2E",
    positive="#26A69A",
    negative="#EF5350",
    accent="#1976D2",
    series_colors=(
        "#1976D2",
        "#D32F2F",
        "#388E3C",
        "#7B1FA2",
        "#F57C00",
        "#0097A7",
        "#C2185B",
        "#689F38",
    ),
)

DARK_THEME_COLORS = ThemeColors(
    background="#1E1E1E",
    paper="#1E1E1E",
    text="#E0E0E0",
    grid="#3D3D3D",
    axis="#E0E0E0",
    positive="#4CAF50",
    negative="#F44336",
    accent="#2196F3",
    series_colors=(
        "#2196F3",
        "#F44336",
        "#4CAF50",
        "#9C27B0",
        "#FF9800",
        "#00BCD4",
        "#E91E63",
        "#8BC34A",
    ),
)


def get_theme_colors(theme: ChartTheme | str) -> ThemeColors:
    """Get color palette for the specified theme.

    Parameters
    ----------
    theme : ChartTheme | str
        Theme name or enum value

    Returns
    -------
    ThemeColors
        Color palette for the theme

    Examples
    --------
    >>> colors = get_theme_colors(ChartTheme.DARK)
    >>> colors.background
    '#1E1E1E'
    """
    if isinstance(theme, str):  # type: ignore[reportUnnecessaryIsInstance]
        theme = ChartTheme(theme)

    if theme == ChartTheme.DARK:
        return DARK_THEME_COLORS
    return LIGHT_THEME_COLORS


# =============================================================================
# Chart Configuration
# =============================================================================


@dataclass
class ChartConfig:
    """Configuration for chart appearance and behavior.

    Parameters
    ----------
    width : int
        Chart width in pixels (default: 1200)
    height : int
        Chart height in pixels (default: 600)
    theme : ChartTheme
        Chart theme (default: LIGHT)
    title : str | None
        Chart title
    title_font_size : int
        Title font size in pixels (default: 18)
    axis_font_size : int
        Axis label font size in pixels (default: 12)
    legend_font_size : int
        Legend font size in pixels (default: 11)
    show_legend : bool
        Whether to show legend (default: True)
    legend_position : str
        Legend position: "top", "bottom", "left", "right" (default: "top")
    margin : dict[str, int] | None
        Chart margins (l, r, t, b)
    """

    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    theme: ChartTheme = ChartTheme.LIGHT
    title: str | None = None
    title_font_size: int = 18
    axis_font_size: int = 12
    legend_font_size: int = 11
    show_legend: bool = True
    legend_position: str = "top"
    margin: dict[str, int] | None = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        logger.debug(
            "Initializing ChartConfig",
            width=self.width,
            height=self.height,
            theme=self.theme.value
            if isinstance(self.theme, ChartTheme)  # type: ignore[reportUnnecessaryIsInstance]
            else self.theme,
        )

        if self.width <= 0:
            raise ValueError(f"Width must be positive, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"Height must be positive, got {self.height}")

        # Convert string theme to enum
        if isinstance(self.theme, str):  # type: ignore[reportUnnecessaryIsInstance]
            self.theme = ChartTheme(self.theme)


# =============================================================================
# ChartBuilder Abstract Base Class
# =============================================================================


class ChartBuilder(ABC):
    """Abstract base class for building charts with Plotly.

    This class provides the foundation for creating consistent, themed charts
    with support for multiple export formats.

    Attributes
    ----------
    config : ChartConfig
        Chart configuration
    figure : go.Figure | None
        Built Plotly figure

    Examples
    --------
    >>> class LineChartBuilder(ChartBuilder):
    ...     def __init__(self, data, config=None):
    ...         super().__init__(config)
    ...         self.data = data
    ...
    ...     def build(self):
    ...         self._figure = go.Figure(data=[go.Scatter(x=self.data.index, y=self.data)])
    ...         self._apply_theme()
    ...         return self
    ...
    >>> builder = LineChartBuilder(data, ChartConfig(theme=ChartTheme.DARK))
    >>> builder.build().save("chart.png")
    """

    def __init__(self, config: ChartConfig | None = None) -> None:
        """Initialize ChartBuilder with configuration.

        Parameters
        ----------
        config : ChartConfig | None
            Chart configuration. If None, uses default configuration.
        """
        self.config = config or ChartConfig()
        self._figure: go.Figure | None = None
        self._colors = get_theme_colors(self.config.theme)

        logger.debug(
            "ChartBuilder initialized",
            builder_type=self.__class__.__name__,
            theme=self.config.theme.value,
            width=self.config.width,
            height=self.config.height,
        )

    @property
    def figure(self) -> go.Figure | None:
        """Get the built figure.

        Returns
        -------
        go.Figure | None
            The Plotly figure, or None if not yet built
        """
        return self._figure

    @property
    def colors(self) -> ThemeColors:
        """Get the current theme colors.

        Returns
        -------
        ThemeColors
            Current theme color palette
        """
        return self._colors

    def set_theme(self, theme: ChartTheme | str) -> "ChartBuilder":
        """Change the chart theme.

        Parameters
        ----------
        theme : ChartTheme | str
            New theme to apply

        Returns
        -------
        ChartBuilder
            Self for method chaining
        """
        if isinstance(theme, str):  # type: ignore[reportUnnecessaryIsInstance]
            theme = ChartTheme(theme)

        self.config.theme = theme
        self._colors = get_theme_colors(theme)

        logger.info("Theme changed", new_theme=theme.value)

        if self._figure is not None:
            self._apply_theme()

        return self

    @abstractmethod
    def build(self) -> "ChartBuilder":
        """Build the chart figure.

        This method must be implemented by subclasses to create the specific
        chart type. It should set self._figure and call self._apply_theme().

        Returns
        -------
        ChartBuilder
            Self for method chaining

        Examples
        --------
        >>> def build(self):
        ...     self._figure = go.Figure(data=[...])
        ...     self._apply_theme()
        ...     return self
        """
        ...

    def _apply_theme(self) -> None:
        """Apply the current theme to the figure.

        This method updates the figure layout with theme colors, fonts,
        and default styling.
        """
        if self._figure is None:
            logger.warning("Cannot apply theme: figure not built")
            return

        legend_config = self._get_legend_config()
        margin = self.config.margin or {"l": 60, "r": 40, "t": 60, "b": 60}

        self._figure.update_layout(
            # Dimensions
            width=self.config.width,
            height=self.config.height,
            # Colors
            paper_bgcolor=self._colors.paper,
            plot_bgcolor=self._colors.background,
            # Title
            title={
                "text": self.config.title,
                "font": {
                    "family": JAPANESE_FONT_STACK,
                    "size": self.config.title_font_size,
                    "color": self._colors.text,
                },
                "x": 0.5,
                "xanchor": "center",
            }
            if self.config.title
            else None,
            # Fonts
            font={
                "family": JAPANESE_FONT_STACK,
                "size": self.config.axis_font_size,
                "color": self._colors.text,
            },
            # Legend
            showlegend=self.config.show_legend,
            legend={
                **legend_config,
                "font": {
                    "family": JAPANESE_FONT_STACK,
                    "size": self.config.legend_font_size,
                    "color": self._colors.text,
                },
            },
            # Margins
            margin=margin,
            # Default color sequence
            colorway=self._colors.series_colors,
        )

        # Apply axis styling
        self._apply_axis_styling()

        logger.debug(
            "Theme applied",
            theme=self.config.theme.value,
            title=self.config.title,
        )

    def _apply_axis_styling(self) -> None:
        """Apply consistent styling to all axes."""
        if self._figure is None:
            return

        axis_style = {
            "gridcolor": self._colors.grid,
            "linecolor": self._colors.axis,
            "tickfont": {
                "family": JAPANESE_FONT_STACK,
                "size": self.config.axis_font_size,
                "color": self._colors.text,
            },
            "title_font": {
                "family": JAPANESE_FONT_STACK,
                "size": self.config.axis_font_size + 2,
                "color": self._colors.text,
            },
            "showgrid": True,
            "gridwidth": 1,
            "zeroline": False,
        }

        self._figure.update_xaxes(**axis_style)
        self._figure.update_yaxes(**axis_style)

    def _get_legend_config(self) -> dict[str, Any]:
        """Get legend configuration based on position setting.

        Returns
        -------
        dict[str, Any]
            Legend position and orientation settings
        """
        position_configs: dict[str, dict[str, Any]] = {
            "top": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
            "bottom": {
                "orientation": "h",
                "yanchor": "top",
                "y": -0.1,
                "xanchor": "center",
                "x": 0.5,
            },
            "left": {
                "orientation": "v",
                "yanchor": "middle",
                "y": 0.5,
                "xanchor": "right",
                "x": -0.1,
            },
            "right": {
                "orientation": "v",
                "yanchor": "middle",
                "y": 0.5,
                "xanchor": "left",
                "x": 1.02,
            },
        }

        return position_configs.get(
            self.config.legend_position, position_configs["top"]
        )

    def show(self) -> "ChartBuilder":
        """Display the chart in an interactive viewer.

        Returns
        -------
        ChartBuilder
            Self for method chaining

        Raises
        ------
        RuntimeError
            If the chart has not been built yet
        """
        if self._figure is None:
            logger.error("Cannot show chart: figure not built. Call build() first.")
            raise RuntimeError("Chart not built. Call build() first.")

        logger.info("Displaying chart")
        self._figure.show()
        return self

    def save(
        self,
        path: str | Path,
        format: ExportFormat | str | None = None,
        *,
        scale: float = 2.0,
    ) -> "ChartBuilder":
        """Save the chart to a file.

        Parameters
        ----------
        path : str | Path
            Output file path
        format : ExportFormat | str | None
            Export format. If None, inferred from file extension.
        scale : float
            Scale factor for raster formats (default: 2.0 for high DPI)

        Returns
        -------
        ChartBuilder
            Self for method chaining

        Raises
        ------
        RuntimeError
            If the chart has not been built yet
        ValueError
            If the export format is not supported

        Examples
        --------
        >>> builder.build().save("chart.png")
        >>> builder.save("chart.svg", format=ExportFormat.SVG)
        >>> builder.save("chart.html")
        """
        if self._figure is None:
            logger.error("Cannot save chart: figure not built. Call build() first.")
            raise RuntimeError("Chart not built. Call build() first.")

        path = Path(path)

        # Infer format from extension if not specified
        if format is None:
            ext = path.suffix.lower().lstrip(".")
            try:
                format = ExportFormat(ext)
            except ValueError as err:
                raise ValueError(
                    f"Cannot infer format from extension '{ext}'. "
                    f"Supported formats: {[f.value for f in ExportFormat]}"
                ) from err
        elif isinstance(format, str):  # type: ignore[reportUnnecessaryIsInstance]
            format = ExportFormat(format)

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Saving chart",
            path=str(path),
            format=format.value,
            scale=scale if format != ExportFormat.HTML else None,
        )

        if format == ExportFormat.HTML:
            self._figure.write_html(str(path), include_plotlyjs=True)
        elif format == ExportFormat.PNG:
            pio.write_image(self._figure, str(path), format="png", scale=scale)
        elif format == ExportFormat.SVG:
            pio.write_image(self._figure, str(path), format="svg")
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info("Chart saved successfully", path=str(path))
        return self

    def to_html(self, *, full_html: bool = True, include_plotlyjs: bool = True) -> str:
        """Convert the chart to HTML string.

        Parameters
        ----------
        full_html : bool
            Whether to include full HTML document structure (default: True)
        include_plotlyjs : bool
            Whether to include Plotly.js library (default: True)

        Returns
        -------
        str
            HTML representation of the chart

        Raises
        ------
        RuntimeError
            If the chart has not been built yet
        """
        if self._figure is None:
            logger.error(
                "Cannot convert to HTML: figure not built. Call build() first."
            )
            raise RuntimeError("Chart not built. Call build() first.")

        return self._figure.to_html(
            full_html=full_html,
            include_plotlyjs="cdn" if include_plotlyjs else False,
        )

    def update_layout(self, **kwargs: Any) -> "ChartBuilder":
        """Update figure layout with additional options.

        Parameters
        ----------
        **kwargs : Any
            Layout options to pass to figure.update_layout()

        Returns
        -------
        ChartBuilder
            Self for method chaining

        Raises
        ------
        RuntimeError
            If the chart has not been built yet
        """
        if self._figure is None:
            logger.error("Cannot update layout: figure not built. Call build() first.")
            raise RuntimeError("Chart not built. Call build() first.")

        self._figure.update_layout(**kwargs)
        logger.debug("Layout updated", options=list(kwargs.keys()))
        return self


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "DARK_THEME_COLORS",
    "DEFAULT_HEIGHT",
    "DEFAULT_WIDTH",
    "JAPANESE_FONT_STACK",
    "LIGHT_THEME_COLORS",
    "ChartBuilder",
    "ChartConfig",
    "ChartTheme",
    "ExportFormat",
    "ThemeColors",
    "get_theme_colors",
]
