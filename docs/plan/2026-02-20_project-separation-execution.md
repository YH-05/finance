# finance プロジェクト部分分離 実行計画

## Context

finance プロジェクト（Python 16パッケージ, ~124,000行）の規模縮小のため、以下3つの作業を実行する:

1. レガシーパッケージを `trash/` へ移動（finance 本体で実施）
2. NotebookLM を独立パッケージ `notebooklm-mcp` として分離
3. note 金融記事執筆機能群を独立パッケージ `note-finance` として分離

**原則**: 分離作業は finance プロジェクトを別フォルダにコピーし、コピー先で不要部分を削除して実施。元の finance プロジェクトは変更しない（作業1を除く）。

---

## 作業1: レガシーパッケージを trash/ へ移動

**対象**: finance 本体（`/Users/yukihata/Desktop/finance/`）で直接実施

### Step 1.1: ディレクトリ移動

```bash
mv src/finance/ trash/legacy-finance-empty/
mv src/market_analysis/ trash/legacy-market-analysis/
mv src/utils/ trash/legacy-utils-alias/
mv src/preprocess/ trash/legacy-preprocess/
```

| パッケージ | 状態 | 行数 |
|-----------|------|------|
| `src/finance/` | 空ディレクトリ（`__init__.py` なし） | 0 |
| `src/market_analysis/` | スケルトンのみ（実装なし） | 0 |
| `src/utils/` | utils_core への互換エイリアス | 30 |
| `src/preprocess/` | レガシー（Ruff 除外、pyproject.toml 非掲載） | 345 |

### Step 1.2: pyproject.toml 修正

**`pyproject.toml`** の以下を変更:

1. **dependencies から `"utils"` を削除** (L8)
2. **packages リストから `"src/utils"` と `"src/quant"` を削除** (L112)
   - `src/quant` はディスク上に存在しないファントムエントリ
3. **`[tool.ruff.lint].exclude` から `"src/preprocess/"` を削除** (L130)
4. **`[tool.pyright].exclude` から `"src/preprocess"` を削除** (L178)
5. **`[tool.uv.sources]` の `utils = { workspace = true }` を削除** (L250)

### Step 1.3: .pre-commit-config.yaml 確認

`src/preprocess` が除外パターンに含まれていれば削除。

### Step 1.4: 検証

```bash
make check-all
```

- 全テスト通過
- `grep -r "from utils\." src/ tests/` で残留参照なしを確認
- `grep -r "from preprocess" src/ tests/` で残留参照なしを確認

---

## 作業2: NotebookLM 独立パッケージ化

**コピー先**: `/Users/yukihata/Desktop/notebooklm-mcp/`

### 概要

| 項目 | 値 |
|------|-----|
| ソース | `src/notebooklm/` (23ファイル, ~10,600行) |
| テスト | `tests/notebooklm/` (16テストモジュール) |
| utils_core 依存 | `get_logger` のみ (14ファイル) |
| 他パッケージからの参照 | なし |
| 関連エージェント/スキル/コマンド | なし |

### Step 2.1: finance プロジェクトをコピー

```bash
rsync -a --progress \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='data/raw/yfinance/' \
  --exclude='data/raw/fred/' \
  --exclude='data/Transcript/' \
  --exclude='research/' \
  --exclude='htmlcov/' \
  --exclude='.ruff_cache/' \
  --exclude='.pytest_cache/' \
  /Users/yukihata/Desktop/finance/ \
  /Users/yukihata/Desktop/notebooklm-mcp/
```

### Step 2.2: 不要ファイルを削除

コピー先で notebooklm に関係ないものを全削除:

```bash
cd /Users/yukihata/Desktop/notebooklm-mcp

# 不要な src/ パッケージを削除
rm -rf src/analyze src/database src/edgar src/market src/rss \
       src/factor src/strategy src/automation src/news src/utils_core \
       src/utils src/preprocess src/finance src/market_analysis \
       src/dev

# 不要な tests/ を削除
rm -rf tests/analyze tests/database tests/edgar tests/market tests/rss \
       tests/factor tests/strategy tests/news tests/skills tests/dev

# 不要な .claude/ を削除（notebooklm にはエージェント/スキル/コマンド不要）
rm -rf .claude/

# 不要なデータ・ドキュメント
rm -rf data/ articles/ research/ template/ snippets/ trash/ \
       docs/ notebook/ notebook_sample/ src_sample/ analyst/

# 不要な設定ファイル
rm -f CLAUDE.md .mcp.json
```

