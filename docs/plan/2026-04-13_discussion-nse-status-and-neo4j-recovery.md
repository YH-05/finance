# 議論メモ: NSE 実行可能性の確認 & Neo4j I/O 障害の復旧

**日付**: 2026-04-13
**議論ID**: disc-2026-04-13-nse-status-and-neo4j-recovery
**参加**: ユーザー + AI

## 背景・コンテキスト

ユーザーから `/project-discuss` コマンドで「nse のデータ取得ロジックはすでに実行可能な状態か？」と質問。
コンテキスト復元のため Neo4j に問い合わせたところ、一部の直接ラベル検索クエリで
`java.io.IOException: Input/output error` が発生。ユーザー要求により Neo4j 障害の原因特定と復旧も併せて実施した。

## 議論のサマリー

### 1. NSE 実行可能性の結論

**結論: 実行可能な状態（フル実行のみ未実施）**。

- PR #3933（2026-04-13 マージ, squash `0efabc5`）で `market.nse` パッケージに
  `corporate-share-holdings-master` + XBRL 解析を統合完了。
- `src/market/nse/__init__.py` で 5 Collector (StockList / Indices / Shareholding / Quote / Corporate)
  + XBRL パーサー (`parse_xbrl`, `ParseResult`, `ShareholderRow`) 等を公開。
- `notebook/NSE/nse_full_download.ipynb`（4 Phase パイプライン、30-40 分）が実装済み。
- 動作確認は `LIMIT_SYMBOLS=10` で完了、全 2,263 銘柄フル実行は未実施
  （act-2026-04-13-001 として pending 継続）。

### 2. Neo4j I/O 障害の原因特定

**原因: Docker grpcfuse の stale file handle**。

観測事象:
- `MATCH (n) RETURN count(n)` や `MATCH (n:Decision)-[]->()` は成功
- `MATCH (n:Decision) WHERE n.decision_id STARTS WITH ...` で `java.io.IOException`
- `MATCH (n:Decision)` 単独 count は成功 → ラベルインデックス自体は生きている
- Decision/ActionItem にはスキーマインデックスが無く property 直接読みに落ちる

コンテナ側調査:
- `neo4j-enterprise` (neo4j:5.26-enterprise) は `/Volumes/NeoData/enterprise/{data,logs,plugins}` を
  grpcfuse 経由でバインドマウント
- コンテナログに `AppenderLoggingException: Error writing to RandomAccessFile /logs/neo4j.log`
  `Caused by: java.io.IOException: Input/output error` が多数
- ホスト側の `neo4j.log` は 13:56 以降更新停止、`query.log` も 11:43 以降更新停止
- コンテナ内で `/logs/_test_write` の新規作成は成功 → マウント自体は生存
- つまり既存 open FD だけが破損 → grpcfuse のコネクション一時断による stale file handle

### 3. 復旧作業

- `docker restart neo4j-enterprise`（所要 ~10 秒でヘルシー復帰）
- 再起動後、直前まで失敗していた
  `MATCH (n:Decision) WHERE n.decision_id STARTS WITH 'dec-2026-04-13'` と
  `MATCH (n:ActionItem) WHERE n.action_id STARTS WITH 'act-2026-04-13'` が正常応答
- 2026-04-13 議論の Decision 6件・ActionItem 5件はすべて保存されていることを確認
- データ損失なし（WAL リプレイで整合性維持）

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-13-007 | Neo4j で `java.io.IOException` が複雑クエリのみで発生した場合、一次対処は `docker restart neo4j-enterprise` で FD を張り直す | 原因は grpcfuse (/Volumes/NeoData) の stale file handle。データ自体は無傷、WAL リプレイで安全に回復 |
| dec-2026-04-13-008 | NSE データ取得ロジックは実行可能な状態と判定（フル実行未実施であることを明記した上で） | PR #3933 で market.nse 統合完了、5 Collector + XBRL + notebook + テスト+1200 LOC。LIMIT=10 動作確認済み |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 | 備考 |
|----|------|--------|------|------|
| act-2026-04-13-001 | ノートブック `notebook/NSE/nse_full_download.ipynb` を全 2,263 銘柄でフル実行 | 中 | pending | 前回議論から継続 |
| act-2026-04-13-006 | grpcfuse stale file handle 再発防止として、NAS `/Volumes/NeoData` のマウント監視 or launchd スクリプトで定期ヘルスチェックを検討 | 低 | pending | 今回新規 |

## 次回の議論トピック

1. フル実行結果の確認（データ品質検証、XBRL パース失敗率等）
2. ASEAN/India 統合設計書（Issue #3900 Wave3）着手（act-2026-04-13-004 継続）
3. Neo4j ログローテーション / grpcfuse 監視の常設化（dec-2026-04-13-007 をスクリプト化するか）

## 参考情報

### Neo4j 障害の再現条件（メモ）

- トリガー: NAS `/Volumes/NeoData` が一時的にアンマウント/再マウントされる等、grpcfuse の FD が
  stale 化する状況
- 症状: 単純なラベルスキャンや count は通るが、property WHERE / ORDER BY 等で store ページを追加
  読み込みに行くクエリが `IOException` で失敗
- ログに `AppenderLoggingException: Error writing to RandomAccessFile /logs/neo4j.log` が出ていたら
  ほぼ確定

### 復旧手順（決定 dec-2026-04-13-007 のメモ）

```bash
docker restart neo4j-enterprise
# ~10秒でヘルシー復帰、データは WAL リプレイで保全される
```

### 関連議論

- 前回: `docs/plan/2026-04-13_discussion-nse-full-download-progress.md`（project-106 完了報告）
- 前々回: `docs/plan/2026-04-08_discussion-nse-scripts.md`（スクリプト整備）

---

**最終更新**: 2026-04-13
