# 投資調査・投資チーム ガイド

投資調査・マーケットレポート生成に関わる全てのスキル、コマンド、エージェント、Pythonスクリプトの包括的リファレンス。

## 1. 概要

### カテゴリ一覧

| カテゴリ | コマンド | スキル | リーダー | チームメイト | 主なデータソース |
|---------|---------|--------|---------|------------|----------------|
| 個別銘柄分析 | `/dr-stock` | `dr-stock` | `dr-stock-lead` | 8名 | yfinance, SEC EDGAR, Tavily, 業界プリセット |
| 業界・セクター分析 | `/dr-industry` | `dr-industry` | `dr-industry-lead` | 9名 | yfinance, SEC EDGAR, Tavily, 業界プリセット, 業界メディア |
| 金融リサーチ | `/finance-research` | `deep-research` | `research-lead` | 12名 | yfinance, FRED, SEC EDGAR, Tavily, Wikipedia |
| 週次レポート | `/generate-market-report` | `generate-market-report` | `weekly-report-lead` | 6名 | yfinance, FRED, GitHub Project #15, Tavily, RSS |
| ニュース収集 | `/finance-news-workflow` | `finance-news-workflow` | - | `news-article-fetcher` | RSS MCP, GitHub Project #15 |
| AI投資トラッキング | `/ai-research-collect` | `ai-research-workflow` | - | `ai-research-article-fetcher` | 企業ブログ/リリース(77社), GitHub Project #44 |

### 投資関連エージェント総数: 51

---

## 2. 個別銘柄分析（dr-stock）

### コマンド・スキル

| 種類 | 名前 | 説明 |
|------|------|------|
| コマンド | `/dr-stock` | 個別銘柄の包括的分析を実行 |
| スキル | `dr-stock` | dr-stock-lead 起動とパラメータ設定 |

### エージェント構成

```
dr-stock-lead (リーダー)
├── Phase 1: データ収集（4並列）
│   ├── T1: finance-market-data        [致命的]
│   ├── T2: finance-sec-filings        [致命的]
│   ├── T3: finance-web                [非致命的]
│   └── T4: industry-researcher        [非致命的]
├── Phase 2: 統合・検証（2並列）
│   ├── T5: dr-source-aggregator
│   └── T6: dr-cross-validator         ← 信頼度スコアリング統合済み
├── Phase 3: 深掘り分析
│   └── T7: dr-stock-analyzer          ← 4ピラー分析
├── Phase 4: 出力生成（2並列）
│   ├── T8: dr-report-generator
│   └── T9: dr-visualizer
└── Phase 0, T10: Lead自身が実行（初期化・最終サマリー）
```

**エージェント詳細**:

| エージェント | 役割 | 入力 | 出力 |
|-------------|------|------|------|
| `finance-market-data` | 株価・財務指標・配当履歴の取得 | ティッカー | `market-data.json` |
| `finance-sec-filings` | 10-K/10-Q/8-K/Form 4 の取得・分析 | ティッカー | `sec-filings-data.json` |
| `finance-web` | ニュース・アナリスト評価の検索 | ティッカー + クエリ | `web-data.json` |
| `industry-researcher` | 業界ポジション・競争優位性の調査 | ティッカー + プリセット | `industry-data.json` |
| `dr-source-aggregator` | 4ファイルを統合 | 上記4ファイル | `raw-data.json` |
| `dr-cross-validator` | ソース照合・信頼度スコアリング | `raw-data.json` | `validated-data.json` |
| `dr-stock-analyzer` | 財務・バリュエーション・品質・カタリスト分析 | `validated-data.json` | `stock-analysis.json` |
| `dr-report-generator` | 形式別レポート生成 | `stock-analysis.json` | `report.md` |
| `dr-visualizer` | チャート・図表生成 | `stock-analysis.json` | 画像ファイル群 |

### データソース

