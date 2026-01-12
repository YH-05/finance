---
description: 金融記事の編集ワークフローを実行します。初稿作成→批評→修正の一連の処理を自動化します。
argument-hint: --article <article_id> [--mode quick|full]
---

金融記事の編集ワークフローを実行します。

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| --article | ○ | - | 記事ID |
| --mode | - | full | 編集モード（quick/full） |
| --skip-draft | - | false | 初稿作成をスキップ（既存の場合） |

## 編集モード

| モード | 実行する批評エージェント |
|--------|------------------------|
| quick | fact, compliance |
| full | fact, structure, compliance, data_accuracy, readability |

## 処理フロー

```
Step 1: 初稿作成
├── finance-article-writer → first_draft.md
└── [HF5] 初稿レビュー（推奨）

Step 2: 批評（並列）
├── finance-critic-fact（必須）
├── finance-critic-compliance（必須）
├── finance-critic-structure（full時）
├── finance-critic-data（full時）
├── finance-critic-readability（full時）
└── → critic.json, critic.md

Step 3: 修正
├── finance-reviser → revised_draft.md
└── [HF6] 最終確認（必須）
```

## 実行手順

### Step 1: 初稿作成

1. **リサーチ完了確認**
   ```
   article-meta.json の workflow を確認:
   - research.decisions = "done" であること
   ```

2. **finance-article-writer 実行**
   ```
   Task: finance-article-writer
   Input: decisions.json, sources.json, claims.json, article-meta.json
   Output: 02_edit/first_draft.md
   ```

3. **[HF5] 初稿レビュー（推奨）**
   ```
   初稿が完成しました。

   ## 初稿サマリー

   - **文字数**: {word_count}字
   - **セクション数**: {section_count}
   - **使用した主張**: {claims_used}件

   初稿を確認しますか？ (y/n)

   確認後、修正が必要な場合は first_draft.md を直接編集してください。
   準備ができたら「続行」と入力してください。
   ```

4. **workflow 更新**
   - writing.first_draft = "done"
   - human_feedback.hf5_draft_reviewed = true

### Step 2: 批評（並列）

5. **批評エージェントの並列実行**

   **quick モード**:
   ```
   Task 1: finance-critic-fact
   Task 2: finance-critic-compliance
   ```

   **full モード**:
   ```
   Task 1: finance-critic-fact
   Task 2: finance-critic-compliance
   Task 3: finance-critic-structure
   Task 4: finance-critic-data
   Task 5: finance-critic-readability
   ```

6. **批評結果の統合**
   ```
   critic.json:
   {
     "article_id": "...",
     "generated_at": "...",
     "critics": {
       "fact": { ... },
       "compliance": { ... },
       "structure": { ... },
       "data_accuracy": { ... },
       "readability": { ... }
     },
     "overall_score": 82,
     "priority_fixes": [ ... ]
   }
   ```

7. **critic.md 生成**（人間可読形式）
   ```markdown
   # 批評レポート

   ## 総合スコア: 82/100

   ## コンプライアンス: 90/100
   - ステータス: pass
   - 問題点: 2件

   ## 事実正確性: 85/100
   - 検証済み: 45件
   - 問題点: 3件

   ...

   ## 優先修正事項
   1. [HIGH] 免責事項の追加が必要
   2. [MEDIUM] 株価データの修正
   ```

8. **コンプライアンスチェック**
   ```
   compliance.status が "fail" の場合:

   ⚠️ コンプライアンス問題が検出されました。

   critical な問題:
   - {問題1}
   - {問題2}

   これらの問題は修正が必須です。
   続行しますか？ (y/n)
   ```

9. **workflow 更新**
   - writing.critics = "done"

### Step 3: 修正

10. **finance-reviser 実行**
    ```
    Task: finance-reviser
    Input: first_draft.md, critic.json, sources.json
    Output: 02_edit/revised_draft.md
    ```

11. **[HF6] 最終確認（必須）**
    ```
    修正版が完成しました。

    ## 修正サマリー

    - **総修正箇所**: {count}件
    - **compliance 修正**: {count}件
    - **fact 修正**: {count}件
    - **最終スコア**: {score}/100

    ## 修正前後の比較

    | 項目 | 修正前 | 修正後 |
    |------|--------|--------|
    | compliance | 70 | 95 |
    | fact | 80 | 95 |
    | overall | 75 | 90 |

    revised_draft.md を確認してください。

    公開準備ができたら「承認」と入力してください。
    追加修正が必要な場合は「修正」と入力してください。
    ```

12. **workflow 更新**
    - writing.revised_draft = "done"
    - human_feedback.hf6_final_approved = true
    - status = "ready_for_publish"

## 完了報告

```markdown
## 編集完了

### 記事情報
- **記事ID**: {article_id}
- **トピック**: {topic}

### 最終スコア
| 項目 | スコア |
|------|--------|
| 総合 | {overall}/100 |
| コンプライアンス | {compliance}/100 |
| 事実正確性 | {fact}/100 |
| 構成 | {structure}/100 |
| データ正確性 | {data}/100 |
| 読みやすさ | {readability}/100 |

### 生成ファイル
- `02_edit/first_draft.md` - 初稿
- `02_edit/critic.json` - 批評（JSON）
- `02_edit/critic.md` - 批評（人間可読）
- `02_edit/revised_draft.md` - 修正版

### 次のステップ

1. revised_draft.md を最終確認
2. 問題なければ 03_published/ に移動
3. note.com に公開
```

## エラーハンドリング

### リサーチ未完了

```
エラー: リサーチが完了していません

必要な完了状態:
- research.decisions = "done"

対処法:
- /finance-research --article {article_id} を先に実行してください
```

### 批評エージェントの部分失敗

一部のエージェントが失敗しても、必須エージェント（fact, compliance）が成功していれば続行します。

```
警告: 一部の批評エージェントが失敗しました

失敗:
- finance-critic-readability

成功した批評で続行します。
失敗した批評は critic.json に含まれません。
```

### コンプライアンス fail

```
⚠️ コンプライアンスチェック失敗

この記事には修正が必須の問題が含まれています。

問題:
1. {critical_issue_1}
2. {critical_issue_2}

修正後、再度 /finance-edit を実行してください。
```

## 関連コマンド・エージェント

- **前提コマンド**: `/finance-research`
- **使用エージェント**: finance-article-writer, finance-critic-*, finance-reviser
