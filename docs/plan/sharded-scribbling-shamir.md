# ディープリサーチワークフロー要件定義・実装計画

## 概要

金融市場・投資テーマ専用のディープリサーチワークフロー `/deep-research` を新規作成する。
既存の `/finance-research`（記事作成用）とは独立した、投資分析特化のワークフロー。

## ユーザー要件

| 項目 | 要件 |
|------|------|
| 出力形式 | 複数形式（note記事/分析レポート/投資メモ） |
| 対象テーマ | 個別銘柄・セクター・マクロ・テーマ投資 |
| 分析深度 | 段階的選択（quick/standard/comprehensive） |
| データソース | バランス型（SEC EDGAR重視、米国株中心） |
| 分析手法 | ファンダメンタル + センチメント分析 |
| 自動化 | 半自動（フェーズ確認あり） |
| 品質管理 | ファクトチェック重視、複数ソースクロス検証 |

## アーキテクチャ

### コンポーネント構成

```
.claude/
├── commands/
│   └── deep-research.md              # メインコマンド
│
├── agents/deep-research/
│   ├── dr-orchestrator.md            # ワークフロー制御
│   │
│   ├── dr-stock-analyzer.md          # 個別銘柄分析
│   ├── dr-sector-analyzer.md         # セクター比較分析
│   ├── dr-macro-analyzer.md          # マクロ経済分析
│   ├── dr-theme-analyzer.md          # テーマ投資分析
│   │
│   ├── dr-source-aggregator.md       # マルチソース集約
│   ├── dr-cross-validator.md         # クロス検証
│   ├── dr-bias-detector.md           # バイアス検出
│   ├── dr-confidence-scorer.md       # 信頼度スコアリング
│   │
│   ├── dr-report-generator.md        # レポート生成
│   └── dr-visualizer.md              # 可視化
│
├── skills/deep-research/
│   ├── SKILL.md
│   ├── research-templates/           # リサーチタイプ別テンプレート
│   │   ├── stock-analysis.md
│   │   ├── sector-analysis.md
│   │   ├── macro-analysis.md
│   │   └── theme-analysis.md
│   └── output-templates/             # 出力形式テンプレート
│       ├── note-article.md
│       ├── analysis-report.md
│       └── investment-memo.md
│
data/
├── schemas/
│   ├── deep-research.schema.json
│   ├── cross-validation.schema.json
│   └── confidence-score.schema.json
└── config/
    └── deep-research-config.json

research/                              # 新規出力ディレクトリ
└── {research_id}/
    ├── research-meta.json
    ├── 01_data_collection/
    ├── 02_validation/
    ├── 03_analysis/
    ├── 04_synthesis/
    └── 05_output/
```

### 処理フロー

```
Phase 0: 設定確認
├── リサーチタイプ選択（stock/sector/macro/theme）
├── 深度選択（quick/standard/comprehensive）
├── 出力形式選択（article/report/memo）
└── [HF0] リサーチ方針確認

Phase 1: データ収集（並列）
├── SEC EDGAR → 10-K/10-Q/8-K/Form4
├── market_analysis → yfinance/FRED
├── Web検索 → 最新ニュース・分析
└── RSS → ニュースフィード

Phase 2: クロス検証
├── dr-cross-validator → 複数ソース照合
├── dr-confidence-scorer → 信頼度スコア算出
├── dr-bias-detector → バイアス検出
└── [HF1] 中間結果確認

Phase 3: 深掘り分析（タイプ別）
├── Stock: 財務・バリュエーション・カタリスト
├── Sector: 比較分析・ローテーション
├── Macro: 経済指標・政策影響
└── Theme: バリューチェーン・投資機会

Phase 4: 出力生成
├── dr-report-generator → 形式別レポート
├── dr-visualizer → チャート・図表
└── [HF2] 最終確認・承認
```

## リサーチタイプ別設計

### 1. 個別銘柄分析（Stock）

**データソース優先度**: SEC EDGAR > market_analysis > Web

**分析フレームワーク**:
1. 財務健全性（3-5年トレンド、収益性、キャッシュフロー）
2. バリュエーション（絶対・相対、ヒストリカルレンジ）
3. ビジネス品質（競争優位性、経営陣、資本配分）
4. カタリスト・リスク（イベント、10-Kリスク要因）

### 2. セクター分析（Sector）

**データソース優先度**: market_analysis > SEC EDGAR > Web

**分析フレームワーク**:
1. セクター概観（市場規模、主要プレイヤー）
2. 比較分析（パフォーマンス、バリュエーション）
3. ローテーション分析（モメンタム、サイクル）
4. 銘柄選定（リーダー/ラガード、バリュー機会）

### 3. マクロ経済分析（Macro）

**データソース優先度**: FRED > Web > market_analysis

**分析フレームワーク**:
1. 経済健全性（GDP、雇用、インフレ）
2. 金融政策（Fed政策、金利見通し）
3. 市場への影響（アセットクラス、セクター）
4. シナリオ分析（ベース/ブル/ベア）

### 4. テーマ投資分析（Theme）

**データソース優先度**: Web > SEC EDGAR > market_analysis