| ソース | ツール/API | 取得データ | Tier |
|--------|-----------|-----------|------|
| **Yahoo Finance** | `yfinance` (Python) | 株価、財務指標、配当履歴、ETF構成 | Tier 2 |
| **SEC EDGAR** | `mcp__sec-edgar-mcp__*` | 10-K, 10-Q, 8-K, Form 4, 財務データ | Tier 1 |
| **Web検索** | `Tavily` WebSearch + WebFetch | ニュース、アナリスト評価（最大20件） | Tier 3 |
| **業界プリセット** | ローカル `data/config/industry-research-presets.json` | スクレイピング対象、業界メディアリスト | - |
| **業界レポートキャッシュ** | ローカル `data/raw/industry_reports/` | 蓄積済み業界データ（7日以内で再利用） | - |
| **競争優位性ルール** | ローカル `analyst/Competitive_Advantage/analyst_YK/dogma.md` | 12判断ルール | - |

### Pythonスクリプト

| スクリプト | 概要 |
|-----------|------|
| `src/market/industry/collector.py` | 業界レポート一括収集（McKinsey, BCG, Goldman Sachs等11社） |

### 出力ディレクトリ

```
research/DR_stock_{date}_{TICKER}/
├── 01_data_collection/          # Phase 1 個別出力
│   ├── market-data.json
│   ├── sec-filings-data.json
│   ├── web-data.json
│   └── industry-data.json
├── 02_validation/               # Phase 2
│   ├── raw-data.json
│   └── validated-data.json
├── 03_analysis/                 # Phase 3
│   └── stock-analysis.json
└── 04_output/                   # Phase 4
    ├── report.md
    └── charts/
```

### 実装状況

- **エージェント定義**: 全て完成
- **実運用**: 稼働中
- **dr-confidence-scorer**: `dr-cross-validator` に統合済み（旧エージェントは呼び出し不要）

---

## 3. 業界・セクター分析（dr-industry）

### コマンド・スキル

| 種類 | 名前 | 説明 |
|------|------|------|
| コマンド | `/dr-industry` | セクター・業界の包括的分析を実行 |
| スキル | `dr-industry` | dr-industry-lead 起動とパラメータ設定 |

### エージェント構成

```
dr-industry-lead (リーダー)
├── Phase 1: データ収集（5並列）
│   ├── T1: finance-market-data        [致命的] ← セクターETF + 企業群
│   ├── T2: finance-sec-filings        [非致命的] ← 上位5社のみ
│   ├── T3: finance-web                [非致命的] ← セクターニュース
│   ├── T4: industry-researcher        [致命的] ← 業界分析の中核
│   └── T5: finance-web (2nd)          [非致命的] ← 業界メディア専用
├── Phase 2: 統合・検証（2並列）
│   ├── T6: dr-source-aggregator       ← 5ファイル統合
│   └── T7: dr-cross-validator
├── Phase 3: セクター比較分析
│   └── T8: dr-sector-analyzer         ← dr-stockとの主要差分
├── Phase 4: 出力生成（2並列）
│   ├── T9: dr-report-generator
│   └── T10: dr-visualizer
└── Phase 0, T11: Lead自身が実行
```

**dr-stock との主要な差分**:

| 項目 | dr-stock | dr-industry |
|------|---------|-------------|
| Phase 1 並列数 | 4 | **5**（業界メディア検索 T5 新設） |
| SEC Filings | 致命的 | **非致命的**（個別企業は補助的） |
| industry-researcher | 非致命的 | **致命的**（業界分析の中核） |
| Phase 3 分析 | `dr-stock-analyzer` | **`dr-sector-analyzer`** |
| ソースTier | SEC > 市場 > Web | **業界 > 市場 > SEC** |

### データソース

| ソース | ツール/API | 取得データ | Tier |
|--------|-----------|-----------|------|
| **Yahoo Finance** | `yfinance` | セクターETF（XLK, XLV等）+ 構成企業群 | Tier 2 |
| **SEC EDGAR** | `mcp__sec-edgar-mcp__*` | 上位5社の Competition/Risk Factors セクション | Tier 2 |
| **Web検索（ニュース）** | `Tavily` | セクターニュース、規制動向 | Tier 3 |
| **業界プリセット** | ローカル `data/config/industry-research-presets.json` | 業界メディアリスト、スクレイピング対象 | - |
| **Web検索（業界メディア）** | `Tavily` + WebFetch | McKinsey, BCG, IDC, Gartner等（最大15件） | Tier 3 |
| **業界レポートキャッシュ** | ローカル `data/raw/industry_reports/` | 7日以内の蓄積データ再利用 | - |

