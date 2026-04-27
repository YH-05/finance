# 議論メモ: Neo4j Docker コンテナのストレージを外付け SSD からローカル PC へ移行

**日付**: 2026-04-27
**議論ID**: disc-2026-04-27-neo4j-storage-migration
**参加**: ユーザー + AI

## 背景・コンテキスト

`neo4j-enterprise` (neo4j:5.26-enterprise) コンテナは外付け SSD `/Volumes/NeoData/enterprise/` を bind mount しており、grpcfuse 経由のファイルシステム経由参照になっていた。

過去の運用で以下の問題が発生:
- 複雑クエリ実行時の `java.io.IOException`（grpcfuse stale FD）
- 外付け SSD 切断時のコンテナ Exited (137) → `mkdir /host_mnt/Volumes/NeoData: operation not permitted`

これらは `dec-2026-04-13-007` で「複雑クエリ I/O エラー時は `docker restart neo4j-enterprise` で対処」と決定されていたが、**根本対策**としてストレージをローカル APFS に移すことを決定。

## 議論のサマリー

ユーザーから「neo4j をホストしている docker コンテナの保存先を外付け SSD からローカル PC に移したい」と要望。

確認した3つの論点:
1. **移行先パス** → `~/neo4j-data/enterprise/`（標準的・シンプル）
2. **バックアップ方式** → ダンプ + 旧 enterprise/ も当面残す（二重バックアップ）
3. **外付け SSD の扱い** → 切断してもコンテナが動作する状態にする（依存ゼロ）

実行手順は `STOP DATABASE` → `neo4j-admin database dump` → `START DATABASE` → `docker stop` → `rsync -aHP` → `docker rm` → `docker run`（同名・同設定）→ 動作確認 の順で完遂。

### 移行結果

| 項目 | 値 |
|---|---|
| 移行データサイズ | 1.6GB（コピー後 2.4GB、APFS差） |
| データ整合性 | `diff -rq` 差分0件 |
| ダンプ | `~/neo4j-data/enterprise/data/backup-before-migration/neo4j.dump` (31KB) |
| 全 DB ノード/リレーション | neo4j 35/25, quants 3,534/8,051, creator 15,312/31,362, research 27,960/516,590, note 754/888 |
| コンテナ状態 | Up & healthy、ポート 7474/7687 で稼働 |
| マウント参照 | 全て `/Users/yukihata/neo4j-data/...`（NeoData 参照ゼロ） |

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-27-004 | neo4j-enterprise の bind mount を `/Volumes/NeoData/enterprise/` から `~/neo4j-data/enterprise/` に移行 | grpcfuse stale FD と外付け切断問題の根本対策。6 DB すべて稼働確認、APOC 5.26.24 ロード成功 |
| dec-2026-04-27-005 | 旧 `/Volumes/NeoData/enterprise/` は削除せず当面残す | ロールバック余地確保、ローカル動作十分確認後に削除 |
| dec-2026-04-27-006 | dec-2026-04-13-007 の grpcfuse 一次対処（docker restart）は本移行で不要化 | bind mount がローカル APFS になり stale FD 起因の I/O エラーは発生しない |
| dec-2026-04-27-007 | Neo4j 論理バックアップは `STOP DATABASE` → `neo4j-admin database dump` → `START DATABASE` 手順を採用 | 稼働中はダンプ不可。WAL 整合性確保のため対象 DB 停止必須 |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| act-2026-04-27-001 | 外付け SSD アンマウント状態で neo4j-enterprise が正常動作するか検証（全 6 DB クエリ + 複雑クエリ） | high | 2026-05-04 |
| act-2026-04-27-002 | act-001 完了後、旧データ `/Volumes/NeoData/enterprise/` を削除（SSD 自体は他用途のため残す） | medium | 2026-05-11 |
| act-2026-04-27-003 | memory `feedback_neo4j_iox_restart.md` を更新（grpcfuse / 外付け切断シナリオ削除、ローカル前提に書き換え） | medium | 2026-05-04 |

## 次回の議論トピック

- ローカル空き容量 35GB の長期運用可否（KG enrichment で論文大量投入 → 数十GB 増加が想定される）
- 定期バックアップの自動化（cron / launchd で `STOP/dump/START` の運用化）
- 旧データ削除タイミング（act-001 検証後）

## 参考情報

- 旧運用ログ: `feedback_neo4j_iox_restart.md`（2026-04-13 の grpcfuse 問題ナレッジ）
- 移行先で稼働中のコンテナ ID: `7b684d10a9af`
- 関連 Decision: `dec-2026-04-13-007`（superseded by `dec-2026-04-27-006`）
