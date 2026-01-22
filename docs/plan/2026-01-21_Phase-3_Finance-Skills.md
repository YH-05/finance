# フェーズ 3: 金融分析スキル

> 元ドキュメント: `2026-01-21_System-Update-Implementation.md`

## 目標

7つの金融分析スキルを実装し、金融エージェント群に統合する：

**🔴 Wave 0（最優先 - ニュース収集システム）**:
1. **finance-news-workflow スキル** - `/collect-finance-news` コマンドの完全スキル移行

**Wave 1（データ取得・基盤）**:
2. market-data スキル（MarketData API、yfinance/FRED統合）
3. rss-integration スキル（RSSライブラリ統合）

**Wave 2（分析スキル）**:
4. technical-analysis スキル（Analysis API、テクニカル指標）
5. financial-calculations スキル（リターン計算、相関分析）

**Wave 3（外部連携）**:
6. sec-edgar スキル（SEC EDGAR MCP統合）
7. web-research スキル（Tavily MCP、Web検索）

---

## Wave 0: finance-news-workflow スキル（最優先）

### 概要

`/collect-finance-news` コマンドをスキルベースに完全移行し、関連するエージェント・コマンド・スキルを整理する。

### 統合対象

| 種別 | ファイル | 役割 |
|------|---------|------|
| **コマンド** | `.claude/commands/collect-finance-news.md` | ニュース収集エントリーポイント |
| **スキル** | `.claude/skills/finance-news-collection/SKILL.md` | ワークフロー定義（既存） |
| **エージェント** | `.claude/agents/finance-news-orchestrator.md` | オーケストレーター |
| **エージェント** | `.claude/agents/finance-news-collector.md` | メインコレクター |
| **エージェント** | `.claude/agents/finance-news-index.md` | Indexテーマ |
| **エージェント** | `.claude/agents/finance-news-stock.md` | Stockテーマ |
| **エージェント** | `.claude/agents/finance-news-sector.md` | Sectorテーマ |
| **エージェント** | `.claude/agents/finance-news-macro.md` | Macroテーマ |
| **エージェント** | `.claude/agents/finance-news-ai.md` | AIテーマ |
| **エージェント** | `.claude/agents/finance-news-finance.md` | Financeテーマ |

### 設計方針

#### 1. スキル構造

```
.claude/skills/finance-news-workflow/
├── SKILL.md                    # クイックリファレンス（概要、4フェーズフロー）
├── guide.md                    # 詳細ガイド（フィルタリング、重複チェック）
├── templates/
│   ├── issue-template.md       # Issue作成テンプレート
│   └── summary-template.md     # 結果サマリーテンプレート
└── examples/
    ├── daily-collection.md     # 日次収集パターン
    ├── theme-filtering.md      # テーマフィルタリングパターン
    └── dry-run.md              # dry-runモードパターン
```

#### 2. コマンドとスキルの関係

**決定**: コマンドはスキルを参照する形式に変更（**スキル完成後、削除**）

```markdown
# /collect-finance-news コマンド（変更後）

参照スキル:
- @.claude/skills/finance-news-workflow/SKILL.md

このスキルに従って処理を実行してください。
```

#### 3. エージェントの整理

**決定**: テーマ別エージェントを維持、スキル参照を追加

| エージェント | 変更内容 |
|------------|----------|
| finance-news-orchestrator | `skills: [finance-news-workflow, rss-integration]` 追加 |
| finance-news-collector | `skills: [finance-news-workflow, rss-integration]` 追加 |
| finance-news-* (テーマ別) | `skills: [finance-news-workflow]` 追加、共通処理をスキルから参照 |

### SKILL.md 概要

```markdown
---
name: finance-news-workflow
description: 金融ニュース収集の4フェーズワークフロー。RSS取得→フィルタリング→重複チェック→GitHub投稿。
allowed-tools: Read, Bash, Task, MCPSearch
---
```

**クイックリファレンス内容**:
- 4フェーズワークフロー（初期化→データ準備→テーマ別収集→結果報告）
- パラメータ一覧（--since, --themes, --limit, --dry-run）
- テーマ設定ファイル構造
- RSS MCP ツール一覧

### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.0.1 | SKILL.md の作成 | なし | `.claude/skills/finance-news-workflow/SKILL.md` |
| 3.0.2 | guide.md の作成 | 3.0.1 | `guide.md` |
| 3.0.3 | templates/ の作成 | 3.0.1 | `templates/` |
| 3.0.4 | examples/ の作成 | 3.0.1 | `examples/` |
| 3.0.5 | /collect-finance-news コマンドの更新 | 3.0.2 | コマンド更新 |
| 3.0.6 | オーケストレーター・コレクターエージェントの更新 | 3.0.2 | エージェント更新 |
| 3.0.7 | テーマ別エージェント群の更新 | 3.0.2 | エージェント更新（6件） |
| 3.0.8 | 既存 finance-news-collection スキルの統合・削除 | 3.0.5 | スキル整理 |
| 3.0.9 | 検証 | 3.0.7 | 動作確認 |

**並列実行可能**: 3.0.3〜3.0.4

### Wave 0 完了基準

#### スキル作成
- [ ] `.claude/skills/finance-news-workflow/` が存在し、SKILL.md, guide.md, templates/, examples/ が揃っている
- [ ] 既存 `.claude/skills/finance-news-collection/` が統合・削除されている

#### コマンド更新
- [ ] `/collect-finance-news` がスキルを参照する形式に変更されている
- [ ] `/collect-finance-news --dry-run` が動作する
- [ ] `/collect-finance-news --themes "index,stock"` が動作する

#### エージェント更新
- [ ] `finance-news-orchestrator.md` が `skills: [finance-news-workflow]` を参照
- [ ] `finance-news-collector.md` が `skills: [finance-news-workflow]` を参照
- [ ] 6つのテーマ別エージェントが `skills: [finance-news-workflow]` を参照

#### 品質確認
- [ ] `/collect-finance-news` の既存機能が全て動作
- [ ] テーマ別並列実行が正常動作
- [ ] GitHub Project への投稿が正常動作

---

## Wave 1-3: 金融分析スキル（元の計画）

### 設計方針

#### 1. 既存ライブラリとの関係

**決定**: スキルは既存ライブラリ（`src/market_analysis/`, `src/rss/`）の使用ガイドとベストプラクティスを提供

- スキルは「ナレッジ（知識・手順・テンプレート）」を提供
- 実際の処理は既存の Python ライブラリと MCP ツールを活用
- Python スクリプトの新規実装は行わない

#### 2. スキルの粒度

**決定**: 機能領域ごとに独立したスキル

- データ取得系（market-data, rss-integration）
- 分析系（technical-analysis, financial-calculations）
- 外部連携系（sec-edgar, web-research）

#### 3. エージェントへの統合

**決定**: 金融エージェント群のフロントマターにスキル参照を追加

```yaml
# 例: finance-technical-analysis エージェント
skills:
  - market-data
  - technical-analysis
```

---

### 3.1 market-data スキル

#### 構造

```
.claude/skills/market-data/
├── SKILL.md              # クイックリファレンス（API概要、基本使用法）
├── guide.md              # 詳細ガイド（キャッシュ、リトライ、エラーハンドリング）
└── examples/
    ├── stock-data.md     # 株式データ取得パターン
    ├── forex-data.md     # 為替データ取得パターン
    ├── fred-data.md      # 経済指標（FRED）取得パターン
    └── multi-asset.md    # 複数資産並列取得パターン
```

#### SKILL.md 概要

```markdown
---
name: market-data
description: market_analysis.api.MarketData を使用した市場データ取得のベストプラクティス。yfinance/FRED統合、キャッシュ、リトライ戦略。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- MarketData 初期化パターン（キャッシュ・リトライ設定）
- `fetch_stock()`, `fetch_forex()`, `fetch_fred()` の使用法
- `to_agent_json()` でのエージェント出力変換
- 主要エラーコードと対処法

**プリロード対象エージェント**:
- `finance-technical-analysis`
- `finance-economic-analysis`
- `finance-market-data`
- `dr-source-aggregator`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.1.1 | SKILL.md の作成 | なし | `.claude/skills/market-data/SKILL.md` |
| 3.1.2 | guide.md の作成 | 3.1.1 | `guide.md` |
| 3.1.3 | examples/stock-data.md の作成 | 3.1.1 | `examples/stock-data.md` |
| 3.1.4 | examples/forex-data.md の作成 | 3.1.1 | `examples/forex-data.md` |
| 3.1.5 | examples/fred-data.md の作成 | 3.1.1 | `examples/fred-data.md` |
| 3.1.6 | examples/multi-asset.md の作成 | 3.1.1 | `examples/multi-asset.md` |
| 3.1.7 | エージェントへのスキル参照追加 | 3.1.2 | エージェント更新 |
| 3.1.8 | 検証 | 3.1.7 | 動作確認 |

**並列実行可能**: 3.1.3〜3.1.6

---

### 3.2 rss-integration スキル

#### 構造

```
.claude/skills/rss-integration/
├── SKILL.md              # クイックリファレンス（API概要、基本使用法）
├── guide.md              # 詳細ガイド（フィード管理、差分検出、バッチ処理）
└── examples/
    ├── feed-management.md    # フィード登録・管理パターン
    ├── item-fetching.md      # アイテム取得・検索パターン
    └── mcp-integration.md    # MCP ツール活用パターン