### Pythonスクリプト

| スクリプト | 概要 |
|-----------|------|
| `src/market/industry/collector.py` | 業界レポート一括収集（コンサル・投資銀行11社対応） |

### 実装予定

| 対象 | 内容 | 状態 |
|------|------|------|
| `finance-sec-filings` | 複数シンボル対応分岐（type=="industry"時） | 設計完了、実装待ち |
| `industry-researcher` | 7カテゴリソース対応（Bain, Accenture, EY, KPMG追加） | 設計完了、実装待ち |
| `dr-source-aggregator` | `web-media-data.json` を5番目のソースとして追加 | 設計完了、実装待ち |
| `dr-report-generator` | industry テンプレート分岐追加 | 設計完了、実装待ち |

設計ドキュメント: `docs/plan/2026-02-15_dr-industry-lead-design.md`

---

## 4. 金融リサーチ（finance-research）

### コマンド・スキル

| 種類 | 名前 | 説明 |
|------|------|------|
| コマンド | `/finance-research` | 金融リサーチワークフローを実行 |
| スキル | `deep-research` | research-lead 起動と深度オプション設定 |

### エージェント構成

```
research-lead (リーダー)
├── Phase 1: クエリ生成
│   └── task-1: finance-query-generator
├── Phase 2: データ収集（4並列）
│   ├── task-2: finance-market-data     ← yfinance / FRED
│   ├── task-3: finance-web             ← Tavily WebSearch
│   ├── task-4: finance-wiki            ← Wikipedia MCP
│   └── task-5: finance-sec-filings     ← SEC EDGAR MCP
├── Phase 3: データ処理（直列）
│   ├── task-6: finance-source          ← ソース抽出・整理
│   ├── task-7: finance-claims          ← 主張・事実抽出
│   └── task-8: finance-sentiment-analyzer ← センチメント分析
├── Phase 4: 分析・検証（2並列）
│   ├── task-9:  finance-claims-analyzer ← 情報ギャップ検出
│   └── task-10: finance-fact-checker   ← ファクトチェック
└── Phase 5: 決定・可視化
    ├── task-11: finance-decisions      ← 採用/棄却判定
    └── task-12: finance-visualize      ← チャート生成
```

**深度オプション**:

| モード | 説明 | Phase省略 |
|--------|------|----------|
| `shallow` | 基本的な情報収集（8タスク） | Phase 3.5（センチメント）, Phase 4（検証）省略 |
| `deep` | 詳細な情報収集（全12タスク） | なし |
| `auto` | データ量で動的判断 | gap_score > 0.5 で追加タスク（task-13〜19）を動的作成 |

### データソース

| ソース | ツール/API | 取得データ | Tier |
|--------|-----------|-----------|------|
| **Yahoo Finance** | `yfinance` (Python) | 株価、指数、為替 | Tier 2 |
| **FRED** | `FREDFetcher` (Python) | 経済指標、金利、インフレ率 | Tier 2 |
| **SEC EDGAR** | `mcp__sec-edgar-mcp__*` | 決算データ、財務諸表 | Tier 1 |
| **Web検索** | `Tavily` WebSearch + WebFetch | ニュース、アナリストレポート | Tier 3 |
| **Wikipedia** | `mcp__wikipedia__*` | 企業概要、背景情報 | Tier 4 |

### Pythonスクリプト

直接呼び出すCLIスクリプトはなし。`src/market/` および `src/analyze/` のライブラリを finance-market-data エージェントが内部利用。

### 実装予定

| 対象 | 内容 | 状態 |
|------|------|------|
| `finance-technical-analysis` | テクニカル指標計算（SMA, EMA, MACD, RSI, Bollinger Bands等10指標） | エージェント定義完成、実装待ち |
| `finance-economic-analysis` | FRED経済指標分析（GDP, CPI, 失業率, FF金利等） | エージェント定義完成、実装待ち |

これら2エージェントは finance-research の Phase 2 に追加予定（並列データ収集を4→6に拡張）。

---

