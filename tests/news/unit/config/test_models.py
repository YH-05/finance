"""Unit tests for configuration Pydantic models."""

import pytest
from pydantic import ValidationError


class TestRetryConfig:
    """Test RetryConfig Pydantic model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """RetryConfigをデフォルト値で作成できることを確認。"""
        from news.config.models import RetryConfig

        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay == 1.0

    def test_正常系_カスタム値で作成できる(self) -> None:
        """RetryConfigをカスタム値で作成できることを確認。"""
        from news.config.models import RetryConfig

        config = RetryConfig(max_attempts=5, initial_delay=2.0)

        assert config.max_attempts == 5
        assert config.initial_delay == 2.0

    def test_異常系_負の値でValidationError(self) -> None:
        """max_attemptsが負の値の場合、ValidationErrorが発生することを確認。"""
        from news.config.models import RetryConfig

        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=-1)


class TestYFinanceTickerSourceConfig:
    """Test YFinanceTickerSourceConfig Pydantic model."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """YFinanceTickerSourceConfigを必須パラメータで作成できることを確認。"""
        from news.config.models import YFinanceTickerSourceConfig

        config = YFinanceTickerSourceConfig(
            symbols_file="src/analyze/config/symbols.yaml"
        )

        assert config.enabled is True  # デフォルト値
        assert config.symbols_file == "src/analyze/config/symbols.yaml"
        assert config.categories == []  # デフォルト値

    def test_正常系_全パラメータで作成できる(self) -> None:
        """YFinanceTickerSourceConfigを全パラメータで作成できることを確認。"""
        from news.config.models import YFinanceTickerSourceConfig

        config = YFinanceTickerSourceConfig(
            enabled=False,
            symbols_file="src/analyze/config/symbols.yaml",
            categories=["indices", "mag7", "sectors"],
        )

        assert config.enabled is False
        assert config.symbols_file == "src/analyze/config/symbols.yaml"
        assert config.categories == ["indices", "mag7", "sectors"]

    def test_異常系_symbols_file未指定でValidationError(self) -> None:
        """symbols_fileが未指定の場合、ValidationErrorが発生することを確認。"""
        from news.config.models import YFinanceTickerSourceConfig

        with pytest.raises(ValidationError):
            YFinanceTickerSourceConfig()  # type: ignore[call-arg]


class TestYFinanceSearchSourceConfig:
    """Test YFinanceSearchSourceConfig Pydantic model."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """YFinanceSearchSourceConfigを必須パラメータで作成できることを確認。"""
        from news.config.models import YFinanceSearchSourceConfig

        config = YFinanceSearchSourceConfig(
            keywords_file="data/config/news_search_keywords.yaml"
        )

        assert config.enabled is True  # デフォルト値
        assert config.keywords_file == "data/config/news_search_keywords.yaml"

    def test_正常系_enabled無効化できる(self) -> None:
        """YFinanceSearchSourceConfigをenabled=Falseで作成できることを確認。"""
        from news.config.models import YFinanceSearchSourceConfig

        config = YFinanceSearchSourceConfig(
            enabled=False,
            keywords_file="data/config/news_search_keywords.yaml",
        )

        assert config.enabled is False


class TestSourcesConfig:
    """Test SourcesConfig Pydantic model."""

    def test_正常系_空の設定で作成できる(self) -> None:
        """SourcesConfigを空の設定で作成できることを確認。"""
        from news.config.models import SourcesConfig

        config = SourcesConfig()

        assert config.yfinance_ticker is None
        assert config.yfinance_search is None

    def test_正常系_yfinance_ticker設定で作成できる(self) -> None:
        """SourcesConfigをyfinance_ticker設定で作成できることを確認。"""
        from news.config.models import SourcesConfig, YFinanceTickerSourceConfig

        ticker_config = YFinanceTickerSourceConfig(
            symbols_file="src/analyze/config/symbols.yaml",
            categories=["indices", "mag7"],
        )
        config = SourcesConfig(yfinance_ticker=ticker_config)

        assert config.yfinance_ticker is not None
        assert config.yfinance_ticker.categories == ["indices", "mag7"]


class TestFileSinkConfig:
    """Test FileSinkConfig Pydantic model."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """FileSinkConfigを必須パラメータで作成できることを確認。"""
        from news.config.models import FileSinkConfig

        config = FileSinkConfig(output_dir="data/news")

        assert config.enabled is True  # デフォルト値
        assert config.output_dir == "data/news"
        assert config.filename_pattern == "news_{date}.json"  # デフォルト値

    def test_正常系_全パラメータで作成できる(self) -> None:
        """FileSinkConfigを全パラメータで作成できることを確認。"""
        from news.config.models import FileSinkConfig

        config = FileSinkConfig(
            enabled=False,
            output_dir="data/output",
            filename_pattern="articles_{date}.json",
        )

        assert config.enabled is False
        assert config.output_dir == "data/output"
        assert config.filename_pattern == "articles_{date}.json"


class TestGitHubSinkConfig:
    """Test GitHubSinkConfig Pydantic model."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """GitHubSinkConfigを必須パラメータで作成できることを確認。"""
        from news.config.models import GitHubSinkConfig

        config = GitHubSinkConfig(project_number=24)

        assert config.enabled is True  # デフォルト値
        assert config.project_number == 24

    def test_正常系_enabled無効化できる(self) -> None:
        """GitHubSinkConfigをenabled=Falseで作成できることを確認。"""
        from news.config.models import GitHubSinkConfig

        config = GitHubSinkConfig(enabled=False, project_number=24)

        assert config.enabled is False

    def test_異常系_負のproject_numberでValidationError(self) -> None:
        """project_numberが負の値の場合、ValidationErrorが発生することを確認。"""
        from news.config.models import GitHubSinkConfig

        with pytest.raises(ValidationError):
            GitHubSinkConfig(project_number=-1)


class TestSinksConfig:
    """Test SinksConfig Pydantic model."""

    def test_正常系_空の設定で作成できる(self) -> None:
        """SinksConfigを空の設定で作成できることを確認。"""
        from news.config.models import SinksConfig

        config = SinksConfig()

        assert config.file is None
        assert config.github is None

    def test_正常系_file設定で作成できる(self) -> None:
        """SinksConfigをfile設定で作成できることを確認。"""
        from news.config.models import FileSinkConfig, SinksConfig

        file_config = FileSinkConfig(output_dir="data/news")
        config = SinksConfig(file=file_config)

        assert config.file is not None
        assert config.file.output_dir == "data/news"


class TestSettingsConfig:
    """Test SettingsConfig Pydantic model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """SettingsConfigをデフォルト値で作成できることを確認。"""
        from news.config.models import SettingsConfig

        config = SettingsConfig()

        assert config.max_articles_per_source == 10
        assert config.retry_config is not None
        assert config.retry_config.max_attempts == 3

    def test_正常系_カスタム値で作成できる(self) -> None:
        """SettingsConfigをカスタム値で作成できることを確認。"""
        from news.config.models import RetryConfig, SettingsConfig

        config = SettingsConfig(
            max_articles_per_source=20,
            retry_config=RetryConfig(max_attempts=5),
        )

        assert config.max_articles_per_source == 20
        assert config.retry_config.max_attempts == 5


