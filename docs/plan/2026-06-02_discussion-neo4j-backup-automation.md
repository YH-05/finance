# 議論メモ: Neo4j NAS バックアップ取りこぼし調査と全write経路の自動同期整備

**日付**: 2026-06-02
**議論ID**: disc-2026-06-02-neo4j-backup-automation
**参加**: ユーザー + AI (Claude Opus 4.8)
**関連プロジェクト**: quants-neo4j-kg
**前回議論**: [2026-05-27 Neo4j 同期の自動化と双方向化](2026-05-27_discussion-neo4j-bidirectional-sync.md)

## 背景・コンテキスト

「Neo4j を最終更新してから NAS にバックアップしていないようだ」というユーザーの指摘から調査を開始。

`dec-2026-05-27-003/004/005` で確立した dirty フラグ方式（SessionStart=pull --auto / PostToolUse=touch dirty / Stop=push --if-dirty）は、**dirty フラグを立てる matcher が `mcp__neo4j-cypher__write_neo4j_cypher` のみ**という制約があり、MCP を経由しない書き込みを取りこぼす設計だった。

## 調査で判明した事実

- NAS への最終 push は **2026-05-30 08:43 JST**（last_source=YukinoMac-mini）。dirty フラグなし。
- しかし `research` DB のトランザクションログは **2026-06-02 03:04 JST** に更新されていた（コンテナは UTC、18:04 UTC）。
- 正体は launchd ジョブ **`com.note-finance.pipeline-scraped-to-neo4j`**（毎朝 3:00 JST、`note-finance` の bolt 直結スクリプト）。11ソースから新規 207 記事を dedup し、**397ノード + 828リレーション**を `research` DB に投入していた（graph-queue `gq-20260601180426`, schema research-4.0）。MCP 非経由のため dirty フラグが立たず、自動 push が走っていなかった。
- **第2の欠陥**: 同期対象は `quants/research/note/creator` の4つのみで、**デフォルト DB `neo4j`（59ノード: Decision/ActionItem/Discussion）が対象外**。しかも MCP の接続先は `NEO4J_DATABASE=neo4j` であり、Claude の MCP 書き込みは全て `neo4j` DB に入る。つまり dirty フラグは立つのに push 対象に `neo4j` が無く、内容が NAS に保存されていなかった。

## 議論のサマリー（対応の段階）

### 応急対応
- 毎朝4時(JST)の無条件 push を launchd 化（catch-all）。
- デフォルト DB `neo4j` を同期対象に追加。

### 恒久対応（ケースB = 非MCP更新の自動同期）
非MCP書込を「どう書いたか」ではなく「DBが変わったか」で検知する方式を検討。

| 検知手段 | 評価 | 採否 |
|----------|------|------|
| tx-log mtime（標準ツールのみ） | 全経路検知可・docker exec 前提 | 代替案 |
| **APOC lastTxId（apoc.monitor.tx）** | コミット番号で厳密・docker exec 不要・他用途流用可 | **採用(Option B)** |

APOC Core(5.26.24) は導入済だが `apoc.monitor.tx` は Extended 専用のため、**APOC Extended 5.26.4** を `/plugins` へ手動導入（先頭2桁 5.26 一致が要件）。`push --if-changed` を実装し、Stop hook(B1) + 毎時 launchd(B2) + 毎朝4時無条件push の3層に整備した。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-06-02-001 | 毎朝4時(JST)の無条件 NAS push を launchd(`com.quants.neo4j-push`)で追加 | 非MCP書込(3時パイプライン等)の catch-all。応急対応 |
| dec-2026-06-02-002 | デフォルトDB `neo4j` を同期対象(NEO4J_DBS)に追加 | MCP書込先なのに対象外で未バックアップ。dec-2026-05-27-006 を拡張(4→5 DB) |
| dec-2026-06-02-003 | 変更検知は APOC lastTxId 採用(Option B)。APOC Extended 5.26.4 を手動導入 | mtime より厳密・docker exec 不要・他用途流用可。Core では apoc.monitor.tx 不可 |
| dec-2026-06-02-004 | `push --if-changed` 実装、Stop hook を --if-dirty→--if-changed(B1)+毎時launchd(B2)。dirty機構は温存 | dec-2026-05-27-003/004/005 の「MCPのみ検知」制約を解消。dec-2026-05-27-005 は不要化 |
| dec-2026-06-02-005 | 多PC完全自動化（plist 可搬化 + 他PC への APOC/launchd 導入）は当面延期し現状を許容 | ユーザー判断「今は何もしない」。pull/push B1 hook は可搬で他PCでも機能 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-06-02-001 | 他PC構築時に `scripts/install-apoc-extended.sh` 実行 + `docker restart` で APOC Extended 導入 | 中 | pending |
| act-2026-06-02-002 | `docs/neo4j-sync-via-nas.md` を push --if-changed / lastTxId / 3層構成に更新 | 中 | ✅ 完了(commit 74b097b3) |
| act-2026-06-02-003 | 数日間ログ確認で毎時/毎朝4時の実バックアップを検証 | 低 | pending |
| act-2026-06-02-004 | `settings.local.json` の WebFetch 権限追加(maven.org/neo4j.com)未コミットの要否判断 | 低 | pending |
| act-2026-06-02-005 | launchd plist 2本の多PC可搬化（/Users/yuki 固定 → $HOME/$USER 反映 or PC別生成）。act-001 の前提 | 中 | pending |

