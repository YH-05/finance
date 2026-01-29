"""Unit tests for NewsWorkflowConfig and load_config function.

Tests for Issue #2370: config.py 設定ファイル読み込み機能

This module tests the workflow configuration models and loading function
for the news collection workflow.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError


class TestRssConfig:
    """Test RssConfig Pydantic model."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """RssConfigを必須パラメータで作成できることを確認。"""
        from news.config.workflow import RssConfig

        config = RssConfig(presets_file="data/config/rss-presets.json")

        assert config.presets_file == "data/config/rss-presets.json"

    def test_異常系_presets_file未指定でValidationError(self) -> None:
        """presets_fileが未指定の場合、ValidationErrorが発生することを確認。"""
        from news.config.workflow import RssConfig

        with pytest.raises(ValidationError):
            RssConfig()


class TestExtractionConfig:
    """Test ExtractionConfig Pydantic model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """ExtractionConfigをデフォルト値で作成できることを確認。"""
        from news.config.workflow import ExtractionConfig

        config = ExtractionConfig()

        assert config.concurrency == 5
        assert config.timeout_seconds == 30
        assert config.min_body_length == 200
        assert config.max_retries == 3

    def test_正常系_カスタム値で作成できる(self) -> None:
        """ExtractionConfigをカスタム値で作成できることを確認。"""
        from news.config.workflow import ExtractionConfig

        config = ExtractionConfig(
            concurrency=10,
            timeout_seconds=60,
            min_body_length=100,
            max_retries=5,
        )

        assert config.concurrency == 10
        assert config.timeout_seconds == 60
        assert config.min_body_length == 100
        assert config.max_retries == 5

    def test_異常系_負のconcurrencyでValidationError(self) -> None:
        """concurrencyが負の値の場合、ValidationErrorが発生することを確認。"""
        from news.config.workflow import ExtractionConfig

        with pytest.raises(ValidationError):
            ExtractionConfig(concurrency=-1)


class TestSummarizationConfig:
    """Test SummarizationConfig Pydantic model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """SummarizationConfigをデフォルト値で作成できることを確認。"""
        from news.config.workflow import SummarizationConfig

        config = SummarizationConfig(prompt_template="test template")

        assert config.concurrency == 3
        assert config.timeout_seconds == 60
        assert config.max_retries == 3
        assert config.prompt_template == "test template"

    def test_異常系_prompt_template未指定でValidationError(self) -> None:
        """prompt_templateが未指定の場合、ValidationErrorが発生することを確認。"""
        from news.config.workflow import SummarizationConfig

        with pytest.raises(ValidationError):
            SummarizationConfig()


class TestGitHubConfig:
    """Test GitHubConfig Pydantic model for workflow."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """GitHubConfigを必須パラメータで作成できることを確認。"""
        from news.config.workflow import GitHubConfig

        config = GitHubConfig(
            project_number=15,
            project_id="PVT_kwHOBoK6AM4BMpw_",
            status_field_id="PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
            published_date_field_id="PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
            repository="YH-05/finance",
        )

        assert config.project_number == 15
        assert config.project_id == "PVT_kwHOBoK6AM4BMpw_"
        assert config.status_field_id == "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE"
        assert config.published_date_field_id == "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
        assert config.repository == "YH-05/finance"
        assert config.duplicate_check_days == 7  # デフォルト値
        assert config.dry_run is False  # デフォルト値

    def test_正常系_全パラメータで作成できる(self) -> None:
        """GitHubConfigを全パラメータで作成できることを確認。"""
        from news.config.workflow import GitHubConfig

        config = GitHubConfig(
            project_number=15,
            project_id="PVT_kwHOBoK6AM4BMpw_",
            status_field_id="PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
            published_date_field_id="PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
            repository="YH-05/finance",
            duplicate_check_days=14,
            dry_run=True,
        )

        assert config.duplicate_check_days == 14
        assert config.dry_run is True

    def test_異常系_project_number未指定でValidationError(self) -> None:
        """project_numberが未指定の場合、ValidationErrorが発生することを確認。"""
        from news.config.workflow import GitHubConfig

        with pytest.raises(ValidationError):
            GitHubConfig(
                project_id="PVT_kwHOBoK6AM4BMpw_",
                status_field_id="PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
                published_date_field_id="PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
                repository="YH-05/finance",
            )


class TestFilteringConfig:
    """Test FilteringConfig Pydantic model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """FilteringConfigをデフォルト値で作成できることを確認。"""
        from news.config.workflow import FilteringConfig

        config = FilteringConfig()

        assert config.max_age_hours == 168  # 7日

    def test_正常系_カスタム値で作成できる(self) -> None:
        """FilteringConfigをカスタム値で作成できることを確認。"""
        from news.config.workflow import FilteringConfig

        config = FilteringConfig(max_age_hours=24)

        assert config.max_age_hours == 24