## 5. 週次マーケットレポート（generate-market-report）

### コマンド・スキル

| 種類 | 名前 | 説明 |
|------|------|------|
| コマンド | `/generate-market-report` | 週次マーケットレポートを自動生成 |
| スキル | `generate-market-report` | weekly-report-lead 起動とモード設定 |
| 補助スキル | `weekly-data-aggregation` | データ集約・正規化 |
| 補助スキル | `weekly-comment-generation` | コメント文生成 |
| 補助スキル | `weekly-template-rendering` | テンプレート埋め込み |
| 補助スキル | `weekly-report-validation` | 品質検証 |

### エージェント構成（`--weekly` モード）

```
weekly-report-lead (リーダー) ← 全タスク直列依存
├── Task 1: wr-news-aggregator       ← GitHub Project からニュース集約
├── Task 2: wr-data-aggregator       ← データ統合・正規化
├── Task 3: wr-comment-generator     ← 全10セクションのコメント生成
├── Task 4: wr-template-renderer     ← テンプレート埋め込み → Markdownレポート
├── Task 5: wr-report-validator      ← フォーマット・文字数・データ整合性検証
└── Task 6: wr-report-publisher      ← GitHub Issue作成 + Project #15 追加
```

**コメント生成用ニュース収集エージェント**（`--weekly-comment` モード / wr-comment-generator から呼出）:

| エージェント | 対象 | データソース |
|-------------|------|-------------|
| `weekly-comment-indices-fetcher` | 主要指数（S&P500, Nasdaq, Dow等） | RSS MCP + Tavily |
| `weekly-comment-mag7-fetcher` | MAG7銘柄（AAPL, MSFT, GOOGL等） | RSS MCP + Tavily |
| `weekly-comment-sectors-fetcher` | セクターETF（XLK, XLV等） | RSS MCP + Tavily |

### データソース

| ソース | ツール/API | 取得データ | 使用Phase |
|--------|-----------|-----------|----------|
| **Yahoo Finance** | `yfinance` via スクリプト | 株価指数、セクターETF、MAG7、コモディティ | 前処理 |
| **FRED** | `FREDFetcher` via スクリプト | 金利（DGS2, DGS10, DGS30, FEDFUNDS）、イールドカーブ | 前処理 |
| **GitHub Project #15** | `gh` CLI | 既存ニュースIssue | Task 1 |
| **RSS** | RSS MCP `rss_search_items` | 最新ニュース検索 | Task 3 (コメント生成) |
| **Web検索** | `Tavily` | 補完的ニュース検索 | Task 3 (コメント生成) |
| **為替データ** | `yfinance` via スクリプト | USD/JPY, EUR/USD等 | 前処理 |
| **決算カレンダー** | `yfinance` via スクリプト | 来週の決算予定 | 前処理 |

### Pythonスクリプト

| スクリプト | 概要 | 出力先 |
|-----------|------|--------|
| `scripts/collect_market_performance.py` | 市場パフォーマンス（指数・セクター・MAG7・コモディティ）一括収集 | `data/market/` |
| `scripts/collect_interest_rates.py` | 金利データ収集（DGS2, DGS10, DGS30, FEDFUNDS等） | `data/market/` |
| `scripts/collect_currency_rates.py` | 為替レート収集（USD/JPY等） | `data/market/` |
| `scripts/collect_upcoming_events.py` | 来週の決算・経済指標スケジュール | `data/market/` |
| `scripts/weekly_comment_data.py` | 週次コメント用マーケットデータ統合 | `data/market/` |
| `scripts/market_report_data.py` | 騰落率・セクター・決算カレンダー統合 | `data/market/` |

**スクリプト内の分析クラス**（`src/analyze/reporting/`）:

| クラス | ファイル | 役割 |
|--------|---------|------|
| `PerformanceAnalyzer4Agent` | `performance_agent.py` | 複数期間の騰落率計算（1D, 1W, MTD, YTD） |
| `InterestRateAnalyzer4Agent` | `interest_rate_agent.py` | 金利データ・イールドカーブ分析 |
| `CurrencyAnalyzer4Agent` | `currency_agent.py` | 複数通貨ペアのパフォーマンス計算 |
| `UpcomingEvents4Agent` | `upcoming_events_agent.py` | 決算・経済指標カレンダー生成 |

