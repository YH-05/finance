"""Unit tests for charts module."""

from pathlib import Path
from unittest.mock import patch

import plotly.graph_objects as go
import pytest
from analyze.visualization.charts import (
    DARK_THEME_COLORS,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    JAPANESE_FONT_STACK,
    LIGHT_THEME_COLORS,
    ChartBuilder,
    ChartConfig,
    ChartTheme,
    ExportFormat,
    get_theme_colors,
)

# =============================================================================
# Concrete Implementation for Testing
# =============================================================================


class ConcreteChartBuilder(ChartBuilder):
    """Concrete implementation of ChartBuilder for testing."""

    def __init__(
        self,
        config: ChartConfig | None = None,
        data: list[float] | None = None,
    ) -> None:
        """Initialize with optional data."""
        super().__init__(config)
        self.data = data or [1, 2, 3, 4, 5]

    def build(self) -> "ConcreteChartBuilder":
        """Build a simple line chart."""
        self._figure = go.Figure(
            data=[go.Scatter(x=list(range(len(self.data))), y=self.data, mode="lines")]
        )
        self._apply_theme()
        return self


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def default_config() -> ChartConfig:
    """Create a default ChartConfig."""
    return ChartConfig()


@pytest.fixture
def dark_config() -> ChartConfig:
    """Create a ChartConfig with dark theme."""
    return ChartConfig(theme=ChartTheme.DARK, title="Test Chart")


@pytest.fixture
def builder() -> ConcreteChartBuilder:
    """Create a default ConcreteChartBuilder."""
    return ConcreteChartBuilder()


@pytest.fixture
def built_builder() -> ConcreteChartBuilder:
    """Create a ConcreteChartBuilder with built figure."""
    builder = ConcreteChartBuilder()
    builder.build()
    return builder


# =============================================================================
# ThemeColors Tests
# =============================================================================


class TestThemeColors:
    """Tests for ThemeColors dataclass."""

    def test_正常系_ライトテーマカラーが定義されている(self) -> None:
        """ライトテーマのカラーパレットが正しく定義されていることを確認。"""
        assert LIGHT_THEME_COLORS.background == "#FFFFFF"
        assert LIGHT_THEME_COLORS.text == "#2E2E2E"
        assert len(LIGHT_THEME_COLORS.series_colors) > 0

    def test_正常系_ダークテーマカラーが定義されている(self) -> None:
        """ダークテーマのカラーパレットが正しく定義されていることを確認。"""
        assert DARK_THEME_COLORS.background == "#1E1E1E"
        assert DARK_THEME_COLORS.text == "#E0E0E0"
        assert len(DARK_THEME_COLORS.series_colors) > 0

    def test_正常系_テーマカラーはフローズン(self) -> None:
        """ThemeColorsがイミュータブルであることを確認。"""
        with pytest.raises(AttributeError):
            LIGHT_THEME_COLORS.background = "#000000"


class TestGetThemeColors:
    """Tests for get_theme_colors function."""

    def test_正常系_ライトテーマ取得(self) -> None:
        """ライトテーマのカラーを取得できることを確認。"""
        colors = get_theme_colors(ChartTheme.LIGHT)
        assert colors == LIGHT_THEME_COLORS

    def test_正常系_ダークテーマ取得(self) -> None:
        """ダークテーマのカラーを取得できることを確認。"""
        colors = get_theme_colors(ChartTheme.DARK)
        assert colors == DARK_THEME_COLORS

    def test_正常系_文字列でテーマ指定(self) -> None:
        """文字列でテーマを指定できることを確認。"""
        colors = get_theme_colors("dark")
        assert colors == DARK_THEME_COLORS

    def test_異常系_無効なテーマ文字列(self) -> None:
        """無効なテーマ文字列でValueErrorが発生することを確認。"""
        with pytest.raises(ValueError):
            get_theme_colors("invalid_theme")


# =============================================================================
# ChartConfig Tests
# =============================================================================


class TestChartConfig:
    """Tests for ChartConfig dataclass."""

    def test_正常系_デフォルト値で初期化(self, default_config: ChartConfig) -> None:
        """デフォルト値で初期化されることを確認。"""
        assert default_config.width == DEFAULT_WIDTH
        assert default_config.height == DEFAULT_HEIGHT
        assert default_config.theme == ChartTheme.LIGHT
        assert default_config.title is None
        assert default_config.show_legend is True

    def test_正常系_カスタム値で初期化(self) -> None:
        """カスタム値で初期化できることを確認。"""
        config = ChartConfig(
            width=800,
            height=400,
            theme=ChartTheme.DARK,
            title="Custom Title",
            show_legend=False,
        )
        assert config.width == 800
        assert config.height == 400
        assert config.theme == ChartTheme.DARK
        assert config.title == "Custom Title"
        assert config.show_legend is False

    def test_正常系_文字列でテーマ指定(self) -> None:
        """文字列でテーマを指定できることを確認。"""
        config = ChartConfig(theme="dark")  # type: ignore[arg-type]
        assert config.theme == ChartTheme.DARK

    def test_異常系_幅が0以下でValueError(self) -> None:
        """幅が0以下の場合、ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="Width must be positive"):
            ChartConfig(width=0)

    def test_異常系_高さが0以下でValueError(self) -> None:
        """高さが0以下の場合、ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="Height must be positive"):
            ChartConfig(height=-100)


