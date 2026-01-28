"""Unit tests for ConfigLoader class."""

from pathlib import Path

import pytest


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_正常系_YAML設定ファイルを読み込める(self, tmp_path: Path) -> None:
        """ConfigLoaderがYAML設定ファイルを読み込めることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange: YAML設定ファイルを作成
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
sources:
  yfinance_ticker:
    enabled: true
    symbols_file: "src/analyze/config/symbols.yaml"
    categories:
      - indices
      - mag7

sinks:
  file:
    enabled: true
    output_dir: "data/news"

settings:
  max_articles_per_source: 10
"""
        )

        # Act
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Assert
        assert config.sources.yfinance_ticker is not None
        assert config.sources.yfinance_ticker.enabled is True
        assert config.sources.yfinance_ticker.categories == ["indices", "mag7"]
        assert config.sinks.file is not None
        assert config.sinks.file.output_dir == "data/news"
        assert config.settings.max_articles_per_source == 10

    def test_正常系_JSON設定ファイルを読み込める(self, tmp_path: Path) -> None:
        """ConfigLoaderがJSON設定ファイルを読み込めることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange: JSON設定ファイルを作成
        config_file = tmp_path / "config.json"
        config_file.write_text(
            """
{
  "sources": {
    "yfinance_ticker": {
      "enabled": true,
      "symbols_file": "src/analyze/config/symbols.yaml",
      "categories": ["indices"]
    }
  },
  "sinks": {
    "file": {
      "enabled": true,
      "output_dir": "data/news"
    }
  },
  "settings": {
    "max_articles_per_source": 5
  }
}
"""
        )

        # Act
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Assert
        assert config.sources.yfinance_ticker is not None
        assert config.sources.yfinance_ticker.categories == ["indices"]
        assert config.settings.max_articles_per_source == 5

    def test_異常系_存在しないファイルでFileNotFoundError(self) -> None:
        """存在しないファイルを読み込むとFileNotFoundErrorが発生することを確認。"""
        from news.config.loader import ConfigLoader

        loader = ConfigLoader()

        with pytest.raises(FileNotFoundError):
            loader.load(Path("/nonexistent/config.yaml"))

    def test_異常系_不正なYAMLでConfigParseError(self, tmp_path: Path) -> None:
        """不正なYAMLファイルを読み込むとConfigParseErrorが発生することを確認。"""
        from news.config.errors import ConfigParseError
        from news.config.loader import ConfigLoader

        # Arrange: 不正なYAMLファイルを作成
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text(
            """
sources:
  - this is invalid yaml structure
    without proper indentation
"""
        )

        # Act & Assert
        loader = ConfigLoader()
        with pytest.raises(ConfigParseError):
            loader.load(config_file)

    def test_異常系_不正なJSONでConfigParseError(self, tmp_path: Path) -> None:
        """不正なJSONファイルを読み込むとConfigParseErrorが発生することを確認。"""
        from news.config.errors import ConfigParseError
        from news.config.loader import ConfigLoader

        # Arrange: 不正なJSONファイルを作成
        config_file = tmp_path / "invalid.json"
        config_file.write_text(
            """
{
  "sources": {
    "yfinance_ticker": {
      "enabled": true,
    }
  }
}
"""  # trailing comma is invalid in JSON
        )

        # Act & Assert
        loader = ConfigLoader()
        with pytest.raises(ConfigParseError):
            loader.load(config_file)

    def test_異常系_未対応の拡張子でConfigParseError(self, tmp_path: Path) -> None:
        """未対応の拡張子を読み込むとConfigParseErrorが発生することを確認。"""
        from news.config.errors import ConfigParseError
        from news.config.loader import ConfigLoader

        # Arrange: 未対応の拡張子でファイルを作成
        config_file = tmp_path / "config.txt"
        config_file.write_text("some content")

        # Act & Assert
        loader = ConfigLoader()
        with pytest.raises(ConfigParseError, match="Unsupported file format"):
            loader.load(config_file)

    def test_エッジケース_空のYAMLファイルでデフォルト設定(
        self, tmp_path: Path
    ) -> None:
        """空のYAMLファイルを読み込むとデフォルト設定が適用されることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange: 空のYAMLファイルを作成
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        # Act
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Assert: デフォルト設定が適用される
        assert config.sources is not None
        assert config.sinks is not None
        assert config.settings is not None
        assert config.settings.max_articles_per_source == 10  # デフォルト値

    def test_正常系_文字列パスで読み込める(self, tmp_path: Path) -> None:
        """ConfigLoaderが文字列パスでも読み込めることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
settings:
  max_articles_per_source: 20
"""
        )

        # Act
        loader = ConfigLoader()
        config = loader.load(str(config_file))  # 文字列パスで呼び出し

        # Assert
        assert config.settings.max_articles_per_source == 20


