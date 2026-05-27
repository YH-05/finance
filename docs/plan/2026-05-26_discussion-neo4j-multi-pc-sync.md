# 議論メモ: Neo4j を複数 PC で利用するための同期方式

**日付**: 2026-05-26
**議論ID**: disc-2026-05-26-neo4j-multi-pc-sync
**参加**: ユーザー + AI (Claude Opus 4.7)
**関連プロジェクト**: quants-neo4j-kg
**前回議論**: [disc-2026-04-27-neo4j-storage-migration](2026-04-27-neo4j-storage-migration.md)

## 背景・コンテキスト

MacBook Air (このPC) で Docker 上に `neo4j-enterprise` (5.26) を稼働させており、`bolt://localhost:7687` で Claude Code から利用中。データは `~/neo4j-data/enterprise/` 配下に 2GB 規模で、5 DB (`quants` / `note` / `research` / `creator` / `neo4j` + `system`) が稼働している。

別 PC (自宅 Mac) でも同じ Neo4j を利用したいという要求が発生。前回の議論 (2026-04-27) では外付け SSD からローカルディスクへの bind mount 移行を行ったが、複数 PC 間の利用は未対応のままだった。

## 議論のサマリー

### 比較検討した方式

| 方式 | 評価 | 採否 |
|------|------|------|
| A. Tailscale 経由で現 Mac を共有 | Mac 常時稼働必須でユーザー要件に合わない | ✗ |
| B. NAS (DH2300-48C1) に Neo4j 移行 | NAS が Docker 非対応 | ✗ |
| C. Neo4j Aura / VPS にホスト | コスト高、独立運用要件と矛盾 | ✗ |
| D. 各 PC ローカル Neo4j + Causal Cluster | Enterprise でも構築複雑、ズレ許容なら過剰 | ✗ |
| **E. dump/load + NAS 中継ファイル受け渡し** | 独立運用・ズレ許容と整合、追加コストゼロ | **✓** |

### ユーザー要件の確認結果

- **接続経路**: 同一 LAN 内のみ (自宅 Wi-Fi)
- **Mac 稼働**: 別 Mac は独立運用、一時的ズレ許容、手動同期で OK
- **NAS Docker**: 非対応、NAS は使いたくない (ただしファイル中継には使用)
- **同期手段**: NAS 経由
- **対象 DB**: quants, research, note, creator
- **方針**: まず手動手順、スクリプト化は後

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-26-501 | 同期方式は `neo4j-admin database dump / load` を採用し、NAS (`/Volumes/personal_folder`) を中継ストレージとしてファイル受け渡し | Causal Cluster は複雑、データディレクトリ rsync は破損リスク、APOC export は大規模で遅い |
| dec-2026-05-26-502 | 同期方向は MacBook Air → 自宅 Mac の片方向 | 双方向は競合管理が複雑、一時的ズレ許容と整合 |
| dec-2026-05-26-503 | 同期対象 DB は `quants`, `research`, `note`, `creator` の 4 つ (`system` / `neo4j` は対象外) | ユーザー明示選択、system DB は DBMS 固有で同期不要 |
| dec-2026-05-26-504 | 両 Mac の Neo4j は独立運用、ネットワーク不通時も各自動作 | 常時オンライン要件回避、外付け SSD トラブル経験から独立運用の優位性確認 |
| dec-2026-05-26-505 | 初回はスクリプト化せず、手動手順 (`docs/neo4j-sync-via-nas.md`) で動作検証 | DB 存在チェック・バージョン差吸収など未検証要素があるため段階実施 |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|----------|
| act-2026-05-26-501 | quants DB 1 つで Phase 1→2 を手動実行、件数一致で動作検証 | 高 | pending |
| act-2026-05-26-502 | 自宅 Mac の Neo4j バージョンが 5.26-enterprise であることを確認 | 高 | pending |
| act-2026-05-26-503 | 自宅 Mac で DB 未登録の場合の `CREATE DATABASE` 手順を準備・追記 | 中 | pending |
| act-2026-05-26-504 | 検証成功後、`scripts/neo4j_sync.sh` としてスクリプト化 | 中 | pending |
| act-2026-05-26-505 | `docker-compose.yml` の bind mount パスを `/Volumes/NeoData` → `~/neo4j-data/` に修正 | 中 | pending |

## 成果物

- **手順書**: [docs/neo4j-sync-via-nas.md](../neo4j-sync-via-nas.md) (Phase 1 dump / Phase 2 load の手動コマンド)

## 次回の議論トピック

- 手動検証完了後のスクリプト化方針 (引数設計・エラーハンドリング・冪等性)
- `system` DB のロール・ユーザー定義の同期可否 (現状対象外だが将来課題)
- 逆方向 (自宅 Mac → MacBook Air) 同期の必要性が出た場合の競合解決方針

## 参考情報

- 関連メモリ: `project_neo4j_local_migration_2026_04_27.md` (前回の SSD → ローカル移行)
- 関連メモリ: `feedback_neo4j_iox_restart.md` (2026-04-27 ローカル移行で解消済)
- 前回議論: `disc-2026-04-27-neo4j-storage-migration`
- データ規模: `~/neo4j-data/enterprise/data` = 約 2GB、`research` DB が最大 (27,960 ノード / 516,590 リレーション)