### 旧実装からの移行

| 旧エージェント | 新エージェント | 状態 |
|---------------|---------------|------|
| `weekly-report-news-aggregator` | `wr-news-aggregator` | 移行済み |
| `weekly-report-publisher` | `wr-report-publisher` | 移行済み |
| - (新規) | `wr-data-aggregator` | 新規追加 |
| - (新規) | `wr-comment-generator` | 新規追加 |
| - (新規) | `wr-template-renderer` | 新規追加 |
| - (新規) | `wr-report-validator` | 新規追加 |

### 出力ディレクトリ

```
articles/weekly_report/{report_dir}/
├── data/
│   ├── news_from_project.json       # Task 1 出力
│   ├── indices.json                 # 前処理出力
│   ├── mag7.json                    # 前処理出力
│   ├── sectors.json                 # 前処理出力
│   ├── aggregated_data.json         # Task 2 出力
│   └── comments.json                # Task 3 出力
├── report.md                        # Task 4 出力
└── validation_result.json           # Task 5 出力
```

---

## 6. 金融ニュース収集（finance-news-workflow）

### コマンド・スキル

| 種類 | 名前 | 説明 |
|------|------|------|
| コマンド | `/finance-news-workflow` | 金融ニュース収集の全ワークフローを実行 |
| スキル | `finance-news-workflow` | 4フェーズワークフロー制御 |

### エージェント構成

```
finance-news-workflow (スキル制御)
├── Phase 1: 前処理（Pythonスクリプト）
│   └── prepare_news_session.py      ← RSS取得 + 既存Issue抽出
├── Phase 2: テーマ別Issue作成（並列）
│   └── news-article-fetcher × N     ← テーマ別に並列起動
└── Phase 3: 結果集約・レポート
```

**news-article-fetcher の処理フロー**:
1. 記事URLから本文取得（WebFetch、3ティア: 一次→二次→Wikipedia）
2. 日本語要約生成
3. GitHub Issue作成
4. Project #15 に自動登録（Status・Category・Published Date フィールド設定）

### データソース

| ソース | ツール/API | 取得データ |
|--------|-----------|-----------|
| **RSS MCP** | `rss_search_items`, `rss_get_items` | フィード記事（タイトル、URL、要約、公開日） |
| **GitHub Project #15** | `gh` CLI | 既存ニュースIssue（重複チェック用） |
| **Web記事本文** | `WebFetch` | 元記事の全文テキスト |
| **ニュース設定** | ローカル `data/config/news-collection-config.yaml` | テーマ定義、フィルタ設定 |
| **RSSプリセット** | ローカル `data/config/rss-presets.json` | フィード購読リスト |
| **テーマ分類** | ローカル `data/config/finance-news-themes.json` | カテゴリ分類ルール |
| **フィルタ** | ローカル `data/config/finance-news-filter.json` | 除外キーワード |

### Pythonスクリプト

| スクリプト | 概要 |
|-----------|------|
| `scripts/prepare_news_session.py` | セッション前処理（既存Issue URL抽出、RSS日付フィルタ、テーマ別バッチJSON出力） |
| `src/news/scripts/finance_news_workflow.py` | メインワークフロー（async対応、per-category/per-article形式） |
| `scripts/collect_finance_news.py` | 金融ニュース収集の統合スクリプト |
| `scripts/collect_finance_news_index.py` | 株価指数テーマ別フィルタリング |
| `scripts/collect_finance_news_stock.py` | 個別銘柄テーマ別フィルタリング |
| `scripts/collect_finance_news_sector.py` | セクターテーマ別フィルタリング |
| `scripts/collect_finance_news_macro.py` | マクロ経済テーマ別フィルタリング |
| `scripts/collect_finance_news_ai.py` | AI/テクノロジーテーマ別フィルタリング |

**定期実行**: `scripts/com.finance.news-collector.plist`（macOS launchd設定）

---

## 7. AI投資バリューチェーン収集（ai-research-collect）

### コマンド・スキル

