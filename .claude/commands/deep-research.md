---
description: 金融市場・投資テーマ専用のディープリサーチワークフローを実行します。複数ソースからデータ収集→クロス検証→深掘り分析→レポート生成までを自動化します。
argument-hint: --type <stock|sector|macro|theme> --ticker <AAPL> [--depth quick|standard|comprehensive] [--output article|report|memo]
---

金融市場・投資テーマのディープリサーチを実行します。

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| --type | ○ | - | リサーチタイプ（stock/sector/macro/theme） |
| --ticker | △ | - | ティッカーシンボル（stock分析時に必須） |
| --sector | △ | - | セクター名（sector分析時に必須） |
| --topic | △ | - | テーマ名（theme分析時に必須） |
| --depth | - | standard | 分析深度（quick/standard/comprehensive） |
| --output | - | report | 出力形式（article/report/memo） |
| --force | - | false | 強制再実行（既存データを上書き） |

## リサーチタイプ

| タイプ | 説明 | 必須パラメータ |
|--------|------|---------------|
| stock | 個別銘柄分析（財務・バリュエーション・カタリスト） | --ticker |
| sector | セクター比較分析（ローテーション・リーダー選定） | --sector |
| macro | マクロ経済分析（経済指標・金融政策・市場影響） | なし |
| theme | テーマ投資分析（バリューチェーン・投資機会） | --topic |

## 深度オプション

| 深度 | スコープ | データソース |
|------|---------|-------------|
| quick | 主要指標のみ、1ページサマリー | 単一ソース中心 |
| standard | 包括的指標、5-10ページレポート | 複数ソース |
| comprehensive | 5年分析、シナリオ分析、15-30ページ | 全ソース網羅 |

## 出力形式

| 形式 | 説明 | 用途 |
|------|------|------|
| article | note記事形式（Key Takeaways + 本文 + 免責事項） | note.com投稿 |
| report | 分析レポート形式（Executive Summary + 詳細分析） | 本格的な投資分析 |
| memo | 投資メモ形式（1ページサマリー） | 素早い意思決定 |

## 処理フロー

```
Phase 0: 設定確認
├── リサーチタイプ確認
├── パラメータバリデーション
├── 出力フォルダ作成
└── [HF0] リサーチ方針確認

Phase 1: データ収集（並列）
├── dr-source-aggregator が以下を並列実行：
│   ├── SEC EDGAR → 10-K/10-Q/8-K/Form4
│   ├── market_analysis → yfinance/FRED
│   ├── Web検索 → 最新ニュース・分析
│   └── RSS → ニュースフィード
└── raw-data.json 生成

Phase 2: クロス検証
├── dr-cross-validator → 複数ソース照合
├── dr-confidence-scorer → 信頼度スコア算出
├── dr-bias-detector → バイアス検出
├── validation-results.json 生成
└── [HF1] 中間結果確認

Phase 3: 深掘り分析（タイプ別）
├── Stock: dr-stock-analyzer
├── Sector: dr-sector-analyzer
├── Macro: dr-macro-analyzer
├── Theme: dr-theme-analyzer
└── analysis-results.json 生成

Phase 4: 出力生成
├── dr-report-generator → 形式別レポート
├── dr-visualizer → チャート・図表
├── 05_output/ にファイル生成
└── [HF2] 最終確認・承認
```

## 実行手順

### Phase 0: 設定確認

1. **リサーチID生成**
   - 形式: `DR_{type}_{YYYYMMDD}_{identifier}`
   - 例: `DR_stock_20260119_AAPL`, `DR_macro_20260119_fed-policy`

2. **出力ディレクトリ作成**
   ```
   research/{research_id}/
   ├── research-meta.json
   ├── 01_data_collection/
   ├── 02_validation/
   ├── 03_analysis/
   ├── 04_synthesis/
   └── 05_output/
   ```

3. **research-meta.json 初期化**
   ```json
   {
     "research_id": "DR_stock_20260119_AAPL",
     "type": "stock",
     "params": {
       "ticker": "AAPL",
       "depth": "standard",
       "output": "report"
     },
     "workflow": {
       "phase_0": "done",
       "phase_1": "pending",
       "phase_2": "pending",
       "phase_3": "pending",
       "phase_4": "pending"
     },
     "created_at": "2026-01-19T10:00:00Z"
   }
   ```

4. **[HF0] リサーチ方針確認**
   ```
   ディープリサーチを開始します。

   リサーチ設定:
   - タイプ: {type}
   - ターゲット: {ticker/sector/topic}
   - 深度: {depth}
   - 出力形式: {output}

   この設定でリサーチを開始しますか？ (y/n)
   ```

### Phase 1: データ収集（並列）

5. **dr-source-aggregator 実行**
   ```
   Task: dr-source-aggregator
   Input: research-meta.json
   Output: 01_data_collection/raw-data.json
   ```

   データソース優先度（タイプ別）:
   - Stock: SEC EDGAR > market_analysis > Web
   - Sector: market_analysis > SEC EDGAR > Web
   - Macro: FRED > Web > market_analysis
   - Theme: Web > SEC EDGAR > market_analysis

6. **workflow 更新**
   - phase_1 = "done"

### Phase 2: クロス検証