```

#### SKILL.md 概要

```markdown
---
name: rss-integration
description: rss ライブラリを使用したフィード管理・取得のベストプラクティス。差分検出、重複排除、MCP統合。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- FeedManager, FeedFetcher, FeedReader の使用法
- MCP ツール（`mcp__rss__*`）の活用
- 差分検出・重複排除パターン
- バッチスケジューリング

**プリロード対象エージェント**:
- `finance-news-collector`
- `finance-news-*`（テーマ別エージェント群）

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.2.1 | SKILL.md の作成 | なし | `.claude/skills/rss-integration/SKILL.md` |
| 3.2.2 | guide.md の作成 | 3.2.1 | `guide.md` |
| 3.2.3 | examples/feed-management.md の作成 | 3.2.1 | `examples/feed-management.md` |
| 3.2.4 | examples/item-fetching.md の作成 | 3.2.1 | `examples/item-fetching.md` |
| 3.2.5 | examples/mcp-integration.md の作成 | 3.2.1 | `examples/mcp-integration.md` |
| 3.2.6 | エージェントへのスキル参照追加 | 3.2.2 | エージェント更新 |
| 3.2.7 | 検証 | 3.2.6 | 動作確認 |

**並列実行可能**: 3.2.3〜3.2.5

---

### 3.3 technical-analysis スキル

#### 構造

```
.claude/skills/technical-analysis/
├── SKILL.md              # クイックリファレンス（Analysis API、指標一覧）
├── guide.md              # 詳細ガイド（メソッドチェーン、指標計算、判定基準）
└── examples/
    ├── trend-analysis.md     # トレンド分析（SMA, EMA, MACD）
    ├── momentum-analysis.md  # モメンタム分析（RSI, Stochastic）
    ├── volatility-analysis.md # ボラティリティ分析（BB, ATR）
    └── signal-generation.md  # シグナル生成パターン
```

#### SKILL.md 概要

```markdown
---
name: technical-analysis
description: market_analysis.api.Analysis を使用したテクニカル分析のベストプラクティス。メソッドチェーン、指標計算、シグナル生成。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- Analysis クラスのメソッドチェーン設計
- 主要テクニカル指標（SMA, EMA, RSI, MACD, BB）
- AnalysisResult の活用
- 判定基準テーブル（トレンド、買われ過ぎ/売られ過ぎ）

**プリロード対象エージェント**:
- `finance-technical-analysis`
- `dr-stock-analyzer`
- `dr-sector-analyzer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.3.1 | SKILL.md の作成 | 3.1.2 | `.claude/skills/technical-analysis/SKILL.md` |
| 3.3.2 | guide.md の作成 | 3.3.1 | `guide.md` |
| 3.3.3 | examples/trend-analysis.md の作成 | 3.3.1 | `examples/trend-analysis.md` |
| 3.3.4 | examples/momentum-analysis.md の作成 | 3.3.1 | `examples/momentum-analysis.md` |
| 3.3.5 | examples/volatility-analysis.md の作成 | 3.3.1 | `examples/volatility-analysis.md` |
| 3.3.6 | examples/signal-generation.md の作成 | 3.3.1 | `examples/signal-generation.md` |
| 3.3.7 | エージェントへのスキル参照追加 | 3.3.2 | エージェント更新 |
| 3.3.8 | 検証 | 3.3.7 | 動作確認 |

**並列実行可能**: 3.3.3〜3.3.6

---

### 3.4 financial-calculations スキル

#### 構造

