---
name: finance-news-workflow
description: 金融ニュース収集の3フェーズワークフロー。Python CLI前処理→テーマ別エージェント直接呼び出し→結果報告。
allowed-tools: Read, Bash, Task, MCPSearch
---

# 金融ニュース収集ワークフロー

RSSフィードから金融ニュースを自動収集し、GitHub Project #15に投稿するワークフロースキル。

## 新アーキテクチャ（2026-01-29〜）

```
prepare_news_session.py (Python CLI) ← 決定論的前処理
  ├── 既存Issue取得・URL抽出
  ├── RSS取得（全テーマ一括）
  ├── 公開日時フィルタリング
  ├── 重複チェック
  ├── ペイウォール事前チェック（Playwright使用）
  └── セッションファイル出力（.tmp/news-{timestamp}.json）

/finance-news-workflow (このスキル)
  ├── Python CLI前処理実行
  └── テーマエージェント × 11（並列呼び出し）
        ├── テーマ設定を保持（ラベル、Status Option ID等）
        ├── セッションファイルから自テーマの記事読み込み
        ├── news-article-fetcher に委譲（バッチ）
        │     ├── Tier 1: ArticleExtractor（trafilatura）
        │     ├── Tier 2: MCP Playwright（動的サイト用）
        │     └── Tier 3: RSS Summary フォールバック
        ├── 結果を受け取り
        └── 取得成功/失敗の件数をログ出力（モニタリング）
```

## 使用方法

```bash
# 標準実行（デフォルト: 過去7日間）
/finance-news-workflow

# オプション付き
/finance-news-workflow --days 3 --themes "index,macro_cnbc" --dry-run
```

## 3フェーズワークフロー

```
Phase 1: 初期化・前処理
├── テーマ設定ファイル確認（data/config/finance-news-themes.json）
├── GitHub CLI 確認
└── Python CLI 実行（prepare_news_session.py）
    ├── 既存Issue取得・URL抽出
    ├── RSS取得（全テーマ一括）
    ├── 公開日時フィルタリング
    ├── 重複チェック
    ├── ペイウォール事前チェック
    └── セッションファイル出力

Phase 2: テーマ別収集（並列）
├── セッションファイルパスを各エージェントに渡す
├── finance-news-index      [Status=Index]
├── finance-news-stock      [Status=Stock]
├── finance-news-sector     [Status=Sector]
├── finance-news-macro-cnbc [Status=Macro]
├── finance-news-macro-other [Status=Macro]
├── finance-news-ai-cnbc    [Status=AI]
├── finance-news-ai-nasdaq  [Status=AI]
├── finance-news-ai-tech    [Status=AI]
├── finance-news-finance-cnbc    [Status=Finance]
├── finance-news-finance-nasdaq  [Status=Finance]
└── finance-news-finance-other   [Status=Finance]

Phase 3: 結果報告
└── テーマ別投稿数・スキップ数サマリー表示
```

## Phase 1: 初期化・前処理

### ステップ1.1: 環境確認

```bash
# テーマ設定ファイル確認
if [ ! -f "data/config/finance-news-themes.json" ]; then
    echo "エラー: テーマ設定ファイルが見つかりません"
    exit 1
fi

# GitHub CLI 確認
gh auth status
```

### ステップ1.2: Python CLI 前処理実行

```bash
# prepare_news_session.py を実行
uv run python scripts/prepare_news_session.py --days ${days} --output .tmp/news-${timestamp}.json

# 出力: セッションファイルパス
session_file=".tmp/news-${timestamp}.json"
```

**セッションファイル形式**:

```json
{
  "session_id": "news-20260129-143000",
  "timestamp": "2026-01-29T14:30:00+09:00",
  "config": {
    "project_id": "PVT_kwHOBoK6AM4BMpw_",
    "project_number": 15,
    "project_owner": "YH-05",
    "status_field_id": "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
    "published_date_field_id": "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
  },
  "themes": {
    "index": {
      "articles": [...],
      "blocked": [...],
      "theme_config": {
        "name_ja": "株価指数",
        "github_status_id": "3925acc3"
      }
    },
    ...
  },
  "stats": {
    "total": 150,
    "duplicates": 30,
    "paywall_blocked": 10,
    "accessible": 110
  }
}
```

## Phase 2: テーマ別収集（並列）

### ステップ2.1: テーマエージェント直接呼び出し

**オーケストレーターは廃止され、テーマエージェントを直接呼び出します。**

```python
# 11テーマを並列で呼び出し
theme_agents = [
    "finance-news-index",
    "finance-news-stock",
    "finance-news-sector",
    "finance-news-macro-cnbc",
    "finance-news-macro-other",
    "finance-news-ai-cnbc",
    "finance-news-ai-nasdaq",
    "finance-news-ai-tech",
    "finance-news-finance-cnbc",
    "finance-news-finance-nasdaq",
    "finance-news-finance-other",
]

results = []
for agent in theme_agents:
    result = Task(
        subagent_type=agent,
        description=f"{agent}: ニュース収集",
        prompt=f"""
セッションファイル: {session_file}

セッションファイルを読み込み、自テーマの記事を news-article-fetcher に委譲してください。
"""
    )
    results.append(result)
```

