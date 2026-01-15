---
description: 記事作成の全工程を一括実行する統合コマンド。フォルダ作成→リサーチ→執筆の全ステップを自動化します。
argument-hint: [トピック名] [--category <category>] [--depth <depth>] [--mode <mode>] [--skip-hf]
---

記事作成の全工程を一括実行する統合コマンドです。

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| トピック名 | ○ | - | 記事のテーマ（例: 2025年1月第2週 米国市場週間レビュー） |
| --category | - | 対話で選択 | カテゴリ（market_report, stock_analysis, etc.） |
| --depth | - | auto | リサーチ深度（auto/shallow/deep） |
| --mode | - | quick | 編集モード（quick/full） |
| --skip-hf | - | false | ヒューマンフィードバックをスキップ（非推奨） |

## 処理フロー

```
Phase 1: 記事フォルダ作成
├── /new-finance-article
│   ├── トピック名入力
│   ├── カテゴリ選択
│   ├── シンボル/指標入力
│   └── article_id 生成
└── [HF1] トピック承認 ✓

Phase 2: リサーチ実行
├── /finance-research
│   ├── クエリ生成
│   ├── データ収集（並列）
│   │   ├── finance-market-data
│   │   ├── finance-web
│   │   ├── finance-wiki
│   │   └── finance-sec-filings
│   ├── データ処理
│   ├── センチメント分析
│   └── 分析・検証
└── [HF3] 主張採用確認

Phase 3: 記事執筆
├── /finance-edit
│   ├── 初稿作成
│   ├── [HF5] 初稿レビュー
│   ├── 批評（並列）
│   └── 修正
└── [HF6] 最終確認
```

## 実行手順

### Phase 1: 記事フォルダ作成

1. **パラメータの解析**

   引数からトピック名と各オプションを取得します。

2. **記事フォルダ作成**

   `/new-finance-article` コマンドの全機能を実行：

   - トピック名が指定されていない場合は質問
   - --category が指定されていない場合はユーザーに選択させる
   - 英語テーマ名の生成と確認
   - シンボル・指標の入力（カテゴリ別）
   - 分析期間の入力
   - article_id の生成
   - フォルダ構造とメタデータの作成

3. **[HF1] トピック承認**

   ```
   記事フォルダを作成しました。

   - 記事ID: {article_id}
   - トピック: {topic}
   - カテゴリ: {category}

   このトピックで続行しますか？ (y/n)
   ```

   --skip-hf が指定されている場合はスキップ。

### Phase 2: リサーチ実行

4. **リサーチワークフロー開始**

   `/finance-research --article {article_id} --depth {depth}` を実行：

   - Phase 1: クエリ生成
   - Phase 2: データ収集（並列）
     - finance-market-data
     - finance-web
     - finance-wiki
     - finance-sec-filings
   - Phase 3: データ処理
     - finance-source
     - finance-claims
   - Phase 3.5: センチメント分析
     - finance-sentiment-analyzer
   - Phase 4: 分析・検証
     - finance-claims-analyzer
     - finance-fact-checker
     - finance-decisions
   - Phase 5: 可視化
     - finance-visualize

5. **リサーチ結果の確認**

   ```
   リサーチが完了しました。

   収集結果:
   - 市場データ: {count}件
   - Webソース: {count}件
   - SEC開示情報: {count}件
   - センチメントスコア: {score}

   分析結果:
   - 抽出した主張: {claims_count}件
   - 採用判定:
     - 採用: {accept_count}件
     - 不採用: {reject_count}件
     - 保留: {hold_count}件
   ```

6. **[HF3] 主張採用確認**

   --skip-hf が指定されていない場合、decisions.json の内容を確認：

   ```
   採用された主張を確認しますか？ (y/n)

   確認する場合:
   - decisions.json を表示
   - 修正が必要な場合は編集を促す
   - 準備ができたら「続行」と入力

   確認をスキップする場合:
   - そのまま執筆フェーズに進む
   ```

### Phase 3: 記事執筆

7. **執筆ワークフロー開始**

   `/finance-edit --article {article_id} --mode {mode}` を実行：

   - Step 1: 初稿作成
     - finance-article-writer
   - Step 2: 批評（並列）
     - quick モード: fact, compliance
     - full モード: fact, compliance, structure, data, readability
   - Step 3: 修正
     - finance-reviser

