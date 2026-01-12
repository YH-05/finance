---
description: 記事フォルダに対して2段階リサーチワークフローを自動実行します。浅い調査→深い調査の2段階で効率的かつ網羅的な情報収集を行います。
argument-hint: --article <article_id> [--depth <shallow|deep|auto>] [--iterations <1-2>] [--parallel] [--batch-size <1-5>] [--force]
---

記事のリサーチワークフローを自動実行します。

## パラメータ

- **--article** (必須): 記事ID または記事フォルダパス
- **--depth** (任意): リサーチ深度（デフォルト: auto）
  - `auto`: 2段階リサーチを自動実行（shallow → deep）
  - `shallow`: 浅い調査のみ
  - `deep`: 深い調査のみ
- **--iterations** (任意): 最大反復回数（デフォルト: 1、範囲: 1-2）
- **--parallel** (任意): 並列処理モードを有効化
- **--batch-size** (任意): バッチ数（デフォルト: 3、範囲: 1-5、--parallel 必須）
- **--force** (任意): 強制再実行（workflow 状態を無視して Phase 1 から実行）

## パラメータ検証

| 条件 | エラー |
|------|--------|
| --article 未指定 | E001: 必須パラメータ --article が不足 |
| --depth が shallow/deep/auto 以外 | E001: 無効な値（有効: shallow, deep, auto） |
| --iterations が 1-2 の範囲外 | E001: 範囲外（有効: 1-2） |
| --batch-size が 1-5 の範囲外 | E001: 範囲外（有効: 1-5） |
| --batch-size を --parallel なしで指定 | 警告: --parallel と組み合わせて使用 |

## 処理フロー概要

```
Phase 1: クエリ生成 → queries.json
Phase 2: 情報収集（並列）→ raw-data.json
Phase 3: 情報源統合 → sources.json
Phase 4: 主張抽出 → claims.json
Phase 5: 論点整理 → analysis.json（必要に応じて2回目リサーチ）
Phase 6: 採用判断・ファクトチェック（並列）→ decisions.json, fact-checks.json
Phase 7: 可視化 → visualize/
```

## 管理対象エージェント

以下の10個のリサーチエージェントを適切なタイミングで実行します：

- research-query-generator
- research-wiki
- research-web
- research-reddit
- research-source
- research-claims
- research-claims-analyzer
- research-decisions
- research-fact-checker
- research-visualize

## Phase 1: クエリ生成

```javascript
const result = await runSubAgent("research-query-generator", {
    article_id: articleId,
    topic: metadata.topic,
    category: metadata.category,
});
// 出力: 01_research/queries.json
```

## Phase 2: 情報収集（並列実行）

```javascript
// 3つの情報収集エージェントを並列実行
const collectors = ["research-wiki", "research-web", "research-reddit"];
const results = await Promise.allSettled(
    collectors.map((agent) =>
        runSubAgent(agent, {
            article_id: articleId,
            queries: queries,
            is_deep: isDeep,
        })
    )
);
// 出力: 01_research/raw-data.json
```

## Phase 3: 情報源統合

```javascript
await runSubAgent("research-source", { article_id: articleId });
// 出力: 01_research/sources.json
```

## Phase 4: 主張抽出

```javascript
await runSubAgent("research-claims", { article_id: articleId });
// 出力: 01_research/claims.json
```

## Phase 5: 論点整理

```javascript
const result = await runSubAgent("research-claims-analyzer", {
    article_id: articleId,
    iteration: isDeep ? 2 : 1,
});
// 出力: 01_research/analysis.json

// 2段階リサーチの判断
if (depth === "auto" && result.needs_additional_research) {
    // Phase 2B-5B へ移行（deep リサーチ）
}
```

## Phase 6: 採用判断・ファクトチェック（並列実行）

```javascript
const phase6Agents = ["research-decisions", "research-fact-checker"];
const results = await Promise.allSettled(
    phase6Agents.map((agent) =>
        runSubAgent(agent, { article_id: articleId })
    )
);
// 出力: 01_research/decisions.json, 01_research/fact-checks.json
```