```
.claude/skills/financial-calculations/
├── SKILL.md              # クイックリファレンス（リターン計算、相関分析）
├── guide.md              # 詳細ガイド（計算式、年率化、統計量）
└── examples/
    ├── return-calculations.md    # 多期間リターン計算
    ├── correlation-analysis.md   # 相関分析パターン
    ├── risk-metrics.md           # リスク指標（ボラティリティ、シャープ比）
    └── performance-attribution.md # パフォーマンス帰属分析
```

#### SKILL.md 概要

```markdown
---
name: financial-calculations
description: 金融計算のベストプラクティス。リターン計算、相関分析、リスク指標、年率化。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- `MultiPeriodReturns` の使用法
- `CorrelationAnalyzer` の使用法
- 年率化係数（252日、12ヶ月、52週）
- 統計量（平均、標準偏差、シャープ比、最大ドローダウン）

**プリロード対象エージェント**:
- `finance-technical-analysis`
- `dr-stock-analyzer`
- `dr-macro-analyzer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.4.1 | SKILL.md の作成 | 3.1.2 | `.claude/skills/financial-calculations/SKILL.md` |
| 3.4.2 | guide.md の作成 | 3.4.1 | `guide.md` |
| 3.4.3 | examples/return-calculations.md の作成 | 3.4.1 | `examples/return-calculations.md` |
| 3.4.4 | examples/correlation-analysis.md の作成 | 3.4.1 | `examples/correlation-analysis.md` |
| 3.4.5 | examples/risk-metrics.md の作成 | 3.4.1 | `examples/risk-metrics.md` |
| 3.4.6 | examples/performance-attribution.md の作成 | 3.4.1 | `examples/performance-attribution.md` |
| 3.4.7 | エージェントへのスキル参照追加 | 3.4.2 | エージェント更新 |
| 3.4.8 | 検証 | 3.4.7 | 動作確認 |

**並列実行可能**: 3.4.3〜3.4.6

---

### 3.5 sec-edgar スキル

#### 構造

```
.claude/skills/sec-edgar/
├── SKILL.md              # クイックリファレンス（MCP ツール一覧、基本使用法）
├── guide.md              # 詳細ガイド（ファイリング種別、財務データ抽出）
└── examples/
    ├── company-info.md       # 企業情報取得パターン
    ├── financial-statements.md # 財務諸表取得パターン
    ├── insider-trading.md    # インサイダー取引分析パターン
    └── filing-analysis.md    # 8-K/10-K/10-Q 分析パターン
```

#### SKILL.md 概要

```markdown
---
name: sec-edgar
description: SEC EDGAR MCP ツールを使用した企業情報・財務データ取得のベストプラクティス。
allowed-tools: Read, ToolSearch, mcp__sec-edgar-mcp__*
---
```

**クイックリファレンス内容**:
- MCP ツール一覧（`mcp__sec-edgar-mcp__*`）
- CIK 取得、企業情報、財務諸表
- インサイダー取引データ
- ファイリング分析（8-K, 10-K, 10-Q）

**プリロード対象エージェント**:
- `finance-sec-filings`
- `dr-stock-analyzer`
- `finance-fact-checker`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.5.1 | SKILL.md の作成 | なし | `.claude/skills/sec-edgar/SKILL.md` |
| 3.5.2 | guide.md の作成 | 3.5.1 | `guide.md` |
| 3.5.3 | examples/company-info.md の作成 | 3.5.1 | `examples/company-info.md` |
| 3.5.4 | examples/financial-statements.md の作成 | 3.5.1 | `examples/financial-statements.md` |
| 3.5.5 | examples/insider-trading.md の作成 | 3.5.1 | `examples/insider-trading.md` |
| 3.5.6 | examples/filing-analysis.md の作成 | 3.5.1 | `examples/filing-analysis.md` |
| 3.5.7 | エージェントへのスキル参照追加 | 3.5.2 | エージェント更新 |
| 3.5.8 | 検証 | 3.5.7 | 動作確認 |

**並列実行可能**: 3.5.3〜3.5.6

---

### 3.6 web-research スキル

#### 構造

```
.claude/skills/web-research/
├── SKILL.md              # クイックリファレンス（Tavily MCP、WebFetch、検索戦略）
├── guide.md              # 詳細ガイド（検索クエリ設計、ソース評価、情報統合）
└── examples/
    ├── news-search.md        # ニュース検索パターン
    ├── company-research.md   # 企業調査パターン
    ├── market-analysis.md    # 市場分析調査パターン
    └── fact-verification.md  # ファクトチェックパターン
```