### Step 2.3: utils_core.logging を structlog 直接利用に置換

**新規ファイル作成**: `src/notebooklm/_logging.py`

```python
"""Logging configuration for notebooklm package."""

import logging
import os
import sys

import structlog
from structlog import BoundLogger


_initialized = False


def _ensure_basic_config() -> None:
    """get_logger 呼び出し前に最小限のロギング設定を確保する."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    level_value = getattr(logging, level_str, logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level_value)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )


def get_logger(name: str, **context) -> BoundLogger:
    """構造化ロガーインスタンスを取得する."""
    _ensure_basic_config()
    logger: BoundLogger = structlog.get_logger(name)
    if context:
        logger = logger.bind(**context)
    return logger
```

**14ファイルの import 置換**:

```python
# 変更前
from utils_core.logging import get_logger

# 変更後
from notebooklm._logging import get_logger
```

対象ファイル:
- `errors.py`, `decorators.py`, `validation.py`, `selectors.py`
- `browser/manager.py`, `browser/helpers.py`
- `mcp/server.py`
- `services/notebook.py`, `services/source.py`, `services/chat.py`
- `services/audio.py`, `services/studio.py`, `services/note.py`, `services/batch.py`

### Step 2.4: pyproject.toml を新規作成

```toml
[project]
name = "notebooklm-mcp"
version = "0.1.0"
description = "MCP server for Google NotebookLM browser automation"
requires-python = ">=3.12"
dependencies = [
    "playwright>=1.49.0,<2.0.0",
    "fastmcp>=2.14.3",
    "pydantic>=2.0.0",
    "structlog>=25.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=7.0.0",
    "pytest-asyncio>=1.3.0",
    "hypothesis>=6.150.2",
    "pyright>=1.1.403",
    "ruff>=0.14.11",
]

[project.scripts]
notebooklm-mcp = "notebooklm.mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/notebooklm"]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "SIM", "RUF", "TCH", "PTH", "PL"]
ignore = ["E501", "F401", "PLR0913", "PLR2004", "PLC0415"]

[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.12"
typeCheckingMode = "basic"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = ["-ra", "--strict-markers", "--strict-config"]
```

### Step 2.5: Makefile を簡易版で作成

finance の Makefile から基本ターゲット（format, lint, typecheck, test, check-all, clean）のみ抜粋。

### Step 2.6: テストフィクスチャ確認・修正

`tests/notebooklm/conftest.py` で `utils_core` や他パッケージへの参照があれば修正。

### Step 2.7: git init & 検証

```bash
cd /Users/yukihata/Desktop/notebooklm-mcp
git init
uv sync --all-extras
uv run ruff check src/ tests/
uv run pyright src/ tests/
uv run pytest tests/
# 残留参照チェック
grep -r "utils_core\|from finance\|from database\|from market" src/ tests/
```

---

## 作業3: note 金融記事パッケージ分離

**コピー先**: `/Users/yukihata/Desktop/note-finance/`

### 概要

| 項目 | 値 |
|------|-----|
| Python パッケージ | `rss` (12,262行), `news` (18,687行), `automation` (401行) |
| エージェント | 24個（記事作成9, ニュース2, 週次レポート10+, 旧3） |
| スキル | 8個 |
| コマンド | 6個 |
| utils_core 依存 | `get_logger` のみ（rss: 2箇所, news: ~34箇所, automation: 1箇所） |
| deep-research | **含めない**（finance 本体に残す） |

### Step 3.1: finance プロジェクトをコピー

```bash
rsync -a --progress \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='data/raw/yfinance/' \
  --exclude='data/raw/fred/' \
  --exclude='data/Transcript/' \
  --exclude='research/' \
  --exclude='htmlcov/' \
  --exclude='.ruff_cache/' \
  --exclude='.pytest_cache/' \
  /Users/yukihata/Desktop/finance/ \
  /Users/yukihata/Desktop/note-finance/
```

### Step 3.2: 不要ファイルを削除