# =============================================================================
# ChartBuilder Tests
# =============================================================================


class TestChartBuilder:
    """Tests for ChartBuilder abstract base class."""

    def test_正常系_初期化(self, builder: ConcreteChartBuilder) -> None:
        """ChartBuilderが正しく初期化されることを確認。"""
        assert builder.config is not None
        assert builder.figure is None
        assert builder.colors == LIGHT_THEME_COLORS

    def test_正常系_カスタム設定で初期化(self, dark_config: ChartConfig) -> None:
        """カスタム設定で初期化できることを確認。"""
        builder = ConcreteChartBuilder(dark_config)
        assert builder.config.theme == ChartTheme.DARK
        assert builder.colors == DARK_THEME_COLORS

    def test_正常系_buildでfigureが作成される(
        self, builder: ConcreteChartBuilder
    ) -> None:
        """build()でfigureが作成されることを確認。"""
        assert builder.figure is None
        builder.build()
        assert builder.figure is not None
        assert isinstance(builder.figure, go.Figure)

    def test_正常系_buildはメソッドチェーン可能(
        self, builder: ConcreteChartBuilder
    ) -> None:
        """build()がselfを返すことを確認。"""
        result = builder.build()
        assert result is builder


class TestChartBuilderSetTheme:
    """Tests for ChartBuilder.set_theme method."""

    def test_正常系_テーマ変更(self, builder: ConcreteChartBuilder) -> None:
        """テーマを変更できることを確認。"""
        assert builder.colors == LIGHT_THEME_COLORS
        builder.set_theme(ChartTheme.DARK)
        assert builder.colors == DARK_THEME_COLORS
        assert builder.config.theme == ChartTheme.DARK

    def test_正常系_文字列でテーマ変更(self, builder: ConcreteChartBuilder) -> None:
        """文字列でテーマを変更できることを確認。"""
        builder.set_theme("dark")
        assert builder.config.theme == ChartTheme.DARK

    def test_正常系_テーマ変更はメソッドチェーン可能(
        self, builder: ConcreteChartBuilder
    ) -> None:
        """set_theme()がselfを返すことを確認。"""
        result = builder.set_theme(ChartTheme.DARK)
        assert result is builder

    def test_正常系_ビルド後のテーマ変更でレイアウト更新(
        self, built_builder: ConcreteChartBuilder
    ) -> None:
        """ビルド後にテーマを変更するとレイアウトが更新されることを確認。"""
        built_builder.set_theme(ChartTheme.DARK)
        layout = built_builder.figure.layout  # type: ignore[union-attr]
        assert layout.paper_bgcolor == DARK_THEME_COLORS.paper


class TestChartBuilderShow:
    """Tests for ChartBuilder.show method."""

    def test_正常系_showが呼び出せる(self, built_builder: ConcreteChartBuilder) -> None:
        """show()が呼び出せることを確認。"""
        with patch.object(built_builder.figure, "show") as mock_show:
            result = built_builder.show()
            mock_show.assert_called_once()
            assert result is built_builder

    def test_異常系_ビルド前にshowでRuntimeError(
        self, builder: ConcreteChartBuilder
    ) -> None:
        """ビルド前にshow()を呼ぶとRuntimeErrorが発生することを確認。"""
        with pytest.raises(RuntimeError, match="Chart not built"):
            builder.show()


