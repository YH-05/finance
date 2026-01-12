---
description: edit フェーズ全体を実行します。初稿作成→批評→修正の一連のワークフローを自動実行します。
argument-hint: <article_id> [--mode <full|quick>]
---

edit フェーズ全体を実行します。

## パラメータ

- **article_id** (必須): 記事ID（例: unsolved_001_db-cooper）
- **--mode** (任意): 実行モード（デフォルト: full）
  - `full`: 全ての批評家エージェントを実行
  - `quick`: 主要な批評のみ実行（fact, structure）

## パラメータ検証

| 条件 | エラー |
|------|--------|
| article_id 未指定 | E001: 必須パラメータ article_id が不足 |
| --mode が full/quick 以外 | E001: 無効な値（有効: full, quick） |
| 記事フォルダが存在しない | E002: 記事フォルダが見つかりません |

## 処理フロー概要

```
/edit <article_id>
    ↓
[Step 1] edit-article-writer を実行
    └─ first_draft.md（既存なら自動スキップ）
    ↓
[Step 2] edit-critic-* を並列実行
    ├─ edit-critic-fact
    ├─ edit-critic-structure
    ├─ edit-critic-entertainment（full モードのみ）
    └─ edit-critic-depth（full モードのみ）
            ↓
    critic.json + critic.md（両方生成）
    ↓
[Step 3] edit-reviser を実行
        ↓
    revised_draft.md
```

## 管理対象エージェント

以下の6個のエージェントを適切なタイミングで実行します：

- edit-article-writer
- edit-critic-fact
- edit-critic-structure
- edit-critic-entertainment
- edit-critic-depth
- edit-reviser

## モード説明

| モード | 批評家エージェント                                 | 説明             |
| ------ | -------------------------------------------------- | ---------------- |
| full   | fact, structure, entertainment, depth（全 4 種）   | フル批評         |
| quick  | fact, structure のみ                               | 必須批評のみ     |

## 入力ファイル（前提条件）

| ファイル         | パス                                 | 必須 | 生成元              |
| ---------------- | ------------------------------------ | ---- | ------------------- |
| sources.json     | articles/{article_id}/01_research/   | ✅   | research-source     |
| claims.json      | articles/{article_id}/01_research/   | ✅   | research-claims     |
| decisions.json   | articles/{article_id}/01_research/   | ✅   | research-decisions  |
| fact-checks.json | articles/{article_id}/01_research/   | ✅   | research-fact-checker |

## Step 1: edit-article-writer の実行

```javascript
const firstDraftPath = `articles/${articleId}/02_edit/first_draft.md`;

if (await fileExists(firstDraftPath)) {
    console.log("✅ first_draft.md が既に存在するためスキップ");
} else {
    console.log("📝 edit-article-writer を実行中...");
    await runSubAgent("edit-article-writer", {
        article_id: articleId
    });
}
```

**スキップ条件**:
- first_draft.md が既に存在する場合、edit-article-writer の実行をスキップ
- 強制的に再生成したい場合は、手動で first_draft.md を削除してから実行

## Step 2: 批評家エージェントの並列実行

```javascript
const criticAgents = mode === "quick"
    ? [
        { name: "edit-critic-fact", priority: "high", required: true },
        { name: "edit-critic-structure", priority: "high", required: true },
    ]
    : [
        { name: "edit-critic-fact", priority: "high", required: true },
        { name: "edit-critic-structure", priority: "high", required: true },
        { name: "edit-critic-entertainment", priority: "medium", required: false },
        { name: "edit-critic-depth", priority: "medium", required: false },
    ];

const results = await Promise.allSettled(
    criticAgents.map((agent) =>
        runSubAgent(agent.name, {
            article_id: articleId,
            draft_file: "02_edit/first_draft.md",
        })
    )
);
```

### 批評結果の統合

批評結果は2つの形式で出力:

1. **critic.json**（機械処理用）: edit-reviser が参照
2. **critic.md**（人間可読用）: レビュー用ドキュメント

#### critic.json 構造

```json
{
    "article_id": "unsolved_001_db-cooper",
    "review_date": "2026-01-07T12:00:00+09:00",
    "critics": [
        {
            "critic_type": "fact",
            "status": "success",
            "issues": [
                {
                    "issue_id": "I001",
                    "severity": "high",
                    "description": "問題の説明",
                    "location": "セクション名",
                    "suggestion": "改善提案"
                }
            ]
        }
    ],
    "summary": {
        "grade": "B",
        "key_improvements": ["改善点1", "改善点2"],
        "strengths": ["強み1", "強み2"]
    },
    "priorities": [
        {
            "priority": 1,
            "title": "対応項目タイトル",
            "severity": "high",
            "description": "詳細説明",
            "suggestion": "具体的な改善提案",
            "related_issues": ["I001", "I002"]
        }
    ],
    "statistics": {
        "total_issues": 10,
        "by_severity": { "high": 2, "medium": 5, "low": 3 },
        "by_critic": { "fact": 3, "structure": 4, "entertainment": 2, "depth": 1 }
    }
}
```