```bash
cd /Users/yukihata/Desktop/note-finance

# 不要な src/ パッケージを削除
rm -rf src/analyze src/database src/edgar src/market \
       src/factor src/strategy src/utils_core src/utils \
       src/preprocess src/finance src/market_analysis \
       src/notebooklm src/dev

# 不要な tests/ を削除
rm -rf tests/analyze tests/database tests/edgar tests/market \
       tests/factor tests/strategy tests/notebooklm tests/skills tests/dev

# 不要なデータ
rm -rf data/raw/yfinance data/raw/fred data/duckdb data/sqlite \
       data/processed data/exports data/schemas
rm -rf research/ analyst/ notebook/ notebook_sample/ src_sample/
rm -rf trash/
```

### Step 3.3: .claude/ の整理

**残すエージェント** (`.claude/agents/`):

記事作成 (9):
- `finance-topic-suggester.md`
- `finance-article-writer.md`
- `finance-critic-fact.md`, `finance-critic-data.md`, `finance-critic-structure.md`
- `finance-critic-readability.md`, `finance-critic-compliance.md`
- `finance-reviser.md`
- `research-image-collector.md`

ニュース収集 (2):
- `news-article-fetcher.md`
- `ai-research-article-fetcher.md`

週次レポート (10):
- `weekly-report-lead.md`
- `wr-news-aggregator.md`, `wr-data-aggregator.md`, `wr-comment-generator.md`
- `wr-template-renderer.md`, `wr-report-validator.md`, `wr-report-publisher.md`
- `weekly-comment-indices-fetcher.md`, `weekly-comment-mag7-fetcher.md`, `weekly-comment-sectors-fetcher.md`

仮説生成 (1):
- `market-hypothesis-generator.md`

**残すスキル** (`.claude/skills/`):
- `finance-news-workflow/`
- `ai-research-workflow/`
- `generate-market-report/`
- `weekly-comment-generation/`
- `weekly-data-aggregation/`
- `weekly-template-rendering/`
- `weekly-report-validation/`

**残すコマンド** (`.claude/commands/`):
- `finance-suggest-topics.md`
- `new-finance-article.md`
- `finance-edit.md`
- `finance-full.md`
- `generate-market-report.md`
- `ai-research-collect.md`

**残すルール** (`.claude/rules/`):
- `coding-standards.md`, `common-instructions.md`, `git-rules.md`
- `testing-strategy.md`, `subagent-data-passing.md`

**それ以外の .claude/ 内ファイルを全削除**:
- deep-research エージェント群 (15個)
- ca-strategy エージェント群 (8個)
- ca-eval エージェント群 (6個)
- 汎用開発エージェント群 (テスト、品質、PR レビュー等 ~70個)
- 対応する不要スキル・コマンド

### Step 3.4: utils_core.logging を置換

**rss パッケージ**: `src/rss/_logging.py` を新規作成（Step 2.3 と同じ実装）

置換対象:
```python
# 変更前
from utils_core.logging import get_logger
# 変更後
from rss._logging import get_logger
```

**追加**: `rss/storage/json_storage.py` が使用する `utils_core.errors.log_and_reraise` を `rss/_errors.py` にコピー。

**news パッケージ**: `src/news/_logging.py` を新規作成

置換対象（~34箇所）:
```python
# 変更前
from utils_core.logging import get_logger
# 変更後
from news._logging import get_logger
```

`news/scripts/finance_news_workflow.py` の `setup_logging` も `news/_logging.py` に簡易版を実装。

**automation パッケージ**: `automation/news_collector.py` の `from database import get_logger` を標準 logging に置換。

### Step 3.5: common-instructions.md の修正

```python
# 変更前
from finance.utils.logging_config import get_logger

# 変更後（パッケージに応じて）
from rss._logging import get_logger  # rss パッケージ内
from news._logging import get_logger  # news パッケージ内
```

### Step 3.6: pyproject.toml を新規作成

