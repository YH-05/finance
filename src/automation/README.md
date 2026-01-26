# automation

Claude Agent SDK を使った自動化スクリプト集。金融ニュース収集などのワークフローを自動実行します。

## 概要

このパッケージは、Claude Code のスキルやワークフローをプログラマティックに実行するためのスクリプトを提供します。

**主な特徴:**

- Claude Agent SDK による自動化
- 定期実行（cron / launchd）対応
- MCP サーバー設定の自動読み込み（`.mcp.json`）
- 構造化ロギング

## ディレクトリ構成

```
automation/
├── __init__.py          # パッケージ定義
├── __main__.py          # モジュールエントリポイント
├── README.md            # このファイル
└── news_collector.py    # finance-news-workflow 実行スクリプト
```

## インストール

```bash
# automation 依存関係をインストール
uv sync --extra automation
```

## モジュール詳細

### news_collector.py

`/finance-news-workflow` コマンドを Claude Agent SDK 経由で実行するスクリプト。

| 関数/クラス | 役割 |
|------------|------|
| `NewsCollectorConfig` | 設定用 dataclass |
| `NewsCollector` | ニュース収集の実行管理 |
| `run_news_collection()` | async メインエントリポイント |
| `main()` | CLI エントリポイント |

## 使用例

### Python から実行

```python
from automation.news_collector import run_news_collection

# デフォルト設定で実行
await run_news_collection()

# オプション指定
await run_news_collection(
    days=3,
    themes=["index", "macro"],
    dry_run=True
)
```

### CLI から実行

```bash
# 基本実行
uv run python -m automation.news_collector

# オプション付き
uv run python -m automation.news_collector --days 3 --themes index,macro --dry-run

# スクリプトエントリポイントから実行
uv run collect-finance-news --days 7
```

### シェルスクリプトから実行

```bash
# プロジェクトルートから
./scripts/collect-news.sh

# オプション付き
./scripts/collect-news.sh --days 3 --dry-run
```

## 定期実行の設定

### Cron（Linux/macOS）

```crontab
# 毎日朝7時に実行
0 7 * * * /path/to/finance/scripts/collect-news.sh >> /var/log/finance-news.log 2>&1
```

### Launchd（macOS）

```bash
# plist ファイルをコピー（パスを環境に合わせて編集）
cp scripts/com.finance.news-collector.plist ~/Library/LaunchAgents/

# 有効化
launchctl load ~/Library/LaunchAgents/com.finance.news-collector.plist

# 無効化
launchctl unload ~/Library/LaunchAgents/com.finance.news-collector.plist

# 手動実行テスト
launchctl start com.finance.news-collector
```

## 依存関係

- `claude-agent-sdk>=0.1.22`: Claude Agent SDK
- `anyio>=4.0.0`: 非同期ランタイム
- `database`: ロギングユーティリティ（フォールバックあり）

## MCP サーバー設定

プロジェクトルートの `.mcp.json` を自動的に読み込みます。
RSS MCP サーバーなどが設定されている場合、そのまま利用可能です。

## 関連リソース

| リソース | パス |
|---------|------|
| finance-news-workflow スキル | `.claude/skills/finance-news-workflow/SKILL.md` |
| テーマ設定 | `data/config/finance-news-themes.json` |
| 定期実行スクリプト | `scripts/collect-news.sh` |
| launchd plist | `scripts/com.finance.news-collector.plist` |
| GitHub Project | https://github.com/users/YH-05/projects/15 |

## 更新履歴

このREADME.mdは、モジュール構造や公開APIに変更があった場合に更新してください。