class TestNewsConfig:
    """Test NewsConfig root Pydantic model."""

    def test_正常系_空の設定で作成できる(self) -> None:
        """NewsConfigを空の設定で作成できることを確認。"""
        from news.config.models import NewsConfig

        config = NewsConfig()

        assert config.sources is not None
        assert config.sinks is not None
        assert config.settings is not None

    def test_正常系_完全な設定で作成できる(self) -> None:
        """NewsConfigを完全な設定で作成できることを確認。"""
        from news.config.models import (
            FileSinkConfig,
            GitHubSinkConfig,
            NewsConfig,
            SettingsConfig,
            SinksConfig,
            SourcesConfig,
            YFinanceTickerSourceConfig,
        )

        sources = SourcesConfig(
            yfinance_ticker=YFinanceTickerSourceConfig(
                symbols_file="src/analyze/config/symbols.yaml",
                categories=["indices", "mag7"],
            )
        )
        sinks = SinksConfig(
            file=FileSinkConfig(output_dir="data/news"),
            github=GitHubSinkConfig(enabled=False, project_number=24),
        )
        settings = SettingsConfig(max_articles_per_source=15)

        config = NewsConfig(sources=sources, sinks=sinks, settings=settings)

        assert config.sources.yfinance_ticker is not None
        assert config.sinks.file is not None
        assert config.sinks.github is not None
        assert config.sinks.github.enabled is False
        assert config.settings.max_articles_per_source == 15

    def test_正常系_dictから作成できる(self) -> None:
        """NewsConfigを辞書から作成できることを確認。"""
        from news.config.models import NewsConfig

        data = {
            "sources": {
                "yfinance_ticker": {
                    "enabled": True,
                    "symbols_file": "src/analyze/config/symbols.yaml",
                    "categories": ["indices"],
                }
            },
            "sinks": {
                "file": {
                    "enabled": True,
                    "output_dir": "data/news",
                }
            },
            "settings": {
                "max_articles_per_source": 5,
            },
        }

        config = NewsConfig.model_validate(data)

        assert config.sources.yfinance_ticker is not None
        assert (
            config.sources.yfinance_ticker.symbols_file
            == "src/analyze/config/symbols.yaml"
        )
        assert config.sinks.file is not None
        assert config.settings.max_articles_per_source == 5
