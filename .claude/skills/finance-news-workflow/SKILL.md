---
name: finance-news-workflow
description: 金融ニュース収集の3フェーズワークフロー。Python CLI前処理→テーマ別news-article-fetcher並列呼び出し→結果報告。
allowed-tools: Read, Bash, Task
---

# 金融ニュース収集ワークフロー

RSSフィードから金融ニュースを自動収集し、GitHub Project #15に投稿するワークフロースキル。

## アーキテクチャ

```
/finance-news-workflow (このスキル = オーケストレーター)
  │
  ├── Phase 1: Python CLI前処理
  │     └── prepare_news_session.py
  │           ├── 既存Issue取得・URL抽出
  │           ├── RSS取得（全テーマ一括）
  │           ├── 公開日時フィルタリング
  │           ├── 重複チェック
  │           └── テーマ別JSONファイル出力（.tmp/news-batches/）
  │
  ├── Phase 2: news-article-fetcher 並列呼び出し（11テーマ）
  │     ├── Task(news-article-fetcher, index.json)
  │     ├── Task(news-article-fetcher, stock.json)
  │     ├── Task(news-article-fetcher, sector.json)
  │     ├── Task(news-article-fetcher, macro_cnbc.json)
  │     ├── Task(news-article-fetcher, macro_other.json)
  │     ├── Task(news-article-fetcher, ai_cnbc.json)
  │     ├── Task(news-article-fetcher, ai_nasdaq.json)
  │     ├── Task(news-article-fetcher, ai_tech.json)
  │     ├── Task(news-article-fetcher, finance_cnbc.json)
  │     ├── Task(news-article-fetcher, finance_nasdaq.json)
  │     └── Task(news-article-fetcher, finance_other.json)
  │
  └── Phase 3: 結果集約・報告
        └── 各エージェントの完了を待ち、統計を報告
```

## 使用方法

```bash
# 標準実行（デフォルト: 過去7日間）
/finance-news-workflow

# オプション付き
/finance-news-workflow --days 3 --themes "index,macro_cnbc"
```

## Phase 1: Python CLI前処理

### ステップ1.1: 環境確認

```bash
# テーマ設定ファイル確認
test -f data/config/finance-news-themes.json

# GitHub CLI 確認
gh auth status
```

### ステップ1.2: Python CLI実行 + テーマ別JSON出力

```bash
# 1. セッションファイル作成
uv run python scripts/prepare_news_session.py --days ${days}

# 2. テーマ別JSONファイル作成
python3 << 'EOF'
import json
from pathlib import Path

session_file = Path(".tmp/news-YYYYMMDD-HHMMSS.json")  # 最新のセッションファイル
session = json.load(open(session_file))

output_dir = Path(".tmp/news-batches")
output_dir.mkdir(exist_ok=True)

config = session["config"]

for theme_key, theme_data in session["themes"].items():
    articles = theme_data["articles"]
    theme_config = theme_data["theme_config"]

    issue_config = {
        "theme_key": theme_key,
        "theme_label": theme_config["name_ja"].split(" (")[0],
        "status_option_id": theme_config["github_status_id"],
        "project_id": config["project_id"],
        "project_number": config["project_number"],
        "project_owner": config["project_owner"],
        "repo": "YH-05/finance",
        "status_field_id": config["status_field_id"],
        "published_date_field_id": config["published_date_field_id"]
    }

    output_file = output_dir / f"{theme_key}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "articles": articles,
            "issue_config": issue_config
        }, f, ensure_ascii=False, indent=2)

    print(f"{theme_key}: {len(articles)} articles -> {output_file}")
EOF
```

**出力ファイル形式**（各テーマ）:

```json
{
  "articles": [
    {
      "url": "https://...",
      "title": "...",
      "summary": "...",
      "feed_source": "...",
      "published": "2026-01-29T12:00:00+00:00"
    }
  ],
  "issue_config": {
    "theme_key": "index",
    "theme_label": "株価指数",
    "status_option_id": "3925acc3",
    "project_id": "PVT_kwHOBoK6AM4BMpw_",
    "project_number": 15,
    "project_owner": "YH-05",
    "repo": "YH-05/finance",
    "status_field_id": "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
    "published_date_field_id": "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
  }
}
```

## Phase 2: news-article-fetcher 並列呼び出し

### ステップ2.1: 全テーマを並列で呼び出し

**重要**: 11テーマ全てを**1つのメッセージ内で並列呼び出し**すること。

