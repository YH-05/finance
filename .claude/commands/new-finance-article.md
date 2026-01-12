---
description: 新規金融記事フォルダを作成し、カテゴリ別テンプレートから初期構造を生成します。
argument-hint: [トピック名]
---

新規金融記事フォルダを作成し、執筆ワークフローの準備をします。

## 入力パラメータの解析

ユーザーが指定したパラメータを確認します：

- **トピック名** (必須): 記事のテーマ（例: `2025年1月第2週 米国市場週間レビュー`, `テスラ決算分析`, `米雇用統計解説`）

トピック名が指定されていない場合は、ユーザーに確認してください。

## 処理フロー

### Phase 1: 記事情報の収集

1. **トピック名の確認**

   引数からトピック名を取得。指定がない場合はユーザーに質問します。

   ```
   記事のトピックを教えてください（例: 2025年1月第2週 米国市場週間レビュー）:
   ```

2. **カテゴリの選択**

   以下のカテゴリから選択してもらいます：

   - `market_report`: 市場レポート・相場解説
   - `stock_analysis`: 個別銘柄・企業分析
   - `economic_indicators`: 経済指標・マクロ分析
   - `investment_education`: 投資教育・基礎知識
   - `quant_analysis`: クオンツ分析・戦略検証

   ユーザーに質問：

   ```
   カテゴリを選択してください:
   1. market_report (市場レポート・相場解説)
   2. stock_analysis (個別銘柄・企業分析)
   3. economic_indicators (経済指標・マクロ分析)
   4. investment_education (投資教育・基礎知識)
   5. quant_analysis (クオンツ分析・戦略検証)
   ```

3. **英語テーマ名の生成**

   トピック名から英語のテーマ名を生成します：

   - ケバブケース（小文字、ハイフン区切り）
   - 特殊文字を除去
   - 例: `2025年1月第2週 米国市場週間レビュー` → `us-market-weekly-2025w02`
   - 例: `テスラ決算分析` → `tsla-earnings-analysis`
   - 例: `米雇用統計解説` → `us-employment-report`

   生成した英語名をユーザーに確認：

   ```
   英語テーマ名: {theme_name_en}
   この名前でよろしいですか？ (y/n または修正案を入力)
   ```

4. **シンボル・指標の入力（カテゴリ別）**

   market_report, stock_analysis, quant_analysis の場合：
   ```
   対象シンボルを入力してください（カンマ区切り）
   例: AAPL,^GSPC,USDJPY=X
   ```

   economic_indicators の場合：
   ```
   対象FRED指標を入力してください（カンマ区切り）
   例: GDP,CPIAUCSL,FEDFUNDS
   ```

5. **分析期間の入力（該当カテゴリのみ）**

   market_report, stock_analysis, economic_indicators, quant_analysis の場合：
   ```
   分析期間を入力してください
   開始日 (YYYY-MM-DD):
   終了日 (YYYY-MM-DD):
   ```

### Phase 2: article_id の生成と重複確認

6. **既存記事の確認**

   `articles/` ディレクトリ内の既存記事を確認し、同じカテゴリの最大通番を取得します。

   ```bash
   ls -d articles/{category}_* 2>/dev/null | grep -o '{category}_[0-9]*' | cut -d'_' -f2 | sort -n | tail -1
   ```

   通番は既存の最大値 + 1、または存在しない場合は 001 から開始します。

7. **article_id の生成**

   形式: `{category}_{seq:03d}_{theme_name_en}`

   例:

   - `market_report_001_us-market-weekly-2025w02`
   - `stock_analysis_002_tsla-earnings-analysis`
   - `economic_indicators_001_us-employment-report`

8. **重複チェック**

   `articles/{article_id}/` が既に存在しないことを確認します。
   存在する場合はエラーを表示し、処理を中断します。

### Phase 3: フォルダ構造の作成

9. **ディレクトリ作成**

   ```bash
   mkdir -p articles/{article_id}
   ```