7. **検証エージェント並列実行**
   ```
   Task 1: dr-cross-validator
   Input: raw-data.json
   Output: 02_validation/cross-validation.json

   Task 2: dr-confidence-scorer
   Input: raw-data.json, cross-validation.json
   Output: 02_validation/confidence-scores.json

   Task 3: dr-bias-detector
   Input: raw-data.json
   Output: 02_validation/bias-analysis.json
   ```

8. **[HF1] 中間結果確認**
   ```
   データ収集・検証が完了しました。

   収集結果:
   - SEC EDGAR: {count}件
   - 市場データ: {count}件
   - Webソース: {count}件
   - RSS: {count}件

   検証結果:
   - 高信頼度データ: {count}件
   - 要確認データ: {count}件
   - バイアス検出: {bias_status}

   分析フェーズに進みますか？ (y/n)
   ```

9. **workflow 更新**
   - phase_2 = "done"

### Phase 3: 深掘り分析

10. **タイプ別分析エージェント実行**

    **Stock (--type stock)**:
    ```
    Task: dr-stock-analyzer
    Input: raw-data.json, validation-results
    Output: 03_analysis/stock-analysis.json
    分析内容:
    - 財務健全性（3-5年トレンド）
    - バリュエーション（絶対・相対）
    - ビジネス品質（競争優位性）
    - カタリスト・リスク
    ```

    **Sector (--type sector)**:
    ```
    Task: dr-sector-analyzer
    Input: raw-data.json, validation-results
    Output: 03_analysis/sector-analysis.json
    分析内容:
    - セクター概観
    - 比較分析
    - ローテーション分析
    - 銘柄選定
    ```

    **Macro (--type macro)**:
    ```
    Task: dr-macro-analyzer
    Input: raw-data.json, validation-results
    Output: 03_analysis/macro-analysis.json
    分析内容:
    - 経済健全性
    - 金融政策
    - 市場への影響
    - シナリオ分析
    ```

    **Theme (--type theme)**:
    ```
    Task: dr-theme-analyzer
    Input: raw-data.json, validation-results
    Output: 03_analysis/theme-analysis.json
    分析内容:
    - テーマ定義
    - バリューチェーン
    - 投資機会
    - タイミング
    ```

11. **workflow 更新**
    - phase_3 = "done"

### Phase 4: 出力生成

12. **レポート生成**
    ```
    Task: dr-report-generator
    Input: analysis-results, output_format
    Output: 05_output/report.md (or article.md, memo.md)
    ```

13. **可視化**
    ```
    Task: dr-visualizer
    Input: analysis-results, market-data
    Output: 05_output/charts/
    ```

14. **[HF2] 最終確認**
    ```
    リサーチが完了しました。

    生成ファイル:
    - 05_output/{output_format}.md
    - 05_output/charts/ ({count}件)

    レポートを確認しますか？ (y/n)
    ```

15. **workflow 更新**
    - phase_4 = "done"

## 完了報告

```markdown
## ディープリサーチ完了

### リサーチ情報
- **リサーチID**: {research_id}
- **タイプ**: {type}
- **ターゲット**: {ticker/sector/topic}
- **深度**: {depth}

### 収集・検証結果
- データソース: {source_count}件
- 高信頼度データ: {high_confidence_count}件
- 検証済み主張: {verified_claims_count}件

### 分析サマリー
{analysis_summary}

### 生成ファイル
- `research/{research_id}/05_output/{output}.md`
- `research/{research_id}/05_output/charts/`

### 次のステップ

**note記事化**: `/finance-edit --from-research {research_id}`
```

## エラーハンドリング

### 必須パラメータ不足

```
エラー: 必須パラメータが不足しています

タイプ: {type}
必要なパラメータ: {required_param}

対処法:
/deep-research --type {type} --{required_param} <value>
```

### データ取得失敗

```
警告: 一部のデータソースから取得できませんでした

失敗したソース:
- {source}: {error_message}

利用可能なデータで続行しますか？ (y/n)
```

### 信頼度不足

```
警告: 高信頼度データが不足しています

現在の信頼度分布:
- 高: {high_count}件
- 中: {medium_count}件
- 低: {low_count}件

追加データ収集を行いますか？ (y/n)
```

## 使用例

### 個別銘柄分析

```bash
/deep-research --type stock --ticker AAPL --depth standard --output report
```

### セクター分析

```bash
/deep-research --type sector --sector technology --depth comprehensive --output article
```

### マクロ経済分析

```bash
/deep-research --type macro --depth standard --output memo
```

### テーマ投資分析

```bash
/deep-research --type theme --topic "AI半導体" --depth comprehensive --output article
```

## 関連コマンド・エージェント

- **次のコマンド**: `/finance-edit --from-research {research_id}`
- **使用エージェント**:
  - dr-orchestrator（ワークフロー制御）
  - dr-source-aggregator（ソース集約）
  - dr-cross-validator（クロス検証）
  - dr-confidence-scorer（信頼度スコア）
  - dr-bias-detector（バイアス検出）
  - dr-stock-analyzer / dr-sector-analyzer / dr-macro-analyzer / dr-theme-analyzer
  - dr-report-generator（レポート生成）
  - dr-visualizer（可視化）

## スキーマ参照

- `data/schemas/deep-research.schema.json`
- `data/schemas/cross-validation.schema.json`
- `data/schemas/confidence-score.schema.json`