| 種類 | 名前 | 説明 |
|------|------|------|
| コマンド | `/ai-research-collect` | AI投資バリューチェーン収集を実行 |
| スキル | `ai-research-workflow` | 10カテゴリ並列処理の制御 |

### エージェント構成

```
ai-research-workflow (スキル制御)
├── Phase 1: 前処理（Pythonスクリプト）
│   └── prepare_ai_research_session.py  ← 企業ブログ/リリースのスクレイピング
├── Phase 2: 投資視点要約（10カテゴリ並列）
│   └── ai-research-article-fetcher × 10
└── Phase 3: 結果集約・統計レポート
```

**ai-research-article-fetcher の出力**:
- 概要 / 技術的意義 / 市場影響 / 投資示唆 の4セクション要約
- GitHub Issue作成 + Project #44 登録

### データソース

| ソース | ツール/API | 取得データ |
|--------|-----------|-----------|
| **企業ブログ/リリース** | Python スクレイピング（71社公開URL） | 最新記事タイトル・URL・公開日 |
| **記事本文** | `WebFetch` | 記事全文テキスト |
| **GitHub Project #44** | `gh` CLI（GraphQL） | 既存Issue（重複チェック用） |

### 10カテゴリ・77社

| カテゴリ | 企業例 | 代表ティッカー |
|---------|--------|---------------|
| AI/LLM開発 | OpenAI, Anthropic, Google DeepMind | GOOGL, META, MSFT |
| GPU・演算チップ | NVIDIA, AMD, Intel | NVDA, AMD, INTC |
| 半導体製造装置 | ASML, Applied Materials | ASML, AMAT |
| データセンター | Equinix, Digital Realty | EQIX, DLR |
| クラウドインフラ | AWS, Azure, GCP | AMZN, MSFT, GOOGL |
| AI SaaS | Salesforce, ServiceNow | CRM, NOW |
| サイバーセキュリティ | CrowdStrike, Palo Alto | CRWD, PANW |
| ロボティクス/自動化 | Tesla, Fanuc | TSLA, 6954.T |
| ヘルスケアAI | Illumina, Intuitive Surgical | ILMN, ISRG |
| AI半導体設計 | Broadcom, Marvell | AVGO, MRVL |

### Pythonスクリプト

| スクリプト | 概要 |
|-----------|------|
| `scripts/prepare_ai_research_session.py` | セッション前処理（企業ブログスクレイピング、日付フィルタ、カテゴリ別バッチJSON出力） |

---

## 8. 共通コンポーネント

### 共通エージェント

複数のワークフローで再利用されるエージェント群。

| エージェント | 使用ワークフロー | 役割 |
|-------------|-----------------|------|
| `finance-market-data` | dr-stock, dr-industry, finance-research | yfinance/FREDによる市場データ取得 |
| `finance-sec-filings` | dr-stock, dr-industry, finance-research | SEC EDGAR からの開示情報取得 |
| `finance-web` | dr-stock, dr-industry, finance-research | Tavily WebSearch によるニュース検索 |
| `industry-researcher` | dr-stock, dr-industry | 業界ポジション・競争優位性調査 |
| `dr-source-aggregator` | dr-stock, dr-industry | 複数ソースの統合 |
| `dr-cross-validator` | dr-stock, dr-industry | ソース照合・信頼度スコアリング |
| `dr-report-generator` | dr-stock, dr-industry | 形式別レポート生成 |
| `dr-visualizer` | dr-stock, dr-industry | チャート・図表生成 |
| `news-article-fetcher` | finance-news, ai-research | URL本文取得・要約・Issue作成 |

### 共通Pythonライブラリ

| パッケージ | 主な提供機能 | 使用ワークフロー |
|-----------|-------------|-----------------|
| `src/market/yfinance/` | `YFinanceFetcher` - 株価・指数・為替取得 | dr-stock, dr-industry, weekly-report |
| `src/market/fred/` | `FREDFetcher` - 経済指標取得 | finance-research, weekly-report |
| `src/edgar/` | edgartools ラッパー - SEC開示情報取得 | dr-stock, dr-industry, finance-research |
| `src/analyze/reporting/` | `*4Agent` クラス群 - レポート用データ整形 | weekly-report |
| `src/analyze/visualization/` | チャート生成 | finance-research, dr-stock, dr-industry |
| `src/rss/` | RSSフィード管理・記事抽出 | finance-news, weekly-report |