```toml
[project]
name = "note-finance"
version = "0.1.0"
description = "note.com 金融記事作成・ニュース収集パイプライン"
requires-python = ">=3.12"
dependencies = [
    "structlog>=25.4.0",
    "rich>=13.7.0",
    "filelock>=3.20.3",
    "httpx>=0.28.1",
    "feedparser>=6.0.12",
    "lxml>=6.0.2",
    "trafilatura>=2.0.0",
    "anthropic>=0.76.0",
    "pydantic>=2.0.0",
    "jinja2>=3.1.0",
    "tenacity>=9.1.2",
    "tqdm>=4.67.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=7.0.0",
    "pytest-asyncio>=1.3.0",
    "pytest-httpserver>=1.1.3",
    "hypothesis>=6.150.2",
    "pyright>=1.1.403",
    "ruff>=0.14.11",
]
mcp = ["fastmcp>=2.14.3", "mcp>=1.0.0"]
cli = ["click>=8.1.0"]
playwright = ["playwright>=1.49.0,<2.0.0"]
automation = ["claude-agent-sdk>=0.1.22", "anyio>=4.0.0"]
scheduler = ["apscheduler>=3.10.0"]

[project.scripts]
rss-mcp = "rss.mcp.server:main"
rss-cli = "rss.cli.main:cli"
collect-finance-news = "automation.news_collector:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/rss", "src/news", "src/automation"]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "SIM", "RUF", "TCH", "PTH", "PL"]
ignore = ["E501", "F401", "PLR0913", "PLR2004", "PLC0415"]

[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.12"
typeCheckingMode = "basic"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = ["-ra", "--strict-markers", "--strict-config"]
```

### Step 3.7: CLAUDE.md を note-finance 用に新規作成

金融記事関連のコマンド・スキル・エージェントのみ記載した縮小版 CLAUDE.md を作成。

### Step 3.8: Makefile を簡易版で作成

### Step 3.9: git init & 検証

```bash
cd /Users/yukihata/Desktop/note-finance
git init
uv sync --all-extras
uv run ruff check src/ tests/
uv run pyright src/ tests/
uv run pytest tests/
# 残留参照チェック
grep -r "utils_core\|from database\|from market\|from analyze\|from factor\|from strategy\|from edgar" src/ tests/
```

---

## 実行順序

```
1. 作業1: レガシー削除（finance 本体、10分）
   ↓
2. 作業2: notebooklm-mcp 分離（コピー→削除→置換→検証、1-2時間）
   ↓
3. 作業3: note-finance 分離（コピー→削除→置換→検証、2-3時間）
```

作業2と3は独立しているため並行実行も可能だが、作業2で分離パターン（コピー→削除→utils_core置換）を確立してから作業3に進むのが安全。

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| news テストが rss テストのフィクスチャに依存 | テスト失敗 | 両方のテストを同一プロジェクトに含めるため問題なし |
| エージェント内で他グループのエージェントを参照 | エージェント実行失敗 | 24エージェント全てを監査し、cross-reference があればスタブ化 |
| `automation/news_collector.py` が `database` パッケージを import | import エラー | structlog 直接利用に置換（既にフォールバックパターンあり） |
| `rss/storage/json_storage.py` が `utils_core.errors.log_and_reraise` を使用 | import エラー | 関数を `rss/_errors.py` にコピー（自己完結型、20行） |
| 週次レポートエージェントが GitHub Project #15 をハードコード | 同一ユーザーなら問題なし | 同一 GitHub アカウントで使用するため変更不要 |
| rsync コピーが大容量 | 時間がかかる | `.git/`, `.venv/`, 大容量データを除外（推定コピーサイズ: 200-300MB） |

---

## 重要ファイル

| ファイル | 作業 | 変更内容 |
|---------|------|---------|
| `pyproject.toml` | 1,2,3 | 作業1: エントリ削除。作業2,3: 新規作成 |
| `src/utils_core/logging/config.py` | 2,3 | 参考元（`get_logger` の実装をコピー・簡略化） |
| `src/utils_core/errors.py` | 3 | `log_and_reraise` をコピー |
| `src/notebooklm/_logging.py` | 2 | 新規作成（structlog 直接利用） |
| `src/rss/_logging.py` | 3 | 新規作成 |
| `src/news/_logging.py` | 3 | 新規作成 |
| `src/news/collectors/rss.py` | - | news→rss 依存の中核（変更不要、同一プロジェクト内） |
| `.claude/rules/common-instructions.md` | 3 | import 例の書き換え |