#### SKILL.md 概要

```markdown
---
name: web-research
description: Tavily MCP および WebFetch を使用した Web 調査のベストプラクティス。検索戦略、ソース評価、情報統合。
allowed-tools: Read, WebFetch, WebSearch, ToolSearch, mcp__tavily__*
---
```

**クイックリファレンス内容**:
- Tavily MCP ツール（`mcp__tavily__tavily-search`, `tavily-extract`）
- WebFetch / WebSearch の使用法
- 検索クエリ設計パターン
- ソース信頼性評価基準

**プリロード対象エージェント**:
- `finance-web`
- `finance-wiki`
- `finance-fact-checker`
- `dr-source-aggregator`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.6.1 | SKILL.md の作成 | なし | `.claude/skills/web-research/SKILL.md` |
| 3.6.2 | guide.md の作成 | 3.6.1 | `guide.md` |
| 3.6.3 | examples/news-search.md の作成 | 3.6.1 | `examples/news-search.md` |
| 3.6.4 | examples/company-research.md の作成 | 3.6.1 | `examples/company-research.md` |
| 3.6.5 | examples/market-analysis.md の作成 | 3.6.1 | `examples/market-analysis.md` |
| 3.6.6 | examples/fact-verification.md の作成 | 3.6.1 | `examples/fact-verification.md` |
| 3.6.7 | エージェントへのスキル参照追加 | 3.6.2 | エージェント更新 |
| 3.6.8 | 検証 | 3.6.7 | 動作確認 |

**並列実行可能**: 3.6.3〜3.6.6

---

## タスク分解（GitHub Issue）

### Wave 0: ニュース収集システム（最優先）

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.0.1 | [スキル移行] finance-news-workflow スキル SKILL.md の作成 | M | なし |
| 3.0.2 | [スキル移行] finance-news-workflow スキル guide.md の作成 | M | #3.0.1 |
| 3.0.3 | [スキル移行] finance-news-workflow スキル templates/ の作成 | M | #3.0.1 |
| 3.0.4 | [スキル移行] finance-news-workflow スキル examples/ の作成 | M | #3.0.1 |
| 3.0.5 | [スキル移行] /collect-finance-news コマンドの更新 | S | #3.0.2 |
| 3.0.6 | [スキル移行] finance-news-orchestrator, collector エージェント更新 | S | #3.0.2 |
| 3.0.7 | [スキル移行] テーマ別エージェント群（6件）の更新 | M | #3.0.2 |
| 3.0.8 | [スキル移行] 既存 finance-news-collection スキルの統合・削除 | S | #3.0.5 |
| 3.0.9 | [スキル移行] finance-news-workflow 統合テスト | M | #3.0.7, #3.0.8 |

---

### Wave 1: データ取得・基盤スキル（並列実装可）

**market-data スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.1 | [スキル移行] market-data スキル SKILL.md の作成 | M | なし |
| 3.2 | [スキル移行] market-data スキル guide.md の作成 | M | #3.1 |
| 3.3 | [スキル移行] market-data スキル examples/ の作成 | M | #3.1 |
| 3.4 | [スキル移行] market-data スキル エージェント統合 | S | #3.2 |

**rss-integration スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.5 | [スキル移行] rss-integration スキル SKILL.md の作成 | M | なし |
| 3.6 | [スキル移行] rss-integration スキル guide.md の作成 | M | #3.5 |
| 3.7 | [スキル移行] rss-integration スキル examples/ の作成 | M | #3.5 |
| 3.8 | [スキル移行] rss-integration スキル エージェント統合 | S | #3.6 |

### Wave 2: 分析スキル（並列実装可、Wave 1 依存）

**technical-analysis スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.9 | [スキル移行] technical-analysis スキル SKILL.md の作成 | M | #3.2 |
| 3.10 | [スキル移行] technical-analysis スキル guide.md の作成 | M | #3.9 |
| 3.11 | [スキル移行] technical-analysis スキル examples/ の作成 | M | #3.9 |
| 3.12 | [スキル移行] technical-analysis スキル エージェント統合 | S | #3.10 |

**financial-calculations スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.13 | [スキル移行] financial-calculations スキル SKILL.md の作成 | M | #3.2 |
| 3.14 | [スキル移行] financial-calculations スキル guide.md の作成 | M | #3.13 |
| 3.15 | [スキル移行] financial-calculations スキル examples/ の作成 | M | #3.13 |
| 3.16 | [スキル移行] financial-calculations スキル エージェント統合 | S | #3.14 |

