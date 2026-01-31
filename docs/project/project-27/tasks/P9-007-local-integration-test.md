# P9-007: ローカル統合テスト

## 概要

Claude Pro/Max サブスクリプションで認証済みの環境でローカル統合テストを実行し、実際の記事で要約が正常に動作することを確認する。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P9-006: テストのモック更新

## 成果物

- テスト実行ログ
- 動作確認結果

## 前提条件

### サブスクリプション認証の仕組み

Claude Agent SDK は Claude Code をランタイムとして使用し、以下の認証方式をサポート：

| 認証方式 | 対象 | 課金 |
|---|---|---|
| **サブスクリプション認証** | Claude Pro/Max ユーザー | サブスクリプション料金に含まれる |
| API キー認証 | サードパーティ開発者向け | 従量課金 |

**重要**: `ANTHROPIC_API_KEY` 環境変数が設定されていると、サブスクリプションではなく API キーが優先され、従量課金が発生する。

### Claude Code CLI のインストール確認

```bash
# CLI がインストールされているか確認
claude --version

# 未インストールの場合
curl -fsSL https://claude.ai/install.sh | bash
```

### サブスクリプション認証（APIキー不要）

```bash
# 認証状態を確認
claude auth status

# サブスクリプションでログイン（APIキー不要）
claude auth login

# ブラウザが開き、Claude アカウントでログイン
# Pro/Max サブスクリプションがあれば自動的に認証される
```

### 環境変数の確認（重要）

```bash
# ANTHROPIC_API_KEY が設定されていないことを確認
echo $ANTHROPIC_API_KEY

# 設定されている場合は削除（サブスクリプション優先のため）
unset ANTHROPIC_API_KEY
```

**警告**: `ANTHROPIC_API_KEY` が設定されていると、サブスクリプションではなく API キーが使用され、従量課金が発生します。

## テスト手順

### 1. 環境確認スクリプト

```python
# tests/news/integration/conftest.py

import os
import subprocess
import pytest


def check_claude_auth() -> tuple[bool, str]:
    """Claude CLI の認証状態を確認。"""
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, "Authenticated via subscription"
        return False, result.stderr
    except FileNotFoundError:
        return False, "Claude CLI not installed"
    except Exception as e:
        return False, str(e)


def check_api_key_not_set() -> bool:
    """ANTHROPIC_API_KEY が設定されていないことを確認。"""
    return os.environ.get("ANTHROPIC_API_KEY") is None


@pytest.fixture(scope="session", autouse=True)
def verify_subscription_auth():
    """サブスクリプション認証を検証。

    - ANTHROPIC_API_KEY が設定されていないこと
    - claude auth status で認証済みであること
    """
    # API キーが設定されている場合は警告
    if not check_api_key_not_set():
        pytest.skip(
            "ANTHROPIC_API_KEY is set. "
            "Unset it to use subscription auth: unset ANTHROPIC_API_KEY"
        )

    # 認証状態を確認
    is_auth, message = check_claude_auth()
    if not is_auth:
        pytest.skip(f"Claude subscription auth required: {message}")

    print(f"\n✓ Using Claude subscription auth: {message}")
```

### 2. 単一記事の要約テスト

