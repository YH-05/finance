# 議論メモ: Neo4j 同期の自動化と双方向化（Claude Code hooks 連動）

**日付**: 2026-05-27
**議論ID**: disc-2026-05-27-neo4j-bidirectional-sync
**参加**: ユーザー + AI (Claude Opus 4.7)
**関連プロジェクト**: quants-neo4j-kg
**前回議論**: [2026-05-26 複数 PC 同期確立](2026-05-26_discussion-neo4j-multi-pc-sync.md)

## 背景・コンテキスト

2026-05-26 に確立した片方向同期 (MacBook Air → 自宅 Mac) を発展させ、両 Mac から書き込み可能な双方向同期にしたい。
ただし `dec-2026-05-26-502` で「片方向のみ」と決めていたため、設計を見直す必要がある。

ユーザーから出た要件:
- Neo4j を更新したときにのみ同期したい（定期同期は不要）
- 双方向にしたい（実態としては時期がずれるためシリアル運用）
- 自動 pull は不要（明示的にトリガーが走るタイミングがほしい）
- Claude Code の hooks 機能を活用したい
- macOS 通知センターに通知

## 議論のサマリー

### 比較検討した自動化方式

| 方式 | 評価 | 採否 |
|------|------|------|
| Claude CronCreate (ローカル) | Claude REPL 起動中のみ fire、7 日失効 | ✗ |
| Claude RemoteTrigger (claude.ai 側) | クラウド側、ローカル Docker / NAS にアクセス不可 | ✗ |
| macOS launchd (StartCalendarInterval) | 定期実行になるが「更新時のみ」の要求と乖離 | ✗ |
| **Claude Code hooks (SessionStart / PostToolUse / Stop)** | セッション境界連動、要件に合致 | **✓** |

### 双方向同期の競合管理

| 戦略 | 採用 |
|------|------|
| 同時書き込み禁止（時期で分ける） | **採用**: ユーザー実態と一致 |
| DB 分割 | 不要 |
| Causal Cluster (Enterprise) | 不要 |
| Last-Write-Wins | リスクが高く不採用 |

NAS 上 `sync-state.json` に `last_source` を記録し、「最後に書いた側が source」ルールで運用する。

### 動作フロー

```
[Claude Code 起動]                [セッション中]                      [Claude Code 終了]
SessionStart hook                 PostToolUse hook                    Stop hook
       │                          (write_neo4j_cypher のみ)                  │
       ▼ pull --auto              ▼ touch ~/.neo4j-sync-dirty               ▼ push --if-dirty
NAS sync-state.json 確認         (フラグだけ立てる軽量処理)          dirty=true なら
last_source != hostname なら                                          dump → NAS push
load 実行                                                             sync-state.json 更新
macOS 通知                                                            macOS 通知
```

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-27-001 | 同期方式を Claude Code hooks 連動の双方向 (「最後に書いた側が source」) に拡張。`dec-2026-05-26-502` (片方向) を supersede | ユーザー実態 (シリアル運用) と整合 |
| dec-2026-05-27-002 | SessionStart hook で `pull --auto` を実行 | NAS の `last_source != hostname` なら load。失敗は `|| true` で吸収 |
| dec-2026-05-27-003 | PostToolUse hook (`mcp__neo4j-cypher__write_neo4j_cypher`) で `touch ~/.neo4j-sync-dirty` | フラグだけ立てる軽量処理、実 dump は Stop |
| dec-2026-05-27-004 | Stop hook で `push --if-dirty` を同期実行 (完了を待つ) | push 失敗を見落とさないため非同期にしない |
| dec-2026-05-27-005 | save-to-graph スキル等の Neo4j 書き込み箇所にも dirty フラグ更新を組み込み | スクリプト経由の更新を取りこぼさない |
| dec-2026-05-27-006 | NAS 上 `sync-state.json` に `last_source` / `last_dump_at` を記録、`.neo4j-sync.lock` で排他 | jq は macOS 標準で利用可 |
| dec-2026-05-27-007 | macOS 通知 (osascript) で pull/push/エラーを通知 | ユーザー選択。Slack 等は不要 |

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-05-27-001 | `scripts/neo4j_sync.sh` に `push` / `pull` / `--auto` / `--if-dirty` / `status` サブコマンド・`sync-state.json` 対応・排他制御・macOS 通知を実装 | 高 |
| act-2026-05-27-002 | `.claude/settings.json` に SessionStart/PostToolUse(write_neo4j_cypher)/Stop の 3 hook を追加 | 高 |
| act-2026-05-27-003 | save-to-graph スキル等への `touch $HOME/.neo4j-sync-dirty` 組み込み | 中 |
| act-2026-05-27-004 | `docs/neo4j-sync-via-nas.md` を双方向同期対応に更新 | 中 |
| act-2026-05-27-005 | 両 Mac で push/pull/SessionStart/Stop の動作確認 | 高 |