class TestOutputConfig:
    """Test OutputConfig Pydantic model."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """OutputConfigを必須パラメータで作成できることを確認。"""
        from news.config.workflow import OutputConfig

        config = OutputConfig(result_dir="data/exports/news-workflow")

        assert config.result_dir == "data/exports/news-workflow"

    def test_異常系_result_dir未指定でValidationError(self) -> None:
        """result_dirが未指定の場合、ValidationErrorが発生することを確認。"""
        from news.config.workflow import OutputConfig

        with pytest.raises(ValidationError):
            OutputConfig()


class TestNewsWorkflowConfig:
    """Test NewsWorkflowConfig root Pydantic model."""

    def test_正常系_必須パラメータで作成できる(self) -> None:
        """NewsWorkflowConfigを必須パラメータで作成できることを確認。"""
        from news.config.workflow import (
            ExtractionConfig,
            FilteringConfig,
            GitHubConfig,
            NewsWorkflowConfig,
            OutputConfig,
            RssConfig,
            SummarizationConfig,
        )

        config = NewsWorkflowConfig(
            version="1.0",
            status_mapping={"tech": "ai", "market": "index"},
            github_status_ids={"ai": "6fbb43d0", "index": "3925acc3"},
            rss=RssConfig(presets_file="data/config/rss-presets.json"),
            extraction=ExtractionConfig(),
            summarization=SummarizationConfig(prompt_template="test template"),
            github=GitHubConfig(
                project_number=15,
                project_id="PVT_kwHOBoK6AM4BMpw_",
                status_field_id="PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
                published_date_field_id="PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
                repository="YH-05/finance",
            ),
            filtering=FilteringConfig(),
            output=OutputConfig(result_dir="data/exports/news-workflow"),
        )

        assert config.version == "1.0"
        assert config.status_mapping == {"tech": "ai", "market": "index"}
        assert config.github_status_ids == {"ai": "6fbb43d0", "index": "3925acc3"}
        assert config.rss.presets_file == "data/config/rss-presets.json"
        assert config.extraction.concurrency == 5
        assert config.summarization.prompt_template == "test template"
        assert config.github.project_number == 15
        assert config.filtering.max_age_hours == 168
        assert config.output.result_dir == "data/exports/news-workflow"

    def test_正常系_status_mappingでカテゴリからStatusを解決できる(self) -> None:
        """status_mappingでカテゴリからGitHub Statusを解決できることを確認。"""
        from news.config.workflow import (
            ExtractionConfig,
            FilteringConfig,
            GitHubConfig,
            NewsWorkflowConfig,
            OutputConfig,
            RssConfig,
            SummarizationConfig,
        )

        config = NewsWorkflowConfig(
            version="1.0",
            status_mapping={
                "tech": "ai",
                "market": "index",
                "finance": "finance",
                "yf_index": "index",
                "yf_stock": "stock",
            },
            github_status_ids={
                "ai": "6fbb43d0",
                "index": "3925acc3",
                "finance": "ac4a91b1",
                "stock": "f762022e",
            },
            rss=RssConfig(presets_file="data/config/rss-presets.json"),
            extraction=ExtractionConfig(),
            summarization=SummarizationConfig(prompt_template="test"),
            github=GitHubConfig(
                project_number=15,
                project_id="PVT_kwHOBoK6AM4BMpw_",
                status_field_id="PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
                published_date_field_id="PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
                repository="YH-05/finance",
            ),
            filtering=FilteringConfig(),
            output=OutputConfig(result_dir="data/exports"),
        )

        # カテゴリからStatusを解決
        assert config.status_mapping["tech"] == "ai"
        assert config.status_mapping["yf_index"] == "index"

        # Status名からIDを解決
        assert config.github_status_ids["ai"] == "6fbb43d0"
        assert config.github_status_ids["index"] == "3925acc3"

    def test_正常系_dictから作成できる(self) -> None:
        """NewsWorkflowConfigを辞書から作成できることを確認。"""
        from news.config.workflow import NewsWorkflowConfig

        data = {
            "version": "1.0",
            "status_mapping": {"tech": "ai", "market": "index"},
            "github_status_ids": {"ai": "6fbb43d0", "index": "3925acc3"},
            "rss": {"presets_file": "data/config/rss-presets.json"},
            "extraction": {"concurrency": 10},
            "summarization": {"prompt_template": "test template"},
            "github": {
                "project_number": 15,
                "project_id": "PVT_kwHOBoK6AM4BMpw_",
                "status_field_id": "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
                "published_date_field_id": "PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
                "repository": "YH-05/finance",
            },
            "filtering": {"max_age_hours": 24},
            "output": {"result_dir": "data/exports"},
        }

        config = NewsWorkflowConfig.model_validate(data)

        assert config.version == "1.0"
        assert config.extraction.concurrency == 10
        assert config.filtering.max_age_hours == 24


class TestLoadConfig:
    """Test load_config function."""

    def test_正常系_YAML設定ファイルを読み込める(self, tmp_path: Path) -> None:
        """load_configがYAML設定ファイルを読み込めることを確認。"""
        from news.config.workflow import load_config

        # Arrange: YAML設定ファイルを作成
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
version: "1.0"

status_mapping:
  tech: "ai"
  market: "index"

github_status_ids:
  ai: "6fbb43d0"
  index: "3925acc3"

rss:
  presets_file: "data/config/rss-presets.json"

extraction:
  concurrency: 10
  timeout_seconds: 60
  min_body_length: 100
  max_retries: 5

summarization:
  concurrency: 5
  timeout_seconds: 120
  max_retries: 3
  prompt_template: |
    Test prompt template.

github:
  project_number: 15
  project_id: "PVT_kwHOBoK6AM4BMpw_"
  status_field_id: "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE"
  published_date_field_id: "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
  repository: "YH-05/finance"
  duplicate_check_days: 14
  dry_run: true

filtering:
  max_age_hours: 48

output:
  result_dir: "data/exports/news-workflow"
"""
        )

        # Act
        config = load_config(config_file)

        # Assert
        assert config.version == "1.0"
        assert config.status_mapping == {"tech": "ai", "market": "index"}
        assert config.github_status_ids == {"ai": "6fbb43d0", "index": "3925acc3"}
        assert config.rss.presets_file == "data/config/rss-presets.json"
        assert config.extraction.concurrency == 10
        assert config.summarization.concurrency == 5
        assert config.github.project_number == 15
        assert config.github.dry_run is True
        assert config.filtering.max_age_hours == 48
        assert config.output.result_dir == "data/exports/news-workflow"

    def test_正常系_文字列パスで読み込める(self, tmp_path: Path) -> None:
        """load_configが文字列パスでも読み込めることを確認。"""
        from news.config.workflow import load_config

        # Arrange
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
version: "1.0"
status_mapping:
  tech: "ai"
