# news.config

ニュースパッケージの設定管理モジュール。

## 概要

YAML 設定ファイルの読み込みとバリデーションを行う設定管理モジュール。ワークフロー全体の設定（収集、抽出、要約、公開）を一元管理します。28 の設定クラスを Pydantic モデルで定義。

**設定階層:**

```
NewsWorkflowConfig（ワークフロー全体）
├── rss: RssConfig（RSS フィード設定）
├── extraction: ExtractionConfig（本文抽出設定）
│   ├── user_agent_rotation: UserAgentRotationConfig
│   └── playwright_fallback: PlaywrightFallbackConfig
├── summarization: SummarizationConfig（AI 要約設定）
├── github: GitHubConfig（GitHub 連携設定）
├── filtering: FilteringConfig（フィルタリング設定）
├── domain_filtering: DomainFilteringConfig（ドメインフィルタ）
├── output: OutputConfig（出力設定）
├── status_mapping: dict（カテゴリ → Status マッピング）
└── github_status_ids: dict（Status → Option ID マッピング）
```

## クイックスタート

### ワークフロー設定の読み込み

```python
from news.config import load_config

config = load_config("data/config/news-collection-config.yaml")

print(f"バージョン: {config.version}")
print(f"リポジトリ: {config.github.repository}")
print(f"抽出並列数: {config.extraction.concurrency}")
print(f"要約タイムアウト: {config.summarization.timeout_seconds}秒")
```

### 基本設定の読み込み

```python
from news.config import ConfigLoader, NewsConfig

loader = ConfigLoader()
config = loader.load("config.yaml")

print(f"最大記事数/ソース: {config.settings.max_articles_per_source}")
```

### デフォルト設定パス

```python
from news.config import DEFAULT_CONFIG_PATH

print(DEFAULT_CONFIG_PATH)
# → "data/config/news_sources.yaml"
```

## API リファレンス

### 設定読み込み

| 関数/クラス | 説明 |
|------------|------|
| `load_config(path)` | YAML からワークフロー設定を読み込み |
| `ConfigLoader` | 基本設定のローダー |
| `DEFAULT_CONFIG_PATH` | デフォルト設定ファイルパス |

### ワークフロー設定クラス

| クラス | 説明 |
|--------|------|
| `NewsWorkflowConfig` | ワークフロー全体の設定 |
| `RssConfig` | RSS フィード設定（presets_file, user_agent_rotation） |
| `ExtractionConfig` | 本文抽出設定（concurrency, min_body_length, timeout_seconds） |
| `SummarizationConfig` | AI 要約設定（concurrency, prompt_template, timeout_seconds） |
| `GitHubConfig` | GitHub 連携設定（repository, project_id, status_field_id） |
| `FilteringConfig` | フィルタリング設定（max_age_hours） |
| `DomainFilteringConfig` | ドメインフィルタ設定（blocked_domains, enabled） |
| `OutputConfig` | 出力設定（result_dir） |
| `UserAgentRotationConfig` | User-Agent ローテーション設定 |
| `PlaywrightFallbackConfig` | Playwright フォールバック設定 |
| `RetryConfig` | リトライ設定 |

### 基本設定クラス

| クラス | 説明 |
|--------|------|
| `NewsConfig` | 基本ニュース設定 |
| `SettingsConfig` | アプリケーション設定 |
| `SourcesConfig` | ソース設定 |
| `YFinanceTickerSourceConfig` | yfinance Ticker ソース設定 |
| `YFinanceSearchSourceConfig` | yfinance Search ソース設定 |
| `FileSinkConfig` | ファイル出力設定 |
| `GitHubSinkConfig` | GitHub 出力設定 |
| `SinksConfig` | 出力先設定 |

### 例外クラス

| 例外 | 説明 |
|------|------|
| `ConfigError` | 設定エラーの基底例外 |
| `ConfigParseError` | YAML パースエラー |
| `ConfigValidationError` | 設定値バリデーションエラー |

## モジュール構成

```
news/config/
├── __init__.py   # パッケージエクスポート（28クラス + load_config関数）
├── models.py     # 全設定クラスの定義
└── README.md     # このファイル
```

## 関連モジュール

- [news.collectors](../collectors/README.md) - RssConfig 使用
- [news.extractors](../extractors/README.md) - ExtractionConfig 使用
- [news.sinks](../sinks/README.md) - FileSinkConfig, GitHubSinkConfig 使用
