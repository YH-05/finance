---
description: 金融記事のトピックを提案します。カテゴリ、時事性、読者関心度等を考慮してスコアリングされた提案リストを表示します。
argument-hint: [カテゴリ] [--count N]
---

金融記事のトピックを提案します。

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| カテゴリ | - | 全カテゴリ | 特定カテゴリに限定（market_report, stock_analysis等）|
| --count | - | 5 | 提案数 |

## 処理フロー

### Phase 1: 既存記事の確認

1. **articles/ フォルダスキャン**
   ```bash
   ls -d articles/*/ 2>/dev/null
   ```

2. **各記事のメタデータ読み込み**
   - article-meta.json から topic, category, created_at を取得

3. **カテゴリ分布の集計**
   ```
   market_report: 3
   stock_analysis: 4
   economic_indicators: 2
   investment_education: 1
   quant_analysis: 0
   ```

### Phase 2: トピック提案の生成

4. **finance-topic-suggester 実行**
   ```
   Task: finance-topic-suggester
   Input: existing_articles, category (optional), count
   Output: suggestions (JSON)
   ```

### Phase 3: 結果の整形と表示

5. **提案リストの表示**

   ```markdown
   ## トピック提案

   ### 既存記事
   - 総数: 10件
   - market_report: 3件
   - stock_analysis: 4件
   - economic_indicators: 2件
   - investment_education: 1件
   - quant_analysis: 0件

   ---

   ### 提案トピック

   #### 1. 2025年1月第2週 米国市場週間レビュー
   - **カテゴリ**: market_report
   - **スコア**: 41/50
   - **対象**: ^GSPC, ^IXIC, ^DJI, USDJPY=X
   - **期間**: 2025-01-06 〜 2025-01-10
   - **想定文字数**: 4000字
   - **ターゲット**: intermediate

   **提案理由**:
   FOMCを控えた重要な週。米国株は週間で+2%の上昇、
   雇用統計の発表もあり、市場参加者の関心が高い。

   **キーポイント**:
   - S&P 500 の週間パフォーマンス
   - 雇用統計の影響
   - 来週のFOMCへの注目点

   ---

   #### 2. NVIDIA (NVDA) 決算分析
   - **カテゴリ**: stock_analysis
   - **スコア**: 39/50
   ...

   ---

   ### カテゴリバランス分析

   現在、quant_analysis の記事がありません。
   バランスを考慮すると、クオンツ分析記事の作成を推奨します。

   ---

   ### 次のアクション

   トピックを選択して記事を作成:
   /new-finance-article "2025年1月第2週 米国市場週間レビュー"
   ```

## 出力フォーマット

### テーブル形式（簡易）

```markdown
| 順位 | トピック | カテゴリ | スコア |
|------|---------|---------|--------|
| 1 | 2025年1月第2週 米国市場週間レビュー | market_report | 41/50 |
| 2 | NVIDIA決算分析 | stock_analysis | 39/50 |
| 3 | 米雇用統計解説 | economic_indicators | 38/50 |
| 4 | ETF入門 | investment_education | 35/50 |
| 5 | モメンタム戦略検証 | quant_analysis | 34/50 |
```

### 詳細形式（デフォルト）

各提案について:
- トピック名
- カテゴリ
- スコア（内訳付き）
- 対象シンボル/指標
- 分析期間
- 提案理由
- キーポイント
- ターゲット読者
- 想定文字数

## スコア評価基準

| 基準 | 高スコア（8-10） | 中スコア（5-7） | 低スコア（1-4） |
|------|-----------------|----------------|----------------|
| timeliness | 今週のイベント、直近の発表 | 今月のイベント | 時事性なし |
| information | データ豊富、複数ソース | 十分なデータ | データ不足 |
| reader_interest | SNS話題、検索需要高 | 一定の関心 | ニッチ |
| feasibility | 3000-5000字で完結 | 調整必要 | 大幅調整必要 |
| uniqueness | 独自視点あり | 標準的 | 類似記事多数 |

## 関連コマンド

- **次のステップ**: `/new-finance-article "選択したトピック"`
- **リサーチ開始**: `/finance-research --article {article_id}`
