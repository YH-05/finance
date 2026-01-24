---
name: finance-news-workflow
description: 金融ニュース収集の4フェーズワークフロー。RSS取得→フィルタリング→重複チェック→GitHub投稿。
allowed-tools: Read, Bash, Task, MCPSearch
---

# 金融ニュース収集ワークフロー

RSSフィードから金融ニュースを自動収集し、GitHub Project #15に投稿するワークフロースキル。

## 使用方法

```bash
# 標準実行（デフォルト: 過去7日間）
/finance-news-workflow

# オプション付き
/finance-news-workflow --days 3 --themes "index,macro" --dry-run
```

## 4フェーズワークフロー

```
Phase 1: 初期化
├── テーマ設定ファイル確認（data/config/finance-news-themes.json）
├── RSS MCP ツール確認（リトライ付き）
└── GitHub CLI 確認

Phase 2: データ準備（オーケストレーター）
└── finance-news-orchestrator エージェント起動
    ├── RSS記事取得
    ├── 既存Issue取得
    └── 一時ファイル保存（.tmp/news-collection-{timestamp}.json）

Phase 3: テーマ別収集（並列）
├── finance-news-index      [Status=Index]
├── finance-news-stock      [Status=Stock]
├── finance-news-sector     [Status=Sector]
├── finance-news-macro      [Status=Macro Economics]
├── finance-news-ai         [Status=AI]
└── finance-news-finance    [Status=Finance]

Phase 4: 結果報告
└── テーマ別投稿数サマリー表示
```

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| --days | 7 | 過去何日分のニュースを対象とするか（日数指定） |
| --project | 15 | GitHub Project番号 |
| --themes | all | 対象テーマ（index,stock,sector,macro,ai,finance / all） |
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
      "description": "株価指数（日経平均、TOPIX、S&P500等）の動向",
      "feeds": [{ "feed_id": "...", "title": "..." }]
    },
    "stock": { ... },
    "sector": { ... },
    "macro": { ... },
    "ai": { ... },
    "finance": { ... }
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

## RSS MCP ツール

| ツール | 用途 |
|--------|------|
| `mcp__rss__rss_list_feeds` | 登録済みフィード一覧取得 |
| `mcp__rss__rss_get_items` | フィードから記事取得 |
| `mcp__rss__rss_search_items` | キーワード検索 |
| `mcp__rss__rss_fetch_feed` | フィード即時取得 |
| `mcp__rss__rss_add_feed` | フィード追加 |
| `mcp__rss__rss_update_feed` | フィード更新 |
| `mcp__rss__rss_remove_feed` | フィード削除 |

## テーマ別エージェント

| エージェント | GitHub Status | 対象 |
|--------------|---------------|------|
| finance-news-index | Index | 株価指数、ETF |
| finance-news-stock | Stock | 個別銘柄、決算 |
| finance-news-sector | Sector | 業界動向 |
| finance-news-macro | Macro Economics | 金融政策、経済指標 |
| finance-news-ai | AI | AI技術、AI企業 |
| finance-news-finance | Finance | 企業財務、金融商品 |

## 関連リソース

| リソース | パス |
|---------|------|
| オーケストレーター | `.claude/agents/finance-news-orchestrator.md` |
| テーマ設定 | `data/config/finance-news-themes.json` |
| GitHub Project | https://github.com/users/YH-05/projects/15 |
| RSS MCPサーバー | `src/rss/mcp/server.py` |

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| E001: テーマ設定ファイルエラー | ファイル存在・JSON形式を確認 |
| E002: RSS MCP ツールエラー | 自動リトライ（3秒待機）、.mcp.json設定を確認 |
| E003: GitHub CLI エラー | `gh auth login` で認証 |
| E004: ネットワークエラー | 自動リトライ（最大3回） |
| E005: GitHub API レート制限 | --limit で取得数を削減、1時間待機 |
| E006: 並列実行エラー | 失敗テーマのみ --themes で再実行 |

## 制約事項

- **GitHub API**: 1時間あたり5000リクエスト
- **RSS取得**: フィードの保持件数に依存（通常10〜50件）
- **重複チェック**: 指定日数（--days）と同じ範囲の既存Issueを対象
- **実行頻度**: 1日1回を推奨（定期実行で取り漏れを防ぐ）