## Phase 7: 可視化

```javascript
await runSubAgent("research-visualize", { article_id: articleId });
// 出力: 01_research/visualize/summary.md, timeline.md, relations.md, dashboard.md
```

## 並列処理モード（--parallel）

並列処理モードでは、クエリをバッチに分割し、各バッチを並列に処理することで処理速度を向上させる。

### バッチ分割

```javascript
function splitIntoBatches(queries, batchSize) {
    const batches = [];
    for (let i = 0; i < queries.length; i += batchSize) {
        batches.push(queries.slice(i, i + batchSize));
    }
    return batches;
}
```

### 処理フロー

```
[--parallel 指定時]
      │
      ▼
クエリを batch_size ごとに分割
      │
      ▼
┌─────┬─────┬─────┐
│ B01 │ B02 │ B03 │ ← 並列実行（Task を複数同時に呼び出し）
└──┬──┴──┬──┴──┬──┘
   │     │     │
   ▼     ▼     ▼
 結果1  結果2  結果3
   │     │     │
   └─────┼─────┘
         │
         ▼
   マージ処理
   - data_sources 統合
   - raw_id 再番号付け
   - statistics 集計
         │
         ▼
   raw-data.json 出力
```

## workflow フィールド管理

### フィールド構造

```json
{
    "workflow": {
        "research": {
            "queries": "pending | done",
            "raw_data": "pending | done",
            "sources": "pending | done",
            "claims": "pending | done",
            "analysis": "pending | done",
            "iterations_completed": 0,
            "fact_checks": "pending | done",
            "decisions": "pending | done",
            "visualize": "pending | done"
        }
    }
}
```

### Phase と workflow フィールドの対応

