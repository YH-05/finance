---
description: AI投資バリューチェーン（77社・10カテゴリ）のブログ/リリースを収集し、投資視点で要約してGitHub Project #44に投稿します。
argument-hint: [--days 7] [--categories all] [--top-n 10]
---

# /ai-research-collect - AI投資バリューチェーン収集

AI企業ブログ/リリースを自動収集し、投資視点で要約してGitHub Project #44に投稿するコマンドです。

## 使用例

```bash
# 標準実行（デフォルト: 過去7日間、全カテゴリ、各最新10件）
/ai-research-collect

# 過去3日間、特定カテゴリ、各最新5件
/ai-research-collect --days 3 --categories "ai_llm,gpu_chips" --top-n 5

# 特定カテゴリのみ
/ai-research-collect --categories "ai_llm"
```

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| --days | - | 7 | 過去何日分の記事を対象とするか |
| --categories | - | all | 対象カテゴリ（ai_llm,gpu_chips,... / all） |
| --top-n | - | 10 | 各カテゴリの最大記事数（公開日時の新しい順） |

## 処理フロー

このコマンドは `ai-research-workflow` スキルを呼び出し、3フェーズで処理を実行します。

```
Phase 1: Python CLI前処理（3分以内）
├── 企業定義マスタ読み込み（77社・10カテゴリ）
├── ティアベース取得ルーティング:
│   ├── Tier 1: FeedReader → RSS対応企業（8社）
│   ├── Tier 2: RobustScraper → 汎用スクレイピング（64社）
│   └── Tier 3: CompanyScraperRegistry → 企業別アダプタ（5社）
├── 日付フィルタリング → 重複チェック → Top-N選択
└── カテゴリ別JSONファイル出力

Phase 2: ai-research-article-fetcher 並列呼び出し（6分以内）
├── 投資視点4セクション要約生成（概要/技術的意義/市場影響/投資示唆）
├── 市場影響度判定（low/medium/high）+ 関連銘柄タグ付け
├── Issue作成 + close → Project #44追加
└── 10カテゴリを並列で処理

Phase 3: 結果集約 + スクレイピング統計レポート（1分以内）
├── カテゴリ別統計
├── ティア別成功率
└── スクレイピング統計サマリー
```

## カテゴリ一覧

| カテゴリキー | 日本語名 | 対象企業数 |
|------------|----------|-----------|
| ai_llm | AI/LLM開発 | 11社 |
| gpu_chips | GPU・演算チップ | 10社 |
| semiconductor_equipment | 半導体製造装置 | 6社 |
| data_center | データセンター・クラウド | 7社 |
| networking | ネットワーキング | 2社 |
| power_energy | 電力・エネルギー | 7社 |
| nuclear_fusion | 原子力・核融合 | 8社 |
| physical_ai | フィジカルAI・ロボティクス | 9社 |
| saas | SaaS・AI活用ソフトウェア | 10社 |
| ai_infra | AI基盤・MLOps | 7社 |

## 実行手順

パラメータをパースした後、`ai-research-workflow` スキルに制御を委譲します。

### パラメータ解析

```python
# デフォルト値
days = 7
categories = "all"
top_n = 10

# 引数からオーバーライド
# --days <N>: 過去N日分の記事を対象
# --categories <list>: カンマ区切りのカテゴリキー、または "all"
# --top-n <N>: 各カテゴリの最大記事数
```

### スキル呼び出し

解析したパラメータを `ai-research-workflow` スキルに渡して実行:

```
Skill: ai-research-workflow
Input: days, categories, top_n
```

## 関連リソース

| リソース | パス |
|---------|------|
| ai-research-workflow スキル | `.claude/skills/ai-research-workflow/SKILL.md` |
| ai-research-article-fetcher | `.claude/agents/ai-research-article-fetcher.md` |
| Python CLI前処理 | `scripts/prepare_ai_research_session.py` |
| 企業定義マスタ | `data/config/ai-research-companies.json` |
| GitHub Project #44 | https://github.com/users/YH-05/projects/44 |
| プロジェクト計画 | `docs/project/ai-research-tracking/project.md` |

## 関連コマンド

- **金融ニュース収集**: `/finance-news-workflow`（RSSフィード経由の金融ニュース収集）
- **週次レポート生成**: `/generate-market-report`（週次マーケットレポート）
- **リサーチ実行**: `/finance-research`（記事向けディープリサーチ）