class TestChartBuilderSave:
    """Tests for ChartBuilder.save method."""

    def test_正常系_PNG保存(
        self, built_builder: ConcreteChartBuilder, tmp_path: Path
    ) -> None:
        """PNG形式で保存できることを確認。"""
        output_path = tmp_path / "test_chart.png"

        with patch("plotly.io.write_image") as mock_write:
            built_builder.save(output_path)
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert call_args.kwargs["format"] == "png"

    def test_正常系_SVG保存(
        self, built_builder: ConcreteChartBuilder, tmp_path: Path
    ) -> None:
        """SVG形式で保存できることを確認。"""
        output_path = tmp_path / "test_chart.svg"

        with patch("plotly.io.write_image") as mock_write:
            built_builder.save(output_path)
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert call_args.kwargs["format"] == "svg"

    def test_正常系_HTML保存(
        self, built_builder: ConcreteChartBuilder, tmp_path: Path
    ) -> None:
        """HTML形式で保存できることを確認。"""
        output_path = tmp_path / "test_chart.html"

        with patch.object(built_builder.figure, "write_html") as mock_write:
            built_builder.save(output_path)
            mock_write.assert_called_once()

    def test_正常系_フォーマット明示指定(
        self, built_builder: ConcreteChartBuilder, tmp_path: Path
    ) -> None:
        """フォーマットを明示的に指定できることを確認。"""
        output_path = tmp_path / "test_chart.xyz"

        with patch("plotly.io.write_image") as mock_write:
            built_builder.save(output_path, format=ExportFormat.PNG)
            mock_write.assert_called_once()

    def test_正常系_saveはメソッドチェーン可能(
        self, built_builder: ConcreteChartBuilder, tmp_path: Path
    ) -> None:
        """save()がselfを返すことを確認。"""
        output_path = tmp_path / "test_chart.html"

        with patch.object(built_builder.figure, "write_html"):
            result = built_builder.save(output_path)
            assert result is built_builder

    def test_異常系_ビルド前にsaveでRuntimeError(
        self, builder: ConcreteChartBuilder, tmp_path: Path
    ) -> None:
        """ビルド前にsave()を呼ぶとRuntimeErrorが発生することを確認。"""
        with pytest.raises(RuntimeError, match="Chart not built"):
            builder.save(tmp_path / "test.png")

    def test_異常系_未知の拡張子でValueError(
        self, built_builder: ConcreteChartBuilder, tmp_path: Path
    ) -> None:
        """未知の拡張子でValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="Cannot infer format"):
            built_builder.save(tmp_path / "test.unknown")


class TestChartBuilderToHtml:
    """Tests for ChartBuilder.to_html method."""

    def test_正常系_HTMLに変換(self, built_builder: ConcreteChartBuilder) -> None:
        """to_html()でHTML文字列が返されることを確認。"""
        html = built_builder.to_html()
        assert isinstance(html, str)
        assert "<html>" in html or "<div" in html

    def test_異常系_ビルド前にto_htmlでRuntimeError(
        self, builder: ConcreteChartBuilder
    ) -> None:
        """ビルド前にto_html()を呼ぶとRuntimeErrorが発生することを確認。"""
        with pytest.raises(RuntimeError, match="Chart not built"):
            builder.to_html()


class TestChartBuilderUpdateLayout:
    """Tests for ChartBuilder.update_layout method."""

    def test_正常系_レイアウト更新(self, built_builder: ConcreteChartBuilder) -> None:
        """update_layout()でレイアウトが更新されることを確認。"""
        built_builder.update_layout(title_text="Updated Title")
        layout = built_builder.figure.layout  # type: ignore[union-attr]
        assert layout.title.text == "Updated Title"

    def test_正常系_update_layoutはメソッドチェーン可能(
        self, built_builder: ConcreteChartBuilder
    ) -> None:
        """update_layout()がselfを返すことを確認。"""
        result = built_builder.update_layout(title_text="Test")
        assert result is built_builder

    def test_異常系_ビルド前にupdate_layoutでRuntimeError(
        self, builder: ConcreteChartBuilder
    ) -> None:
        """ビルド前にupdate_layout()を呼ぶとRuntimeErrorが発生することを確認。"""
        with pytest.raises(RuntimeError, match="Chart not built"):
            builder.update_layout(title_text="Test")


class TestChartBuilderThemeApplication:
    """Tests for theme application in ChartBuilder."""

    def test_正常系_ライトテーマが適用される(self) -> None:
        """ライトテーマが正しく適用されることを確認。"""
        config = ChartConfig(theme=ChartTheme.LIGHT, title="Test")
        builder = ConcreteChartBuilder(config).build()

        layout = builder.figure.layout  # type: ignore[union-attr]
        assert layout.paper_bgcolor == LIGHT_THEME_COLORS.paper
        assert layout.plot_bgcolor == LIGHT_THEME_COLORS.background

    def test_正常系_ダークテーマが適用される(self) -> None:
        """ダークテーマが正しく適用されることを確認。"""
        config = ChartConfig(theme=ChartTheme.DARK, title="Test")
        builder = ConcreteChartBuilder(config).build()

        layout = builder.figure.layout  # type: ignore[union-attr]
        assert layout.paper_bgcolor == DARK_THEME_COLORS.paper
        assert layout.plot_bgcolor == DARK_THEME_COLORS.background

    def test_正常系_日本語フォントが設定される(
        self, built_builder: ConcreteChartBuilder
    ) -> None:
        """日本語フォントが設定されることを確認。"""
        layout = built_builder.figure.layout  # type: ignore[union-attr]
        assert JAPANESE_FONT_STACK in layout.font.family

    def test_正常系_凡例位置が設定される(self) -> None:
        """凡例位置が正しく設定されることを確認。"""
        config = ChartConfig(legend_position="bottom")
        builder = ConcreteChartBuilder(config).build()

        layout = builder.figure.layout  # type: ignore[union-attr]
        assert layout.legend.y < 0  # bottom position


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_正常系_すべてのフォーマットが定義されている(self) -> None:
        """すべてのエクスポートフォーマットが定義されていることを確認。"""
        assert ExportFormat.PNG.value == "png"
        assert ExportFormat.SVG.value == "svg"
        assert ExportFormat.HTML.value == "html"

    def test_正常系_文字列から変換(self) -> None:
        """文字列からExportFormatに変換できることを確認。"""
        assert ExportFormat("png") == ExportFormat.PNG
        assert ExportFormat("svg") == ExportFormat.SVG
        assert ExportFormat("html") == ExportFormat.HTML
