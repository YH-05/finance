# P1-007: config.py 設定ファイル読み込み機能実装

## 概要

YAML 設定ファイルを読み込み、Pydantic モデルにマッピングする機能を実装する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

なし（開始可能）

## 成果物

- `src/news/config.py`（新規作成）

## 実装内容

```python
from pathlib import Path
from pydantic import BaseModel
import yaml

class RssConfig(BaseModel):
    """RSS設定"""
    presets_file: str

class ExtractionConfig(BaseModel):
    """本文抽出設定"""
    concurrency: int = 5
    timeout_seconds: int = 30
    min_body_length: int = 200
    max_retries: int = 3

class SummarizationConfig(BaseModel):
    """要約設定"""
    concurrency: int = 3
    timeout_seconds: int = 60
    max_retries: int = 3
    prompt_template: str

class GitHubConfig(BaseModel):
    """GitHub設定"""
    project_number: int
    project_id: str
    status_field_id: str
    published_date_field_id: str
    repository: str
    duplicate_check_days: int = 7
    dry_run: bool = False

class FilteringConfig(BaseModel):
    """フィルタリング設定"""
    max_age_hours: int = 168  # 7日

class OutputConfig(BaseModel):
    """出力設定"""
    result_dir: str

class NewsWorkflowConfig(BaseModel):
    """ワークフロー全体設定"""
    version: str
    status_mapping: dict[str, str]
    github_status_ids: dict[str, str]
    rss: RssConfig
    extraction: ExtractionConfig
    summarization: SummarizationConfig
    github: GitHubConfig
    filtering: FilteringConfig
    output: OutputConfig

def load_config(path: Path) -> NewsWorkflowConfig:
    """設定ファイルを読み込む"""
    with open(path) as f:
        data = yaml.safe_load(f)
    return NewsWorkflowConfig.model_validate(data)
```

## 受け入れ条件

- [ ] `NewsWorkflowConfig` Pydantic モデルが定義されている
- [ ] 各サブ設定（RssConfig, ExtractionConfig, SummarizationConfig, GitHubConfig, FilteringConfig, OutputConfig）が定義されている
- [ ] `load_config(path: Path) -> NewsWorkflowConfig` 関数が実装されている
- [ ] `status_mapping` でカテゴリ → GitHub Status の解決が可能
- [ ] `github_status_ids` で Status 名 → ID の解決が可能
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: 設定ファイルセクション