8. **[HF5] 初稿レビュー（quick モード時は省略可能）**

   --skip-hf が指定されていない場合、初稿を確認：

   ```
   初稿が完成しました。

   - 文字数: {word_count}字
   - セクション数: {section_count}
   - 使用した主張: {claims_used}件

   初稿を確認しますか？ (y/n)

   確認する場合:
   - first_draft.md を表示
   - 修正が必要な場合は編集を促す
   - 準備ができたら「続行」と入力
   ```

9. **批評と修正の実行**

   批評エージェントを並列実行し、修正版を生成します。

10. **[HF6] 最終確認**

    --skip-hf が指定されていない場合、最終確認：

    ```
    記事の執筆が完了しました。

    最終スコア:
    | 項目 | スコア |
    |------|--------|
    | 総合 | {overall}/100 |
    | コンプライアンス | {compliance}/100 |
    | 事実正確性 | {fact}/100 |

    修正版を確認しますか？ (y/n)

    確認後:
    - 承認: 「承認」と入力 → status = "ready_for_publish"
    - 追加修正: 「修正」と入力 → 編集プロセスに戻る
    ```

## 完了報告

```markdown
## 記事作成完了

### 記事情報
- **記事ID**: {article_id}
- **トピック**: {topic}
- **カテゴリ**: {category_label}

### 実行時間
- リサーチ: {research_time}
- 執筆: {writing_time}
- 合計: {total_time}

### 生成ファイル

**01_research/** (リサーチ成果物)
- queries.json
- raw-data.json
- market_data/data.json
- sources.json
- claims.json
- sentiment_analysis.json
- analysis.json
- fact-checks.json
- decisions.json
- visualize/

**02_edit/** (執筆成果物)
- first_draft.md
- critic.json
- critic.md
- revised_draft.md

### 最終スコア
| 項目 | スコア |
|------|--------|
| 総合 | {overall}/100 |
| コンプライアンス | {compliance}/100 |
| 事実正確性 | {fact}/100 |
| 構成 | {structure}/100 ({mode}モード時) |
| データ正確性 | {data}/100 ({mode}モード時) |
| 読みやすさ | {readability}/100 ({mode}モード時) |

### 次のステップ

1. **最終確認**
   ```bash
   cat articles/{article_id}/02_edit/revised_draft.md
   ```

2. **公開準備**
   ```bash
   cp articles/{article_id}/02_edit/revised_draft.md \
      articles/{article_id}/03_published/article.md
   ```

3. **note.com に公開**
   - revised_draft.md の内容をコピー
   - note.com で記事を作成
   - 画像やチャートをアップロード
   - 公開後、article-meta.json の status を "published" に更新

### ワークフロー状態

**article-meta.json の human_feedback:**
- [HF1] トピック承認: ✓
- [HF3] 主張採用確認: {hf3_status}
- [HF5] 初稿レビュー: {hf5_status}
- [HF6] 最終確認: {hf6_status}

**status:** {current_status}
```

## エラーハンドリング

### articles/ ディレクトリが存在しない

自動的に作成します：
```bash
mkdir -p articles/
```

### リサーチ失敗時

```
エラー: リサーチ中に問題が発生しました

失敗した処理: {failed_step}
エラー内容: {error_message}

対処法:
1. エラー内容を確認
2. 必要に応じて article-meta.json を編集
3. リサーチから再実行:
   /finance-research --article {article_id} --force
```

### 執筆失敗時

```
エラー: 執筆中に問題が発生しました

失敗した処理: {failed_step}
エラー内容: {error_message}

対処法:
1. リサーチ結果（decisions.json）を確認
2. 必要に応じて修正
3. 執筆から再実行:
   /finance-edit --article {article_id}
```

### コンプライアンス fail

```
⚠️ コンプライアンスチェック失敗

この記事には修正が必須の問題が含まれています。

問題:
1. {critical_issue_1}
2. {critical_issue_2}

対処法:
1. first_draft.md または revised_draft.md を手動修正
2. 再度執筆を実行:
   /finance-edit --article {article_id}
```

## オプション詳細

### --depth (リサーチ深度)

| 深度 | 説明 | 用途 |
|------|------|------|
| shallow | 基本情報のみ。クエリ数を制限。 | 速報記事、簡単な解説 |
| auto | claims-analyzer の判定で自動調整。 | 一般的な記事（推奨） |
| deep | 詳細調査。追加クエリ生成、複数回検証。 | 詳細分析、長文記事 |