### 共通ローカル設定ファイル

| ファイル | 用途 | 使用ワークフロー |
|---------|------|-----------------|
| `data/config/industry-research-presets.json` | 業界リサーチ対象・メディアリスト | dr-stock, dr-industry |
| `data/config/rss-presets.json` | RSSフィード購読リスト | finance-news, weekly-report |
| `data/config/news-collection-config.yaml` | ニュース収集の全体設定 | finance-news |
| `data/config/finance-news-themes.json` | ニュースカテゴリ分類ルール | finance-news |
| `data/config/finance-news-filter.json` | 除外キーワード | finance-news |
| `data/config/fred_series.json` | FRED指標定義 | finance-research, weekly-report |

### Agent Teams 設計パターン

全リーダーエージェントに共通する設計要素:

| パターン | 説明 |
|---------|------|
| **ファイルベースデータ受渡し** | チームメイト間は JSON ファイル経由でデータ交換（SendMessage はメタデータのみ） |
| **致命的/非致命的エラー分類** | 致命的失敗は後続キャンセル、非致命的は警告付き続行 |
| **HF（Human Feedback）ポイント** | HF0: パラメータ確認、HF1: 中間結果、HF2: 最終確認 |
| **依存関係管理** | `addBlockedBy` によるタスク依存の明示的設定 |
| **信頼度Tier** | Tier 1（SEC, 公式） > Tier 2（yfinance, FRED） > Tier 3（Web） > Tier 4（Wikipedia, SNS） |

### ローカルキャッシュ構造

```
data/
├── raw/
│   ├── yfinance/              # 株価キャッシュ（24時間TTL）
│   ├── fred/indicators/       # FRED経済指標キャッシュ
│   ├── industry_reports/      # 業界分析蓄積（7日以内で再利用）
│   └── rss/                   # RSSフィード購読データ
├── market/                    # 週次レポート用の市場データ出力
├── processed/                 # 加工済みデータ
└── config/                    # 設定ファイル群
```

---

## 9. 実装ロードマップ

### 優先度高

| 対象 | 内容 | 現状 | 関連カテゴリ |
|------|------|------|-------------|
| `finance-sec-filings` 拡張 | 複数シンボル対応分岐（type=="industry"時） | 設計完了 | dr-industry |
| `industry-researcher` 拡張 | 7カテゴリソース対応（Bain, Accenture, EY, KPMG追加） | 設計完了 | dr-industry |
| `dr-source-aggregator` 拡張 | `web-media-data.json` を5番目のソースとして追加 | 設計完了 | dr-industry |
| `dr-report-generator` 拡張 | industry テンプレート分岐追加 | 設計完了 | dr-industry |
| `finance-technical-analysis` | テクニカル指標計算（SMA, MACD, RSI等10指標） | エージェント定義完成 | finance-research |
| `finance-economic-analysis` | FRED経済指標分析（GDP, CPI, 失業率等） | エージェント定義完成 | finance-research |

### 優先度中

| 対象 | 内容 | 現状 | 関連カテゴリ |
|------|------|------|-------------|
| `/deep-research` ワークフロー統合 | dr-orchestrator を中心とした統合分析（stock/sector/macro/theme 4タイプ対応） | 計画ドキュメント完成 | 全カテゴリ |
| `competitive-advantage-critique` | 競争優位性仮説の批評エージェント | エージェント定義あり | dr-stock, dr-industry |
| `market-hypothesis-generator` | マーケット仮説生成エージェント | エージェント定義あり | weekly-report |

### 旧実装の廃止予定

| 旧エージェント | 代替 | 状態 |
|---------------|------|------|
| `weekly-report-news-aggregator` | `wr-news-aggregator` | 移行済み、廃止可能 |
| `weekly-report-publisher` | `wr-report-publisher` | 移行済み、廃止可能 |
| `dr-confidence-scorer` | `dr-cross-validator` に統合 | 統合済み、廃止可能 |

---

## 10. エージェント全索引