### ステップ2.2: 結果集約

各テーマエージェントから返却される結果を集約:

```python
all_stats = {
    "total_articles": 0,
    "total_blocked": 0,
    "total_created": 0,
    "total_failed": 0,
    "by_theme": {}
}

for result in results:
    theme = result["theme"]
    all_stats["total_articles"] += result["stats"]["total_articles"]
    all_stats["total_blocked"] += result["stats"]["blocked"]
    all_stats["total_created"] += result["stats"]["created"]
    all_stats["total_failed"] += result["stats"]["failed"]
    all_stats["by_theme"][theme] = result["stats"]
```

## Phase 3: 結果報告

### サマリー出力形式

```markdown
## 金融ニュース収集完了

### 全体統計

| 項目 | 件数 |
|------|------|
| 前処理：取得記事数 | {stats.total} |
| 前処理：重複スキップ | {stats.duplicates} |
| 前処理：ペイウォールブロック | {stats.paywall_blocked} |
| 投稿対象 | {stats.accessible} |
| Issue作成成功 | {all_stats.total_created} |
| Issue作成失敗 | {all_stats.total_failed} |

### テーマ別統計

| テーマ | 対象 | 作成 | 失敗 | 抽出方法 |
|--------|------|------|------|----------|
| Index（株価指数） | {n} | {created} | {failed} | Tier1: {t1}, Tier2: {t2}, Tier3: {t3} |
| Stock（個別銘柄） | {n} | {created} | {failed} | Tier1: {t1}, Tier2: {t2}, Tier3: {t3} |
| ... | ... | ... | ... | ... |

### セッション情報

- **セッションID**: {session_id}
- **実行時刻**: {timestamp}
- **セッションファイル**: {session_file}
```

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| --days | 7 | 過去何日分のニュースを対象とするか |
| --project | 15 | GitHub Project番号 |
| --themes | all | 対象テーマ（index,stock,sector,macro_cnbc,... / all） |
| --dry-run | false | GitHub投稿せずに結果確認のみ |

## テーマ設定ファイル

**場所**: `data/config/finance-news-themes.json`

```json
{
  "themes": {
    "index": {
      "name": "Index",
      "name_ja": "株価指数",
      "github_status_id": "3925acc3",
      "feeds": [{ "feed_id": "...", "title": "..." }]
    },
    ...
  },
  "project": {
    "project_id": "PVT_kwHOBoK6AM4BMpw_",
    "status_field_id": "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
    "published_date_field_id": "PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
    "owner": "YH-05",
    "number": 15
  }
}
```

## テーマ別エージェント

| エージェント | GitHub Status | 対象 |
|--------------|---------------|------|
| finance-news-index | Index | 株価指数、ETF |
| finance-news-stock | Stock | 個別銘柄、決算 |
| finance-news-sector | Sector | 業界動向 |
| finance-news-macro-cnbc | Macro | マクロ経済（CNBC系） |
| finance-news-macro-other | Macro | マクロ経済（経済指標・中央銀行） |
| finance-news-ai-cnbc | AI | AI（CNBC Technology） |
| finance-news-ai-nasdaq | AI | AI（NASDAQ系） |
| finance-news-ai-tech | AI | AI（テック系メディア） |
| finance-news-finance-cnbc | Finance | 金融（CNBC系） |
| finance-news-finance-nasdaq | Finance | 金融（NASDAQ系） |
| finance-news-finance-other | Finance | 金融（金融メディア） |

## 関連リソース

| リソース | パス |
|---------|------|
| Python CLI前処理 | `scripts/prepare_news_session.py` |
| テーマ設定 | `data/config/finance-news-themes.json` |
| テーマ別エージェント | `.claude/agents/finance-news-{theme}.md` |
| news-article-fetcher | `.claude/agents/news-article-fetcher.md` |
| GitHub Project | https://github.com/users/YH-05/projects/15 |

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| E001: テーマ設定ファイルエラー | ファイル存在・JSON形式を確認 |
| E002: Python CLI エラー | prepare_news_session.py のログを確認 |
| E003: GitHub CLI エラー | `gh auth login` で認証 |
| E004: テーマエージェント失敗 | 失敗テーマのみ --themes で再実行 |
| E005: news-article-fetcher 失敗 | セッションファイルから手動再実行 |

## 変更履歴

### 2026-01-29: 新アーキテクチャ移行

- **オーケストレーター廃止**: `finance-news-orchestrator.md` を `trash/` に移動
- **Python CLI前処理追加**: 決定論的処理をPythonに移行
- **テーマエージェント軽量化**: 設定保持 + 委譲 + モニタリングに特化
- **3段階フォールバック追加**: trafilatura → Playwright → RSS Summary
- **ネスト削減**: 3段（オーケストレーター→テーマ→fetcher）から2段（テーマ→fetcher）へ

## 制約事項

- **GitHub API**: 1時間あたり5000リクエスト
- **RSS取得**: フィードの保持件数に依存（通常10〜50件）
- **重複チェック**: Python CLIで事前実行
- **実行頻度**: 1日1回を推奨
