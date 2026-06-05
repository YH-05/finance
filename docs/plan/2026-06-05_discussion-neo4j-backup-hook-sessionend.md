# 議論メモ: Neo4j NASバックアップ push を Stop hook から SessionEnd hook へ移行

**日付**: 2026-06-05
**議論ID**: disc-2026-06-05-neo4j-backup-hook-sessionend
**Project**: quants-neo4j-kg
**参加**: ユーザー + AI
**前提議論**: [disc-2026-05-27-neo4j-bidirectional-sync](2026-05-27_discussion-neo4j-bidirectional-sync.md)（Neo4j 同期の hooks 双方向化）の続編

## 背景・コンテキスト

`disc-2026-05-27-neo4j-bidirectional-sync` で、Neo4j を複数 PC 間で同期するために Claude Code hooks を双方向化した：

- **SessionStart hook**（`settings.json`）: `neo4j_sync.sh pull --auto` — セッション開始時に NAS から pull
- **Stop hook**（`settings.json`）: `neo4j_sync.sh push --if-changed` — Claude が応答を終えるたびに NAS へ push

この **Stop hook が「会話一回ごと（毎レスポンス後）」に発火**するため、KG 作業中のセッションでは毎レスポンス後に以下が走り、待たされて煩わしいという課題が出た：

1. `docker exec` で 5 DB（quants / research / note / creator / neo4j）の `lastTxId` を取得（数秒）
2. 変更があれば dump → NAS push（数十秒）

## 議論のサマリー

「会話一回一回ごとではなく、Claude セッション終了時のみ push したい」という要望。

- **正体の特定**: 煩わしさの原因は `settings.json` の `Stop` hook（応答完了ごとに発火）と判明。
- **移行先**: `SessionEnd` hook（`/clear`・CLI終了(exit/Ctrl+D)・ログアウト時のみ発火）。
- **動作実績**: `settings.local.json` に既に `SessionEnd` hook（`sync_nas.sh --push`、ファイル同期）が存在し、このプロジェクトで `SessionEnd` が機能している実績を確認。両ファイルの hooks はマージされるため共存可能。
- **取りこぼし懸念の解消**: `push --if-changed` は **txid baseline 方式**（`~/.neo4j-sync-txid.json`、push 成功時のみ更新）。「セッション終了時に1回」でも前回 push 以降の全変更をまとめて push するため、取りこぼしなし。
- **実行方式の選択**: 同期 vs バックグラウンド（async）を確認 → **同期実行を選択**。理由: Neo4j dump は重く、中断すると NAS 上の dump が中途半端になりうる。push 頻度が激減するため待ち総量はむしろ減少し、確実性を優先できる。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-06-05-001 | Neo4j NASバックアップ push を Stop hook（会話ごと）から SessionEnd hook（セッション終了時のみ・同期実行）へ移行 | コマンド `neo4j_sync.sh push --if-changed` は不変。バックグラウンドではなく同期を選択（dump 中断による不整合回避・確実性優先）。`settings.json` 側に配置（SessionStart pull と対）。`settings.local.json` の sync_nas SessionEnd と共存 |

### 実装差分（`.claude/settings.json`）

```diff
-    "Stop": [
+    "SessionEnd": [
       {
         "hooks": [
           {
             "type": "command",
             "command": "$CLAUDE_PROJECT_DIR/scripts/neo4j_sync.sh push --if-changed 2>&1 | tail -3 || true"
           }
         ]
       }
     ]
```

### 検証結果（`jq`）

- JSON 妥当（`jq empty` 成功）
- `SessionEnd` hook に neo4j push コマンドが登録された
- `Stop` hook は完全削除（`has("Stop")` = `false`）
- 残る hook イベント: `PermissionRequest` / `PostToolUse` / `SessionEnd` / `SessionStart`

### 移行後の挙動

| 項目 | 変更前（Stop） | 変更後（SessionEnd） |
|------|--------------|---------------------|
| 発火タイミング | Claude が応答を終えるたび（1セッションで数十回） | `/clear`・CLI終了・ログアウト時のみ |
| KG作業中の待ち | 毎レスポンス後に txid 取得＋dump で待機 | セッション中は一切走らない |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-06-05-001 | 次セッション開始時に `/hooks` を開く or 再起動し、SessionEnd hook(neo4j push) の反映を確認（設定ウォッチャーのキャッシュにより当該セッションには即時反映されない場合があるため） | 中 | pending |
| act-2026-06-05-002 | 【条件付き保留】`/clear` も push 対象になる。exit/ログアウト時のみに限定したくなった場合は SessionEnd の `reason`（clear/logout/prompt_input_exit/other）でフィルタする追加対応を検討 | 低 | pending |

## 次回の議論トピック

- act-2026-06-05-002 の判断（`/clear` を push 対象に含め続けるか）— 実運用で `/clear` 時の待ちが気になるかを観察してから決める
- 重い dump 処理を SessionEnd 同期で実行することによる終了体感の確認（必要なら `async` 化を再検討）

## 参考情報

- スクリプト: `scripts/neo4j_sync.sh`（`push --if-changed` は APOC `lastTxId` で全 write 経路を検知、container 未起動時は静かに skip）
- 関連ドキュメント: `docs/neo4j-sync-via-nas.md`
- hook 設計の前例: `disc-2026-05-18-claude-hook-bugfix`（`$CLAUDE_PROJECT_DIR` 絶対パス + `|| true` 方針）
- 同期方式の確立: `disc-2026-05-26-neo4j-multi-pc-sync`, `disc-2026-05-27-neo4j-bidirectional-sync`