**分析フレームワーク**:
1. テーマ定義（構造的ドライバー、TAM、普及曲線）
2. バリューチェーン（受益者マッピング）
3. 投資機会（ピュアプレイ vs 分散、ETF）
4. タイミング（カタリスト、エントリーポイント）

## 深度設計

| 深度 | 目安時間 | スコープ |
|------|---------|---------|
| quick | 30分 | 単一ソース、主要指標のみ、1ページサマリー |
| standard | 1-2時間 | 複数ソース、包括的指標、5-10ページレポート |
| comprehensive | 数時間〜1日 | 全ソース網羅、5年分析、シナリオ分析、15-30ページ |

## 品質管理強化

### クロス検証スキーマ

```json
{
  "validation_id": "V001",
  "claim_id": "C001",
  "sources_checked": [
    {"source_id": "S001", "reliability_tier": "tier1", "value_found": "..."}
  ],
  "validation_result": {
    "status": "confirmed | disputed | unverifiable",
    "confidence_score": 0.85,
    "corroboration_count": 3,
    "discrepancies": [...]
  },
  "bias_analysis": {
    "detected_bias": "bullish | bearish | neutral",
    "confidence": 0.7
  }
}
```

### 信頼度スコアリング

```
confidence_score = weighted_average(
  source_reliability × 0.4,    # Tier1=1.0, Tier2=0.7, Tier3=0.4
  corroboration × 0.3,         # 複数ソース確認度
  temporal_relevance × 0.2,    # データ鮮度
  consistency × 0.1            # 内部整合性
)
```

**ソース信頼度Tier**:
- Tier1: SEC EDGAR, FRED, 公式IR
- Tier2: Bloomberg, Reuters, Yahoo Finance
- Tier3: 一般ニュース、ブログ

### バイアス検出ルール

1. センチメント不均衡（ポジティブ/ネガティブ比 > 3:1）
2. ソース集中（単一ソース > 50%）
3. 欠落視点（ブル/ベアバランス欠如）

## 出力形式

### note記事形式
- Key Takeaways + Overview + Analysis + 免責事項

### 分析レポート形式
- Executive Summary + 詳細分析 + リスク評価 + Appendix

### 投資メモ形式
- 1ページサマリー + Why Now + Key Metrics + Risks

## 既存システム連携

### 活用するコンポーネント

| 既存コンポーネント | 用途 |
|------------------|------|
| finance-market-data | 株価・指数・FRED取得 |
| finance-web | Web検索 |
| finance-sec-filings | SEC EDGAR取得（拡張） |
| finance-source | ソース構造化 |
| finance-claims | 主張抽出 |
| finance-fact-checker | ファクトチェック（拡張） |
| finance-visualize | チャート生成 |

### 記事化連携

```
/deep-research → research/{id}/05_output/
                      ↓
/finance-edit --from-research {id}
                      ↓
articles/{article_id}/ （既存フローに合流）
```

## 実装ファイル一覧

### 新規作成（必須）

| ファイル | 説明 |
|---------|------|
| `.claude/commands/deep-research.md` | メインコマンド |
| `.claude/agents/deep-research/dr-orchestrator.md` | オーケストレーター |
| `.claude/agents/deep-research/dr-stock-analyzer.md` | 個別銘柄分析 |
| `.claude/agents/deep-research/dr-sector-analyzer.md` | セクター分析 |
| `.claude/agents/deep-research/dr-macro-analyzer.md` | マクロ分析 |
| `.claude/agents/deep-research/dr-theme-analyzer.md` | テーマ分析 |
| `.claude/agents/deep-research/dr-source-aggregator.md` | ソース集約 |
| `.claude/agents/deep-research/dr-cross-validator.md` | クロス検証 |
| `.claude/agents/deep-research/dr-bias-detector.md` | バイアス検出 |
| `.claude/agents/deep-research/dr-confidence-scorer.md` | 信頼度スコア |
| `.claude/agents/deep-research/dr-report-generator.md` | レポート生成 |
| `.claude/skills/deep-research/SKILL.md` | スキル定義 |
| `data/schemas/deep-research.schema.json` | メインスキーマ |
| `data/schemas/cross-validation.schema.json` | 検証スキーマ |

### 参照ファイル（既存）

| ファイル | 参照理由 |
|---------|---------|
| `.claude/commands/finance-research.md` | コマンド構造パターン |
| `.claude/agents/finance-sec-filings.md` | SEC連携パターン |
| `.claude/agents/finance-fact-checker.md` | 検証ロジック |
| `data/schemas/fact-checks.schema.json` | スキーマパターン |

## 検証方法

1. **ユニットテスト**: 各エージェントの入出力検証
2. **統合テスト**: エンドツーエンドワークフロー実行
3. **実データテスト**: AAPL, MSFT等の実銘柄でテスト
4. **品質検証**: 生成レポートの品質スコア確認

```bash
# テスト実行例
/deep-research --type stock --ticker AAPL --depth quick
/deep-research --type sector --sector technology --depth standard
/deep-research --type macro --depth comprehensive
/deep-research --type theme --topic "AI半導体" --depth standard
```