投資調査・投資チーム関連の全エージェント（記事作成系除外）。

| エージェント | カテゴリ | 種別 | 状態 |
|-------------|---------|------|------|
| `ai-research-article-fetcher` | AI投資トラッキング | タスク | 稼働中 |
| `competitive-advantage-critique` | 分析補助 | タスク | 定義済み |
| `dr-bias-detector` | ディープリサーチ | タスク | 定義済み |
| `dr-cross-validator` | ディープリサーチ | タスク（共通） | 稼働中 |
| `dr-industry-lead` | 業界・セクター分析 | リーダー | 稼働中 |
| `dr-macro-analyzer` | ディープリサーチ | タスク | 定義済み |
| `dr-orchestrator` | ディープリサーチ | オーケストレーター | 計画中 |
| `dr-report-generator` | ディープリサーチ | タスク（共通） | 稼働中 |
| `dr-sector-analyzer` | 業界・セクター分析 | タスク | 稼働中 |
| `dr-source-aggregator` | ディープリサーチ | タスク（共通） | 稼働中 |
| `dr-stock-analyzer` | 個別銘柄分析 | タスク | 稼働中 |
| `dr-stock-lead` | 個別銘柄分析 | リーダー | 稼働中 |
| `dr-theme-analyzer` | ディープリサーチ | タスク | 定義済み |
| `dr-visualizer` | ディープリサーチ | タスク（共通） | 稼働中 |
| `finance-claims` | 金融リサーチ | タスク | 稼働中 |
| `finance-claims-analyzer` | 金融リサーチ | タスク | 稼働中 |
| `finance-decisions` | 金融リサーチ | タスク | 稼働中 |
| `finance-economic-analysis` | 金融リサーチ | タスク | **実装待ち** |
| `finance-fact-checker` | 金融リサーチ | タスク | 稼働中 |
| `finance-market-data` | 共通 | タスク | 稼働中 |
| `finance-query-generator` | 金融リサーチ | タスク | 稼働中 |
| `finance-sec-filings` | 共通 | タスク | 稼働中 |
| `finance-sentiment-analyzer` | 金融リサーチ | タスク | 稼働中 |
| `finance-source` | 金融リサーチ | タスク | 稼働中 |
| `finance-technical-analysis` | 金融リサーチ | タスク | **実装待ち** |
| `finance-visualize` | 金融リサーチ | タスク | 稼働中 |
| `finance-web` | 共通 | タスク | 稼働中 |
| `finance-wiki` | 金融リサーチ | タスク | 稼働中 |
| `industry-researcher` | 共通 | タスク | 稼働中 |
| `market-hypothesis-generator` | 週次レポート | タスク | 定義済み |
| `news-article-fetcher` | ニュース収集 | タスク | 稼働中 |
| `research-lead` | 金融リサーチ | リーダー | 稼働中 |
| `weekly-comment-indices-fetcher` | 週次レポート | タスク | 稼働中 |
| `weekly-comment-mag7-fetcher` | 週次レポート | タスク | 稼働中 |
| `weekly-comment-sectors-fetcher` | 週次レポート | タスク | 稼働中 |
| `weekly-report-lead` | 週次レポート | リーダー | 稼働中 |
| `weekly-report-news-aggregator` | 週次レポート | タスク | **廃止予定** |
| `weekly-report-publisher` | 週次レポート | タスク | **廃止予定** |
| `wr-comment-generator` | 週次レポート | タスク | 稼働中 |
| `wr-data-aggregator` | 週次レポート | タスク | 稼働中 |
| `wr-news-aggregator` | 週次レポート | タスク | 稼働中 |
| `wr-report-publisher` | 週次レポート | タスク | 稼働中 |
| `wr-report-validator` | 週次レポート | タスク | 稼働中 |
| `wr-template-renderer` | 週次レポート | タスク | 稼働中 |

**凡例**:
- **リーダー**: Agent Teams のリーダーエージェント（チームメイトの起動・制御）
- **オーケストレーター**: 複数ワークフローの統合制御（計画中）
- **タスク**: リーダーから起動されるチームメイトエージェント
- **タスク（共通）**: 複数ワークフローで再利用されるエージェント