| Phase | 出力ファイル | workflow フィールド | 更新タイミング |
|-------|-------------|-------------------|--------------|
| Phase 1 | queries.json | `research.queries` | クエリ生成完了後 |
| Phase 2 | raw-data.json | `research.raw_data` | 情報収集完了後 |
| Phase 3 | sources.json | `research.sources` | 情報源統合完了後 |
| Phase 4 | claims.json | `research.claims` | 主張抽出完了後 |
| Phase 5 | analysis.json | `research.analysis`, `iterations_completed` | 論点整理完了後 |
| Phase 6 | decisions.json, fact-checks.json | `research.decisions`, `research.fact_checks` | 採用判断・FC完了後 |
| Phase 7 | visualize/* | `research.visualize` | 可視化完了後 |

### 更新ルール

1. **成功時のみ更新**: エージェントが正常完了し、出力ファイルが作成された場合のみ `"done"` に更新
2. **失敗時は維持**: エージェントが失敗した場合、フィールドは `"pending"` のまま
3. **巻き戻し禁止**: `"done"` → `"pending"` への変更は禁止（データ整合性のため）
4. **iterations_completed**: research-claims-analyzer 完了時にインクリメント（最大2）

## 部分実行からの再開

### 再開判定ロジック

処理開始時に `article-meta.json` の workflow を読み込み、未完了フェーズから再開する。

```javascript
function determineStartPhase(workflow) {
    const research = workflow.research;

    if (research.queries !== "done") return "Phase1";
    if (research.raw_data !== "done") return "Phase2";
    if (research.sources !== "done") return "Phase3";
    if (research.claims !== "done") return "Phase4";
    if (research.analysis !== "done") return "Phase5";
    if (research.decisions !== "done" || research.fact_checks !== "done") return "Phase6";
    if (research.visualize !== "done") return "Phase7";

    return "Completed";
}
```

### 再開時のメッセージ

```markdown
📍 **再開ポイント検出**

前回の実行状態を確認しました。

| フェーズ | 状態 |
|---------|------|
| Phase 1: クエリ生成 | ✅ 完了 |
| Phase 2: 情報収集 | ✅ 完了 |
| Phase 3: 情報源統合 | ⏳ 未完了 |
| Phase 4-7 | ⏳ 未実行 |

**Phase 3（情報源統合）から再開します。**
```

### 強制再実行オプション

全フェーズを最初から実行したい場合は `--force` オプションを使用：

```bash
/research --article unsolved_001_db-cooper --force
```

## エラーハンドリング

| エラーコード | 条件                 | 戦略                           |
| ------------ | -------------------- | ------------------------------ |
| E001         | パラメータ不正       | 処理中断、ユーザーに修正を依頼 |
| E002         | ファイル読み込み失敗 | 処理中断、前段階の確認を依頼   |
| E003         | スキーマ検証失敗     | 処理中断、スキーマ確認を依頼   |
| E004         | MCP 接続エラー       | 処理中断、接続確認を依頼       |
| E005         | 個別エージェント失敗 | 処理中断、エラー原因を報告     |
| E006         | 出力エラー           | ファイル権限確認を依頼         |

**リカバリー戦略**: 全エージェントを必須とし、1つでも失敗した場合は処理を中断。部分成功は許容しない（データ整合性を優先）。

## 出力ファイル一覧

| フェーズ | ファイル               | 説明                 |
| -------- | ---------------------- | -------------------- |
| Phase 1  | queries.json           | 検索クエリ           |
| Phase 2  | raw-data.json          | 収集データ           |
| Phase 3  | sources.json           | 情報源リスト         |
| Phase 4  | claims.json            | 主張リスト           |
| Phase 5  | analysis.json          | 論点整理結果         |
| Phase 6  | decisions.json         | 採用判断結果         |
| Phase 6  | fact-checks.json       | ファクトチェック結果 |
| Phase 7  | visualize/summary.md   | サマリー             |
| Phase 7  | visualize/timeline.md  | 時系列表             |
| Phase 7  | visualize/relations.md | 関係図               |
| Phase 7  | visualize/dashboard.md | ダッシュボード       |

## 結果表示

```markdown
✅ **リサーチ完了**

| 項目 | 件数 |
|------|------|
| 情報源 | {sources_count} |
| 主張 | {claims_count} |
| 採用 | {accepted_count} |
| 検証済み | {verified_count} |

**生成ファイル**: queries.json, raw-data.json, sources.json, claims.json, analysis.json, decisions.json, fact-checks.json, visualize/summary.md

**次のステップ**:
1. サマリー確認: `articles/{article_id}/01_research/visualize/summary.md`
2. 執筆開始: `/edit {article_id}`
```

## エラー時

```
❌ リサーチ失敗
エラー: {error_message}
フェーズ: {failed_phase}
💡 対処法: {suggested_action}
```

## 使用例

```bash
# 標準実行（自動深度判定）
/research --article unsolved_001_db-cooper

# 浅いリサーチのみ
/research --article unsolved_001_db-cooper --depth shallow

# 並列処理モード
/research --article unsolved_001_db-cooper --parallel --batch-size 5

# 強制再実行
/research --article unsolved_001_db-cooper --force
```

## 成功基準

1. 全10個のリサーチエージェントが正常完了
2. 全ての出力ファイルがスキーマ検証をパス
3. visualize/ フォルダに可視化ファイルが生成されている

## 依存関係

- article-meta.json が存在し、有効なスキーマであること
- 10個のリサーチエージェントが利用可能であること
- MCP ツール（Wikipedia, Tavily, Reddit, Fetch）が接続可能であること

## 注意事項

1. **並列実行の管理**: 情報収集エージェントは並列実行されるため、MCP接続のリソース管理に注意
2. **2段階リサーチ**: `depth: auto` の場合、Phase 5A の分析結果に基づいて自動判断
3. **エラー時の中断**: 必須エージェントが失敗した場合、即座に処理を中断
4. **実行時間**: 全フェーズ完了まで約2-5分を想定
