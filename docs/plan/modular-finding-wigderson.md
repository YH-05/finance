# note執筆ワークフロー実装状況まとめ

## 概要

金融記事作成のエンドツーエンドワークフローが実装済み。トピック提案から記事公開まで自動化されている。

---

## 1. ワークフロー全体構成

```
/finance-full（全工程一括実行）
├── /new-finance-article（フォルダ作成）
├── /finance-research（リサーチ）
└── /finance-edit（執筆/批評）

/finance-suggest-topics（トピック提案）
/collect-finance-news（ニュース収集→GitHub Issues）
```

---

## 2. 実装済みコマンド（6つ）

| コマンド | 機能 | 状態 |
|---------|------|------|
| `/new-finance-article` | フォルダ・テンプレート作成 | ✅ 実装済み |
| `/finance-research` | データ収集→分析→判定 | ✅ 実装済み |
| `/finance-edit` | 初稿→批評→修正 | ✅ 実装済み |
| `/finance-full` | 全工程一括実行 | ✅ 実装済み |
| `/finance-suggest-topics` | トピック提案・スコアリング | ✅ 実装済み |
| `/collect-finance-news` | ニュース収集→GitHub投稿 | ✅ 実装済み |

---

## 3. エージェント体系（28エージェント）

### 3.1 データ収集層（4）
- `finance-query-generator` - 検索クエリ生成
- `finance-market-data` - 株価・指標取得（YFinance/FRED）
- `finance-web` - Web記事検索
- `finance-wiki` - Wikipedia検索

### 3.2 データ処理層（3）
- `finance-source` - 情報源抽出
- `finance-claims` - 主張抽出（7タイプ分類）
- `finance-sentiment-analyzer` - センチメント分析

### 3.3 分析層（5）
- `finance-claims-analyzer` - 主張信頼度評価
- `finance-fact-checker` - ファクトチェック
- `finance-decisions` - 主張採用判定
- `finance-technical-analysis` - テクニカル分析
- `finance-economic-analysis` - 経済分析

### 3.4 執筆層（2）
- `finance-article-writer` - 初稿生成
- `finance-visualize` - チャート生成

### 3.5 批評層（5）
- `finance-critic-fact` - 事実正確性
- `finance-critic-compliance` - 規制要件（**最重要**）
- `finance-critic-structure` - 構成・論理
- `finance-critic-data` - データ正確性
- `finance-critic-readability` - 読みやすさ

### 3.6 修正層（1）
- `finance-reviser` - 批評反映修正

### 3.7 ニュース収集層（7）
- `finance-news-orchestrator` - 初期化・制御
- `finance-news-index` - 株価指数
- `finance-news-stock` - 個別銘柄
- `finance-news-sector` - セクター
- `finance-news-macro` - マクロ経済
- `finance-news-ai` - AI関連
- `finance-sec-filings` - SEC開示

### 3.8 トピック層（1）
- `finance-topic-suggester` - トピック提案

---

## 4. テンプレート構成（5カテゴリ）

| カテゴリ | ターゲット | 文字数 |
|---------|-----------|--------|
| market_report | intermediate | 3000-5000 |
| stock_analysis | intermediate | 4000-6000 |
| economic_indicators | intermediate | 2500-4000 |
| investment_education | beginner | 3000-5000 |
| quant_analysis | advanced | 4000-6000 |

### フォルダ構造
```
articles/{category}_{id}_{slug}/
├── article-meta.json
├── 01_research/
│   ├── queries.json, raw-data.json, sources.json
│   ├── claims.json, fact-checks.json, decisions.json
│   ├── market_data/, visualize/
├── 02_edit/
│   ├── first_draft.md, critic.json, critic.md
│   └── revised_draft.md
└── 03_published/
```

---

## 5. データフロー

```
queries.json
    ↓
raw-data.json (web + wiki + market-data 並列)
    ↓
sources.json
    ↓
claims.json → fact-checks.json → decisions.json
    ↓
first_draft.md
    ↓
critic.json (5エージェント並列)
    ↓
revised_draft.md
```

---

## 6. ヒューマンフィードバックポイント

| ポイント | タイミング | 必須度 |
|---------|-----------|--------|
| HF1 | トピック承認 | 自動可 |
| HF3 | 主張採用確認 | 推奨 |
| HF5 | 初稿レビュー | 推奨 |
| HF6 | 最終確認 | **必須** |

---

## 7. 品質管理

### 批評スコア計算
- compliance: 100 - (critical×30 + high×15 + medium×5 + low×2)
- fact/data/structure/readability: 100 - (high×10 + medium×5 + low×2)

### 修正優先順位
1. compliance critical/high（必須）
2. fact high（必須）
3. data_accuracy high
4. structure high/medium
5. readability high/medium

---

## 8. 特徴的な機能

### 信頼度別表現制御
- verified → 「〜である」
- disputed → 「〜という見方がある」
- speculation → 「〜の可能性がある」

### コンプライアンス
- 禁止表現: 「買うべき」「必ず儲かる」「推奨」
- 必須免責: not-advice（冒頭）、investment-risk（末尾）

### 並列実行最適化
- Phase 2: web + wiki + market-data（3並列）
- Phase 7: 5批評エージェント（5並列）
- 推定実行時間: 逐次120秒 → 並列50秒

---

## 9. 関連スキル

- `finance-news-collection` - ニュース収集ワークフロー定義

---

## 結論

note執筆ワークフローは**完全に実装済み**。6つの統合コマンドと28のエージェントにより、トピック提案から記事公開まで自動化されている。多層品質管理（5批評エージェント）と規制ファースト設計により、金融コンテンツの品質と規制遵守を両立している。