```python
# 11テーマを並列で呼び出し（1メッセージに11個のTask呼び出し）
themes = [
    "index", "stock", "sector",
    "macro_cnbc", "macro_other",
    "ai_cnbc", "ai_nasdaq", "ai_tech",
    "finance_cnbc", "finance_nasdaq", "finance_other"
]

# 各テーマのJSONファイルを読み込み、news-article-fetcherに渡す
for theme in themes:
    json_file = f".tmp/news-batches/{theme}.json"
    data = json.load(open(json_file))

    Task(
        subagent_type="news-article-fetcher",
        description=f"{theme}: {len(data['articles'])}件の記事処理",
        prompt=f"""以下の記事データを処理してください。

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

各記事に対して:
1. 3段階フォールバックで本文取得
2. 日本語要約生成
3. Issue作成・close
4. Project追加・Status/Date設定

JSON形式で結果を返してください。""",
        run_in_background=True  # バックグラウンド実行
    )
```

### ステップ2.2: 完了待ち

全エージェントの完了を待ち、結果を集約:

```python
# TaskOutputで各エージェントの結果を取得
results = {}
for theme in themes:
    result = TaskOutput(task_id=agent_ids[theme], block=True, timeout=600000)
    results[theme] = parse_result(result)
```

## Phase 3: 結果報告

### サマリー出力形式

```markdown
## 金融ニュース収集完了

### 全体統計

| 項目 | 件数 |
|------|------|
| 前処理：取得記事数 | {total} |
| 前処理：重複スキップ | {duplicates} |
| 投稿対象 | {accessible} |
| Issue作成成功 | {created} |
| Issue作成失敗 | {failed} |

### テーマ別統計

| テーマ | 対象 | 作成 | 失敗 | 抽出方法 |
|--------|------|------|------|----------|
| Index（株価指数） | {n} | {created} | {failed} | Tier1/2/3 |
| Stock（個別銘柄） | {n} | {created} | {failed} | Tier1/2/3 |
| ... | ... | ... | ... | ... |

### セッション情報

- **実行時刻**: {timestamp}
- **セッションファイル**: {session_file}
```

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| --days | 7 | 過去何日分のニュースを対象とするか |
| --themes | all | 対象テーマ（index,stock,... / all） |

## テーマ一覧

| テーマキー | 日本語名 | GitHub Status |
|------------|----------|---------------|
| index | 株価指数 | Index |
| stock | 個別銘柄 | Stock |
| sector | セクター | Sector |
| macro_cnbc | マクロ経済 (CNBC) | Macro |
| macro_other | マクロ経済 (その他) | Macro |
| ai_cnbc | AI (CNBC) | AI |
| ai_nasdaq | AI (NASDAQ) | AI |
| ai_tech | AI (テックメディア) | AI |
| finance_cnbc | 金融 (CNBC) | Finance |
| finance_nasdaq | 金融 (NASDAQ) | Finance |
| finance_other | 金融 (その他) | Finance |

## 関連リソース

| リソース | パス |
|---------|------|
| Python CLI前処理 | `scripts/prepare_news_session.py` |
| テーマ設定 | `data/config/finance-news-themes.json` |
| news-article-fetcher | `.claude/agents/news-article-fetcher.md` |
| GitHub Project | https://github.com/users/YH-05/projects/15 |

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| E001: テーマ設定ファイルエラー | ファイル存在・JSON形式を確認 |
| E002: Python CLI エラー | prepare_news_session.py のログを確認 |
| E003: GitHub CLI エラー | `gh auth login` で認証 |
| E004: news-article-fetcher 失敗 | JSONファイルから手動再実行 |

## 変更履歴

### 2026-01-29: テーマエージェント廃止

- **テーマエージェント廃止**: 11個のテーマエージェントを `trash/agents/` に移動
- **直接呼び出し方式**: スキルから news-article-fetcher を直接呼び出す
- **ネスト削減**: 3段 → 1段（スキル → news-article-fetcher）
- **ペイウォールチェック削除**: prepare_news_session.py から削除（処理時間: 30分 → 10秒）

### 2026-01-29: 新アーキテクチャ移行（初版）

- **オーケストレーター廃止**: `finance-news-orchestrator.md` を `trash/` に移動
- **Python CLI前処理追加**: 決定論的処理をPythonに移行
- **3段階フォールバック追加**: trafilatura → Playwright → RSS Summary

## 制約事項

- **GitHub API**: 1時間あたり5000リクエスト
- **RSS取得**: フィードの保持件数に依存（通常10〜50件）
- **重複チェック**: Python CLIで事前実行
- **実行頻度**: 1日1回を推奨