class TestConfigLoaderLoadSymbols:
    """Test ConfigLoader.load_symbols method."""

    def test_正常系_symbols_yamlを読み込める(self, tmp_path: Path) -> None:
        """ConfigLoaderがsymbols.yamlを読み込めることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange: symbols.yamlを作成
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(
            """
indices:
  us:
    - symbol: "^GSPC"
      name: "S&P 500"
    - symbol: "^DJI"
      name: "Dow Jones"

mag7:
  - symbol: "AAPL"
    name: "Apple"
  - symbol: "MSFT"
    name: "Microsoft"

sectors:
  - symbol: "XLF"
    name: "Financial"
"""
        )

        # Act
        loader = ConfigLoader()
        symbols = loader.load_symbols(symbols_file)

        # Assert
        assert "indices" in symbols
        assert "mag7" in symbols
        assert "sectors" in symbols
        assert len(symbols["mag7"]) == 2
        assert symbols["mag7"][0]["symbol"] == "AAPL"

    def test_正常系_カテゴリを指定して読み込める(self, tmp_path: Path) -> None:
        """ConfigLoaderがカテゴリを指定してsymbols.yamlを読み込めることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(
            """
indices:
  us:
    - symbol: "^GSPC"
      name: "S&P 500"

mag7:
  - symbol: "AAPL"
    name: "Apple"

sectors:
  - symbol: "XLF"
    name: "Financial"
"""
        )

        # Act
        loader = ConfigLoader()
        symbols = loader.load_symbols(symbols_file, categories=["mag7", "sectors"])

        # Assert
        assert "indices" not in symbols
        assert "mag7" in symbols
        assert "sectors" in symbols

    def test_正常系_ティッカーシンボルのみ取得できる(self, tmp_path: Path) -> None:
        """ConfigLoaderがティッカーシンボルのみを取得できることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(
            """
mag7:
  - symbol: "AAPL"
    name: "Apple"
  - symbol: "MSFT"
    name: "Microsoft"
  - symbol: "GOOGL"
    name: "Alphabet"
"""
        )

        # Act
        loader = ConfigLoader()
        tickers = loader.get_ticker_symbols(symbols_file, categories=["mag7"])

        # Assert
        assert tickers == ["AAPL", "MSFT", "GOOGL"]

    def test_エッジケース_存在しないカテゴリは空で返す(self, tmp_path: Path) -> None:
        """存在しないカテゴリを指定すると空の結果が返されることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(
            """
mag7:
  - symbol: "AAPL"
    name: "Apple"
"""
        )

        # Act
        loader = ConfigLoader()
        symbols = loader.load_symbols(symbols_file, categories=["nonexistent_category"])

        # Assert
        assert symbols == {}

    def test_異常系_存在しないファイルでFileNotFoundError(self) -> None:
        """存在しないsymbolsファイルを読み込むとFileNotFoundErrorが発生することを確認。"""
        from news.config.loader import ConfigLoader

        loader = ConfigLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_symbols(Path("/nonexistent/symbols.yaml"))


class TestConfigLoaderLoadFromDefault:
    """Test ConfigLoader.load_from_default method."""

    def test_正常系_デフォルトパスから読み込める(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ConfigLoaderがデフォルトパスから設定を読み込めることを確認。"""
        from news.config.loader import ConfigLoader

        # Arrange: デフォルト設定ファイルを作成
        config_dir = tmp_path / "data" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "news_sources.yaml"
        config_file.write_text(
            """
settings:
  max_articles_per_source: 25
"""
        )

        # デフォルトパスをモック
        monkeypatch.setattr(
            "news.config.loader.DEFAULT_CONFIG_PATH",
            config_file,
        )

        # Act
        loader = ConfigLoader()
        config = loader.load_from_default()

        # Assert
        assert config.settings.max_articles_per_source == 25

    def test_正常系_デフォルトファイルがない場合はデフォルト設定(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """デフォルトファイルがない場合、デフォルト設定が返されることを確認。"""
        from news.config.loader import ConfigLoader

        # デフォルトパスを存在しないパスに設定
        monkeypatch.setattr(
            "news.config.loader.DEFAULT_CONFIG_PATH",
            tmp_path / "nonexistent" / "config.yaml",
        )

        # Act
        loader = ConfigLoader()
        config = loader.load_from_default()

        # Assert: デフォルト設定が返される
        assert config.settings.max_articles_per_source == 10  # デフォルト値
