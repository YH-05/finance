---
description: テーマ別に金融ニュースを収集し、GitHub Project 15に自動投稿します
argument-hint: [--since 1d|3d|7d] [--themes "index,stock,..."] [--limit N] [--dry-run]
---

# /collect-finance-news コマンド

参照スキル:
- @.claude/skills/finance-news-workflow/SKILL.md

このスキルに従って処理を実行してください。

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| --since | 1d | 公開日時フィルタ（1d/3d/7d） |
| --project | 15 | GitHub Project番号 |
| --limit | 50 | 取得記事数の最大値 |
| --themes | all | 対象テーマ（index,stock,sector,macro,ai,finance / all） |
| --dry-run | false | GitHub投稿せずに結果確認のみ |

## 使用例

```bash
# 標準実行
/collect-finance-news

# 過去3日間のニュースを収集
/collect-finance-news --since 3d

# 特定テーマのみ収集
/collect-finance-news --themes "index,macro"

# 投稿せずに結果確認
/collect-finance-news --dry-run

# 複合オプション
/collect-finance-news --since 3d --themes "index,macro" --limit 30 --dry-run
```