```python
# tests/news/integration/test_summarizer_integration.py

import asyncio
from datetime import datetime, timezone
import re

import pytest

from news.config.workflow import load_config
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
    SummarizationStatus,
)
from news.summarizer import Summarizer


@pytest.fixture
def config():
    """実際の設定ファイルを読み込む。"""
    return load_config("data/config/news-collection-config.yaml")


@pytest.fixture
def sample_article() -> ExtractedArticle:
    """テスト用の記事データ。"""
    source = ArticleSource(
        source_type=SourceType.RSS,
        source_name="Test Source",
        category="market",
    )
    collected = CollectedArticle(
        url="https://example.com/test",
        title="S&P 500 Hits Record High",
        published=datetime.now(timezone.utc),
        raw_summary="Test summary",
        source=source,
        collected_at=datetime.now(timezone.utc),
    )
    return ExtractedArticle(
        collected=collected,
        body_text="""
        The S&P 500 index reached a new all-time high on Tuesday,
        driven by strong earnings reports from technology companies.
        Apple, Microsoft, and Nvidia all reported better-than-expected
        quarterly results, boosting investor confidence.

        Analysts suggest the rally could continue as the Federal Reserve
        maintains its accommodative monetary policy stance.
        """,
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="test",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_統合_サブスクリプション認証で要約成功(
    config,
    sample_article: ExtractedArticle,
) -> None:
    """Claude Pro/Max サブスクリプションで要約が成功する。

    Note
    ----
    このテストは `claude auth login` で認証済みの環境でのみ実行可能。
    ANTHROPIC_API_KEY は設定しないこと（サブスクリプション優先）。
    """
    summarizer = Summarizer(config=config)
    result = await summarizer.summarize(sample_article)

    # 要約が成功している
    assert result.summarization_status == SummarizationStatus.SUCCESS
    assert result.summary is not None

    # StructuredSummary の各フィールドが存在
    assert result.summary.overview is not None
    assert len(result.summary.overview) > 0

    assert result.summary.key_points is not None
    assert len(result.summary.key_points) > 0

    assert result.summary.market_impact is not None
    assert len(result.summary.market_impact) > 0

    # 日本語で要約されている（ひらがな/カタカナ/漢字が含まれる）
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    assert japanese_pattern.search(result.summary.overview)

    print(f"Overview: {result.summary.overview}")
    print(f"Key Points: {result.summary.key_points}")
    print(f"Market Impact: {result.summary.market_impact}")
```

### 3. テスト実行

```bash
# 環境変数を確認
echo $ANTHROPIC_API_KEY  # 空であることを確認

# 統合テストのみ実行（サブスクリプション認証済み環境で）
uv run pytest tests/news/integration/test_summarizer_integration.py -v -m integration

# 全テスト実行
make test
```

### 4. CLI から直接テスト

```bash
# Orchestrator 経由でテスト（ドライラン）
uv run python -m news.scripts.finance_news_workflow --dry-run --max-articles 1 --verbose
```

## 確認項目

| 項目 | 確認内容 |
|---|---|
| 認証 | `claude auth status` でサブスクリプション認証済み |
| API キー | `ANTHROPIC_API_KEY` が未設定 |
| 要約成功 | `SummarizationStatus.SUCCESS` が返る |
| JSON パース | `StructuredSummary` に正しくパースされる |
| 日本語 | 要約が日本語で生成される |
| タイムアウト | 60秒以内に完了する |
| ログ | 適切なログが出力される |

## 受け入れ条件

- [ ] `claude --version` でCLIバージョンが表示される
- [ ] `claude auth status` でサブスクリプション認証済みが確認できる
- [ ] `ANTHROPIC_API_KEY` が未設定であることを確認
- [ ] 統合テストが成功する
- [ ] 要約が日本語で生成される
- [ ] StructuredSummary の全フィールドが正しく設定される
- [ ] エラーなくログが出力される
- [ ] 処理時間が設定のタイムアウト（60秒）以内

## トラブルシューティング

### CLINotFoundError が発生する場合

```bash
# CLI を再インストール
curl -fsSL https://claude.ai/install.sh | bash
```

### 認証エラーが発生する場合

```bash
# サブスクリプションで再認証
claude auth logout
claude auth login
```

### API キーが使用されてしまう場合

```bash
# 環境変数を削除
unset ANTHROPIC_API_KEY

# シェル設定ファイル (.bashrc, .zshrc) からも削除
# export ANTHROPIC_API_KEY=... の行を削除
```

### タイムアウトが発生する場合

- `data/config/news-collection-config.yaml` の `timeout_seconds` を増やす
- ネットワーク接続を確認

## 参照

- [Using Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)
- [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