#### critic.md 構成

1. **サマリー**: 総合評価と主要改善点
2. **事実正確性**: edit-critic-fact の結果
3. **文章構成**: edit-critic-structure の結果
4. **エンタメ性**: edit-critic-entertainment の結果（full モードのみ）
5. **学術的深度**: edit-critic-depth の結果（full モードのみ）
6. **優先対応事項**: severity 順にソート

## Step 3: edit-reviser の実行

```javascript
console.log("📝 edit-reviser を実行中...");
await runSubAgent("edit-reviser", {
    article_id: articleId
});
```

edit-reviser は critic.json を読み込み、優先度順に修正を適用して revised_draft.md を生成します。

## エラーハンドリング

| エラーコード | 条件                           | 戦略                           |
| ------------ | ------------------------------ | ------------------------------ |
| E001         | パラメータ不正                 | 処理中断、ユーザーに修正を依頼 |
| E002         | 記事フォルダ未存在             | 処理中断、フォルダ確認を依頼   |
| E801         | 必須ファイル読み込み失敗       | 処理中断                       |
| E802         | edit-article-writer 実行失敗   | 処理中断                       |
| E803         | 批評家エージェント実行失敗     | 部分的続行可（2/4 以上で続行） |
| E804         | critic.json/md 生成失敗        | 処理中断                       |
| E805         | edit-reviser 実行失敗          | エラー報告（critic.* は保持）  |

**リカバリー戦略**:

- 批評家エージェントは 4 つのうち 2 つ以上成功すれば続行
- fact と structure は必須（失敗時は中断）
- entertainment と depth はオプション（失敗しても続行可能）
- edit-reviser 失敗時、critic.json と critic.md は保持（手動確認可能）

## 出力ファイル

| ファイル         | パス                             | 生成ステップ | 説明                 |
| ---------------- | -------------------------------- | ------------ | -------------------- |
| first_draft.md   | articles/{article_id}/02_edit/   | Step 1       | 記事初稿             |
| critic.json      | articles/{article_id}/02_edit/   | Step 2       | 批評結果（機械処理用）|
| critic.md        | articles/{article_id}/02_edit/   | Step 2       | 批評結果（人間可読用）|
| revised_draft.md | articles/{article_id}/02_edit/   | Step 3       | 修正版記事           |

## 完了レポート形式

```json
{
    "status": "complete | partial",
    "steps": {
        "article_writer": { "status": "success | skipped", "file": "first_draft.md" },
        "critics": {
            "run": 4,
            "success": 4,
            "files": ["critic.json", "critic.md"]
        },
        "reviser": { "status": "success", "file": "revised_draft.md" }
    },
    "summary": {
        "issues_found": 12,
        "files_created": ["first_draft.md", "critic.json", "critic.md", "revised_draft.md"]
    }
}
```

## 結果表示

```markdown
✅ **Edit フェーズ完了**

| 項目 | 状態 |
|------|------|
| 初稿 | {first_draft_status} |
| 批評 | {critic_count} 件 |
| 修正 | {revision_status} |

**生成ファイル**:
- 02_edit/first_draft.md
- 02_edit/critic.json
- 02_edit/critic.md
- 02_edit/revised_draft.md

**次のステップ**:
1. 修正版確認: `articles/{article_id}/02_edit/revised_draft.md`
2. 公開準備: 03_published への移動
```

## エラー時

```
❌ Edit フェーズ失敗
エラー: {error_message}
ステップ: {failed_step}
💡 対処法: {suggested_action}
```

## 使用例

```bash
# フルモードで実行（全批評家）
/edit unsolved_001_db-cooper

# クイックモードで実行（必須批評家のみ）
/edit unsolved_001_db-cooper --mode quick
```

## 成功基準

1. first_draft.md が存在する（新規作成またはスキップ）
2. 少なくとも 2 つの批評家エージェントが正常完了
3. critic.json と critic.md が生成され、問題点と改善案が明確
4. revised_draft.md が生成され、重要な問題が修正済み

## 依存関係

- research フェーズが完了し、以下のファイルが存在すること:
  - sources.json
  - claims.json
  - decisions.json
  - fact-checks.json
- 6 つの子エージェントが利用可能であること:
  - edit-article-writer
  - edit-critic-fact
  - edit-critic-structure
  - edit-critic-entertainment
  - edit-critic-depth
  - edit-reviser

## 注意事項

1. **段階的実行**: 3 つのステップを順番に実行し、各ステップの成功を確認
2. **スキップ機能**: first_draft.md が既に存在する場合は自動スキップ
3. **並列実行の管理**: 批評家エージェントは並列実行されるため、リソース管理に注意
4. **優先順位の遵守**: 事実修正を最優先、エンタメ性は補完的に
5. **透明性の確保**: すべての処理結果を明確にレポート
6. **部分的成功**: 批評家の一部が失敗しても、必須批評家が成功すれば続行