10. **テンプレートのコピー**

    `template/{category}/` から `articles/{article_id}/` へ全ファイルをコピーします。

    ```bash
    cp -r template/{category}/* articles/{article_id}/
    ```

### Phase 4: メタデータの初期化

11. **article-meta.json の更新**

    `articles/{article_id}/article-meta.json` を以下の内容で更新します：

    ```json
    {
        "article_id": "{article_id}",
        "topic": "{トピック名}",
        "category": "{category}",
        "symbols": ["{入力されたシンボル}"],
        "fred_series": ["{入力されたFRED指標}"],
        "date_range": {
            "start": "{開始日}",
            "end": "{終了日}"
        },
        "target_audience": "{カテゴリに応じたデフォルト}",
        "tags": [],
        "status": "research",
        "created_at": "{YYYY-MM-DD}",
        "updated_at": "{YYYY-MM-DD}",
        "human_feedback": {
            "hf1_topic_approved": true,
            "hf3_claims_reviewed": false,
            "hf5_draft_reviewed": false,
            "hf6_final_approved": false
        },
        "workflow": { ... }
    }
    ```

12. **空ファイルの article_id 更新**

    以下のファイルの `article_id` フィールドを更新：

    - `01_research/queries.json`
    - `01_research/raw-data.json`
    - `01_research/sources.json`
    - `01_research/claims.json`
    - `01_research/analysis.json`
    - `01_research/decisions.json`
    - `01_research/fact-checks.json`

### Phase 5: 完了報告

13. **成功メッセージの表示**

    ```markdown
    ## 新規金融記事フォルダを作成しました

    ### 記事情報

    - **記事 ID**: {article_id}
    - **トピック**: {トピック名}
    - **カテゴリ**: {category_label}
    - **対象シンボル**: {symbols}
    - **分析期間**: {start_date} 〜 {end_date}
    - **作成日**: {YYYY-MM-DD}
    - **フォルダ**: `articles/{article_id}/`

    ### 作成されたファイル

    - メタデータ: `article-meta.json`
    - リサーチ: `01_research/` (7 ファイル + market_data/ + visualize/)
    - 執筆: `02_edit/` (4 ファイル)
    - 公開: `03_published/` (1 テンプレート)

    ### 次のステップ

    1. **リサーチ開始**: `/finance-research --article {article_id}`
    2. **執筆開始**: `/finance-edit {article_id}` (リサーチ完了後)

    ### フィードバックポイント

    このワークフローには以下のフィードバックポイントがあります：
    - [HF1] トピック承認 ✓ 完了
    - [HF3] 主張採用確認（リサーチ後）
    - [HF5] 初稿レビュー（執筆後）
    - [HF6] 最終確認（公開前）
    ```

## エラーハンドリング

### articles/ ディレクトリが存在しない場合

```bash
mkdir -p articles/
```

自動的に作成してから処理を続行します。

### 重複する article_id が存在する場合

```
エラー: 記事フォルダが既に存在します

既存フォルダ: articles/{article_id}/

対処法:
- 別の英語テーマ名を使用してください
- または既存フォルダを削除してから再実行してください
```

### テンプレートフォルダが存在しない場合

```
エラー: テンプレートフォルダが見つかりません

必要なパス: template/{category}/

対処法:
- テンプレートが正しく配置されているか確認してください
```

## カテゴリ別デフォルト設定

| カテゴリ | target_audience | 主な入力項目 |
|---------|-----------------|-------------|
| market_report | intermediate | symbols, date_range |
| stock_analysis | intermediate | symbols, date_range |
| economic_indicators | intermediate | fred_series, date_range |
| investment_education | beginner | topics |
| quant_analysis | advanced | symbols, date_range, backtest_config |

## 関連コマンド・エージェント

- **関連コマンド**: `/finance-research`, `/finance-edit`, `/finance-suggest-topics`
- **関連エージェント**: finance-query-generator, finance-market-data, finance-article-writer