### Wave 3: 外部連携スキル（並列実装可）

**sec-edgar スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.17 | [スキル移行] sec-edgar スキル SKILL.md の作成 | M | なし |
| 3.18 | [スキル移行] sec-edgar スキル guide.md の作成 | M | #3.17 |
| 3.19 | [スキル移行] sec-edgar スキル examples/ の作成 | M | #3.17 |
| 3.20 | [スキル移行] sec-edgar スキル エージェント統合 | S | #3.18 |

**web-research スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.21 | [スキル移行] web-research スキル SKILL.md の作成 | M | なし |
| 3.22 | [スキル移行] web-research スキル guide.md の作成 | M | #3.21 |
| 3.23 | [スキル移行] web-research スキル examples/ の作成 | M | #3.21 |
| 3.24 | [スキル移行] web-research スキル エージェント統合 | S | #3.22 |

### Wave 4: 統合テスト

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.25 | [スキル移行] フェーズ3 全スキルの統合テスト実施 | M | #3.0.9, #3.4, #3.8, #3.12, #3.16, #3.20, #3.24 |

---

## 依存関係グラフ

```
フェーズ2（コーディング + Git操作）
    │
    └── フェーズ3（金融分析）
            │
            ├── 🔴 Wave 0 (最優先: ニュース収集システム)
            │   └── finance-news-workflow: #3.0.1 -> #3.0.2 -> (#3.0.3, #3.0.4) -> #3.0.5~#3.0.8 -> #3.0.9
            │
            ├── Wave 1 (データ取得・基盤)
            │   ├── market-data:      #3.1 -> #3.2, #3.3 -> #3.4
            │   └── rss-integration:  #3.5 -> #3.6, #3.7 -> #3.8
            │
            ├── Wave 2 (分析) ← market-data
            │   ├── technical-analysis:     #3.9 -> #3.10, #3.11 -> #3.12
            │   └── financial-calculations: #3.13 -> #3.14, #3.15 -> #3.16
            │
            ├── Wave 3 (外部連携)
            │   ├── sec-edgar:     #3.17 -> #3.18, #3.19 -> #3.20
            │   └── web-research:  #3.21 -> #3.22, #3.23 -> #3.24
            │
            └── Wave 4 (統合)
                    └── #3.25 ← #3.0.9, #3.4, #3.8, #3.12, #3.16, #3.20, #3.24
```

---

## 検証戦略

| 種別 | 対象 | 検証方法 |
|------|------|---------|
| API 使用例検証 | 各スキル | examples/ のコードが実行可能であることを確認 |
| エージェント統合検証 | 金融エージェント群 | `skills:` フィールドでのスキルロード確認 |
| ワークフロー検証 | 記事作成フロー | `/finance-research` コマンドでのスキル参照確認 |

---

## 完了基準

### Wave 0: ニュース収集システム（最優先）
- [ ] `.claude/skills/finance-news-workflow/` が存在し、SKILL.md, guide.md, templates/, examples/ が揃っている
- [ ] 既存 `.claude/skills/finance-news-collection/` が統合・削除されている
- [ ] `/collect-finance-news` がスキルを参照し、全機能が動作
- [ ] 8つの finance-news-* エージェントがスキルを参照

### Wave 1-3: スキル作成
- [ ] `.claude/skills/market-data/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/rss-integration/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/technical-analysis/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/financial-calculations/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/sec-edgar/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/web-research/` が存在し、SKILL.md, guide.md, examples/ が揃っている

### エージェント更新
- [ ] `finance-technical-analysis.md` が `skills: [market-data, technical-analysis]` を参照
- [ ] `finance-economic-analysis.md` が `skills: [market-data, financial-calculations]` を参照
- [ ] `finance-news-collector.md` が `skills: [finance-news-workflow, rss-integration]` を参照
- [ ] `finance-sec-filings.md` が `skills: [sec-edgar]` を参照
- [ ] `finance-web.md` が `skills: [web-research]` を参照

### 品質確認
- [ ] 全スキルで examples/ のコードが実行可能
- [ ] `/collect-finance-news` コマンドが正常動作（最優先で確認）
- [ ] `/finance-research` コマンドが正常動作

---

## 重要ファイル一覧

### 参照元（既存ライブラリ）