## NAS 上のメタデータ

`/Volumes/personal_folder/neo4j-dumps/sync-state.json`:

```json
{
  "last_source": "yukihatas-macbook-air",
  "last_dump_at": "2026-05-27T12:34:56+09:00",
  "dbs": ["quants", "research", "note", "creator"]
}
```

`/Volumes/personal_folder/neo4j-dumps/.neo4j-sync.lock`:
- `mkdir` ベースの排他ロック（同時 push/pull 防止）
- 同期処理開始時に作成、終了時に削除（`trap`）

## 動作シミュレーション

### ケース 1: MacBook Air → 自宅 Mac

1. **MacBook Air** Claude Code 起動 → `pull --auto`: 自分が `last_source`、何もせず即終了
2. **MacBook Air** 書き込み作業 → `~/.neo4j-sync-dirty` が立つ
3. **MacBook Air** Claude Code 終了 → `push --if-dirty`: dump → NAS、`last_source=yukihatas-macbook-air`、通知
4. **自宅 Mac** 後日 Claude Code 起動 → `pull --auto`: `last_source != hostname` で load、通知

### ケース 2: 自宅 Mac で書き込み → MacBook Air へ

5. **自宅 Mac** 書き込み → Stop で push、`last_source=YukinoMac-mini`
6. **MacBook Air** 次回起動 → `pull --auto` で load、通知

## 実行ログ

### 2026-05-27 MacBook Air (Phase 1〜4 + PR 作成・マージ)

- 09:35-09:39: 設計を Neo4j に保存 (Discussion 1 / Decision 7 / ActionItem 5 / リレーション 14、計 13 ノード / 15 リレーション = quants DB の +13/+15 増分)
- 10:30 ごろ: scripts/neo4j_sync.sh 拡張完了 (push/pull/--auto/--if-dirty/status)
- 10:32: status コマンドで動作確認
- 10:34: dirty フラグを touch → push --if-dirty 実行 → dump 成功 (191MB / 約 8 秒)
- 10:35:57: sync-state.json 生成 (`last_source: Yukinonotobukkukonpyuta`)
- 10:36: 冪等動作確認 (pull --auto self skip / push --if-dirty no-dirty skip)
- 10:37:47: PR #3970 マージ (squash, ローカル main 同期)
- 10:39:02: ActionItem を completed に更新

### 2026-05-27 自宅 Mac (実 hook 接続)

- 10:44 ごろ: `git pull origin main` で 4f5bdb7d → 08c12545 取り込み
- status で 4 hook 反映 (PermissionRequest / PostToolUse / SessionStart / Stop)
- `pull --auto` を手動実行 → 4 DB load 成功 (約 48 秒、合計 1.5GB)
- macOS 通知センターに「Pulled 4 DBs from Yukinonotobukkukonpyuta」表示確認
- `verify` で両 Mac の件数完全一致確認 (quants 3,802 / 8,360 等)

## 発覚した課題

### 課題 1: pull が sync-state.json を更新しない

自宅 Mac で `pull --auto` 完了後も `sync-state.json.last_source` は `Yukinonotobukkukonpyuta` のまま残る。
そのため次回 SessionStart hook で再度 pull --auto が走り、同じ dump を上書き load する (約 48 秒 / 1.5GB)。
同一 dump の上書きなので安全だが無駄。

→ `act-2026-05-27-006` で改善予定。

## 次回の議論トピック

- act-2026-05-27-006 の実装方針 (synced_to キー追加 vs タイムスタンプ比較)
- 実 hook (SessionStart/PostToolUse/Stop) の動作確認 (両 Mac で次回 Claude Code 起動時)
- save-to-graph 以外で Neo4j 書き込みを行う箇所の網羅性確認
- 同期エラー時の自動リトライ戦略 (今は手動再実行のみ)
- 将来同時書き込みが発生した場合のエスカレーション策

## 関連

- 前回議論: [2026-05-26 複数 PC 同期確立](2026-05-26_discussion-neo4j-multi-pc-sync.md)
- 手順書: [docs/neo4j-sync-via-nas.md](../neo4j-sync-via-nas.md)
- スクリプト: [scripts/neo4j_sync.sh](../../scripts/neo4j_sync.sh)
- メモリ: `project_neo4j_multi_pc_sync_2026_05_27.md`
- Supersede: `dec-2026-05-26-502` (片方向) → `dec-2026-05-27-001` (双方向)