## 実装・検証ログ（2026-06-02, YukinoMac-mini）

- 08:03: 毎朝4時用 `com.quants.neo4j-push.plist` を作成・ロードし手動起動で push 検証（research.dump 65.4→66.5MB、commit `82c3f883` push）
- 08:20: `neo4j_sync.sh` の DBS に `neo4j` を追加し push、NAS に `neo4j.dump` 作成（commit `e27218a4`）
- 08:33: APOC Extended 5.26.4 を `/plugins` へ DL → `docker restart` → `apoc.monitor.tx()` で各DB lastTxId 取得を確認（全DB online、データ無事）
- 08:42-08:47: `push --if-changed` 実装。baseline `~/.neo4j-sync-txid.json` 生成 → 無変更時 skip / cypher-shell(非MCP)書込で lastTxId 57→61 進行 → if-changed が検知して push、baseline 更新を確認
- Stop hook を `--if-changed` 化、毎時 `com.quants.neo4j-push-changed.plist` をロード（skip 動作 exit 0 確認）、`scripts/install-apoc-extended.sh` 追加、`docker-compose.yml` 注記（commit `387bad6f` push）

## 成果物

- スクリプト: `scripts/neo4j_sync.sh`（`push --if-changed` 追加）, `scripts/install-apoc-extended.sh`
- launchd: `scripts/com.quants.neo4j-push.plist`（毎朝4時無条件）, `scripts/com.quants.neo4j-push-changed.plist`（毎時 if-changed）
- hooks: `.claude/settings.json`（Stop hook → push --if-changed）
- compose: `docker-compose.yml`（APOC Extended 手動導入の注記）

## 進捗追記（2026-06-02 後半）

### act-2026-06-02-002 完了
`docs/neo4j-sync-via-nas.md` を lastTxId 方式 / 3層構成 / 5DB に更新し push（commit `74b097b3`）。

### 多PC自動同期の検証結果
他PCで NAS への自動バックアップ／ダウンロードが成立するかを確認:

| 機能 | 配布/可搬性 | 他PCでの自動化 |
|------|------------|---------------|
| ダウンロード（SessionStart `pull --auto`） | `.claude/settings.json`、`$CLAUDE_PROJECT_DIR` ベースで可搬・git配布 | ✅ Claude Code 起動時に自動（NAS の `last_source != hostname` なら 5DB load） |
| バックアップ B1（Stop hook `push --if-changed`） | 同上、可搬 | ✅ Claude セッション終了時に自動（APOC未導入なら「常に push」へ縮退、安全） |
| バックアップ B2/保険（毎時・毎朝4時 launchd） | **非可搬**（plist が `/Users/yuki` 固定）かつ他PC未インストール | ❌ セッション外の書込は未バックアップ |

**結論**: 他PCは「Claude Code 連動のみ自動」。セッション外の書込を自動化するには (1) APOC Extended 導入（act-001）、(2) launchd plist の可搬化（act-005）、(3) plist の設置・load が必要。ユーザー判断により当面は延期（dec-2026-06-02-005）。

### 未コミット
`.claude/settings.local.json`（WebFetch 権限追加 maven.org/neo4j.com）は act-004 の判断保留として未コミットのまま。

## 次回の議論トピック

- `docs/neo4j-sync-via-nas.md` の更新方針（act-2026-06-02-002）
- 同期エラー時の自動リトライ戦略（前回からの継続課題）
- APOC Extended を docker-compose で再現可能にする方法（jar の事前取得 or init コンテナ化）

## 関連

- 前回議論: [2026-05-27 Neo4j 双方向同期](2026-05-27_discussion-neo4j-bidirectional-sync.md)
- 手順書: [docs/neo4j-sync-via-nas.md](../neo4j-sync-via-nas.md)
- スクリプト: [scripts/neo4j_sync.sh](../../scripts/neo4j_sync.sh)
- コミット: `82c3f883`（毎朝4時push）→ `e27218a4`（neo4j DB追加）→ `387bad6f`（lastTxId if-changed B1+B2）