github_status_ids:
  ai: "6fbb43d0"
rss:
  presets_file: "data/config/rss-presets.json"
extraction: {}
summarization:
  prompt_template: "test"
github:
  project_number: 15
  project_id: "PVT_kwHOBoK6AM4BMpw_"
  status_field_id: "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE"
  published_date_field_id: "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
  repository: "YH-05/finance"
filtering: {}
output:
  result_dir: "data/exports"
"""
        )

        # Act - 文字列パスで呼び出し
        config = load_config(str(config_file))

        # Assert
        assert config.version == "1.0"

    def test_異常系_存在しないファイルでFileNotFoundError(self) -> None:
        """存在しないファイルを読み込むとFileNotFoundErrorが発生することを確認。"""
        from news.config.workflow import load_config

        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_異常系_不正なYAMLでエラー(self, tmp_path: Path) -> None:
        """不正なYAMLファイルを読み込むとエラーが発生することを確認。"""
        from yaml import YAMLError

        from news.config.workflow import load_config

        # Arrange: 不正なYAMLファイルを作成
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text(
            """
version: "1.0"
  - this is invalid yaml structure
"""
        )

        # Act & Assert
        with pytest.raises(YAMLError):
            load_config(config_file)

    def test_異常系_バリデーションエラー(self, tmp_path: Path) -> None:
        """必須フィールドがない場合、ValidationErrorが発生することを確認。"""
        from news.config.workflow import load_config

        # Arrange: 必須フィールドがないYAMLファイルを作成
        config_file = tmp_path / "incomplete.yaml"
        config_file.write_text(
            """
version: "1.0"
# rss, github など必須フィールドが欠けている
"""
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            load_config(config_file)