| ファイル | 役割 |
|---------|------|
| `src/market_analysis/api/market_data.py` | MarketData API |
| `src/market_analysis/api/analysis.py` | Analysis API |
| `src/market_analysis/analysis/*.py` | 分析モジュール群 |
| `src/market_analysis/types.py` | 型定義 |
| `src/market_analysis/errors.py` | 例外クラス |
| `src/rss/services/*.py` | RSS サービス層 |
| `src/rss/types.py` | RSS 型定義 |

### 参照元（Wave 0 - ニュース収集）

| ファイル | 役割 |
|---------|------|
| `.claude/commands/collect-finance-news.md` | ニュース収集コマンド |
| `.claude/skills/finance-news-collection/SKILL.md` | 既存ワークフロー定義 |
| `.claude/agents/finance-news-orchestrator.md` | オーケストレーター |
| `.claude/agents/finance-news-collector.md` | メインコレクター |
| `.claude/agents/finance-news-*.md` (6件) | テーマ別エージェント |
| `data/config/finance-news-themes.json` | テーマ設定ファイル |

### 新規作成

| ファイル | 内容 |
|----------|------|
| `.claude/skills/finance-news-workflow/` | **金融ニュース収集ワークフロースキル（最優先）** |
| `.claude/skills/market-data/` | 市場データ取得スキル一式 |
| `.claude/skills/rss-integration/` | RSS 統合スキル一式 |
| `.claude/skills/technical-analysis/` | テクニカル分析スキル一式 |
| `.claude/skills/financial-calculations/` | 金融計算スキル一式 |
| `.claude/skills/sec-edgar/` | SEC EDGAR スキル一式 |
| `.claude/skills/web-research/` | Web 調査スキル一式 |

### 変更対象（金融エージェント）

| ファイル | 変更内容 |
|----------|----------|
| `.claude/commands/collect-finance-news.md` | finance-news-workflow スキルを参照 |
| `.claude/agents/finance-news-orchestrator.md` | `skills: [finance-news-workflow, rss-integration]` を追加 |
| `.claude/agents/finance-news-collector.md` | `skills: [finance-news-workflow, rss-integration]` を追加 |
| `.claude/agents/finance-news-*.md` (6件) | `skills: [finance-news-workflow]` を追加 |
| `.claude/agents/finance-technical-analysis.md` | `skills: [market-data, technical-analysis]` を追加 |
| `.claude/agents/finance-economic-analysis.md` | `skills: [market-data, financial-calculations]` を追加 |
| `.claude/agents/finance-market-data.md` | `skills: [market-data]` を追加 |
| `.claude/agents/finance-sec-filings.md` | `skills: [sec-edgar]` を追加 |
| `.claude/agents/finance-web.md` | `skills: [web-research]` を追加 |
| `.claude/agents/finance-wiki.md` | `skills: [web-research]` を追加 |
| `.claude/agents/finance-fact-checker.md` | `skills: [sec-edgar, web-research]` を追加 |
| `.claude/agents/dr-source-aggregator.md` | `skills: [market-data, web-research]` を追加 |
| `.claude/agents/dr-stock-analyzer.md` | `skills: [market-data, technical-analysis, sec-edgar]` を追加 |

### 削除対象

| ファイル | 理由 |
|----------|------|
| `.claude/skills/finance-news-collection/` | finance-news-workflow に統合 |

---

## 決定事項（フェーズ3 Wave 0）

| 項目 | 決定内容 |
|------|----------|
| 最優先 | `/collect-finance-news` のスキル移行を**フェーズ3の最優先**とする |
| スキル統合 | 既存 finance-news-collection スキルを finance-news-workflow に統合 |
| コマンド | スキルを参照する形式に変更（**スキル完成後、削除**） |
| テーマ別エージェント | 維持、スキル参照を追加 |
| 設定ファイル | `data/config/finance-news-themes.json` は維持 |

---

## フェーズ 4: 記事執筆スキル（後続フェーズ）

- 記事構成スキル
- 批評・推敲スキル
- コンプライアンススキル

---

## 関連ドキュメント

- [フェーズ0: 基盤整備](./2026-01-21_Phase-0_Foundation.md)
- [フェーズ1: レポジトリ管理スキル](./2026-01-21_Phase-1_Repository-Management.md)
- [フェーズ2: コーディング+Git操作スキル](./2026-01-21_Phase-2_Coding-Git-Skills.md)