### --mode (編集モード)

| モード | 批評エージェント | 用途 |
|--------|-----------------|------|
| quick | fact, compliance | 速報記事、簡潔な記事 |
| full | fact, compliance, structure, data, readability | 詳細記事、高品質記事 |

### --skip-hf (ヒューマンフィードバックスキップ)

**非推奨**: このオプションを使用すると、全てのヒューマンフィードバックポイントがスキップされます。

- [HF1] トピック承認 → 自動承認
- [HF3] 主張採用確認 → スキップ
- [HF5] 初稿レビュー → スキップ
- [HF6] 最終確認 → 自動承認

**使用ケース**:
- 完全自動化テスト
- 既にテンプレート化された記事
- 緊急時の速報記事

**注意**: 品質保証のため、通常は --skip-hf を使用せず、各フィードバックポイントで確認することを推奨します。

## 使用例

### 基本的な使用（推奨）

```bash
# カテゴリを対話で選択
/finance-full "2025年1月第2週 米国市場週間レビュー"

# カテゴリを指定
/finance-full "テスラ決算分析" --category stock_analysis

# 詳細モード
/finance-full "米雇用統計解説" --category economic_indicators --depth deep --mode full
```

### オプション付き

```bash
# 速報記事（浅いリサーチ、クイック編集）
/finance-full "速報: FOMC利上げ決定" --depth shallow --mode quick

# 詳細記事（深いリサーチ、フル編集）
/finance-full "2025年投資戦略ガイド" --category investment_education --depth deep --mode full

# 完全自動化（非推奨）
/finance-full "市場アップデート" --skip-hf
```

## カテゴリ別推奨設定

| カテゴリ | 推奨 depth | 推奨 mode | 理由 |
|---------|-----------|-----------|------|
| market_report | auto | quick | 定期的な市場レポート、速報性重視 |
| stock_analysis | deep | full | 詳細な企業分析、品質重視 |
| economic_indicators | deep | full | マクロ経済分析、正確性重視 |
| investment_education | deep | full | 教育コンテンツ、読みやすさ重視 |
| quant_analysis | deep | full | 数値分析、データ正確性重視 |

## 関連コマンド

- **構成コマンド**:
  - `/new-finance-article` - Phase 1 のみ実行
  - `/finance-research` - Phase 2 のみ実行
  - `/finance-edit` - Phase 3 のみ実行

- **補助コマンド**:
  - `/finance-suggest-topics` - トピック提案

- **関連エージェント** (全16エージェント):
  - データ収集: finance-query-generator, finance-market-data, finance-web, finance-wiki, finance-sec-filings
  - データ処理: finance-source, finance-claims
  - 分析: finance-claims-analyzer, finance-fact-checker, finance-decisions, finance-technical-analysis, finance-economic-analysis, finance-sentiment-analyzer
  - 執筆: finance-article-writer, finance-visualize
  - 批評・修正: finance-critic-*, finance-reviser

## 注意事項

1. **初回実行時**
   - トピック名、カテゴリ、シンボル、期間などの入力が必要
   - 対話的に進むため、時間がかかる場合があります

2. **実行時間**
   - shallow + quick: 約5-10分
   - auto + quick: 約10-20分
   - deep + full: 約20-40分

3. **データ品質**
   - --skip-hf を使用しない場合、各フェーズで確認・修正可能
   - 品質を重視する場合は --skip-hf を使用しない

4. **再実行**
   - エラー時は個別コマンドで該当フェーズから再開可能
   - article_id を指定して部分的に実行できます

## トラブルシューティング

### 「記事フォルダが既に存在します」

```
エラー: 記事フォルダが既に存在します

対処法:
1. 既存フォルダを削除:
   rm -rf articles/{article_id}/

2. または別の英語テーマ名を使用:
   /finance-full "トピック名" --category {category}
```

### 「市場データの取得に失敗しました」

```
エラー: 市場データの取得に失敗しました

対処法:
1. シンボルが正しいか確認
2. ネットワーク接続を確認
3. リサーチから再実行:
   /finance-research --article {article_id} --force
```

### 「批評エージェントが失敗しました」

```
警告: 一部の批評エージェントが失敗しました

対処法:
- 必須エージェント（fact, compliance）が成功していれば続行
- 失敗した批評は critic.json に含まれません
- 必要に応じて手動で確認・修正
```
