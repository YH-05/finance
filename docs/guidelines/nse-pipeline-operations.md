# NSE パイプライン運用ガイド

`notebook/NSE/nse_full_download.ipynb` と `src/market/nse/` パッケージを用いた
NSE 上場銘柄データパイプライン（Phase 1-4）の運用ルール。SQLite DB 破損の
再発防止、Jupyter 実行時の排他制御、障害時の復旧手順を体系化する。

## 対象範囲

- Phase 1: 全上場株マスタ（stocks）
- Phase 2: インデックス構成（index_members）
- Phase 3: 株主構成マスタ（shareholdings）
- Phase 4: XBRL 詳細株主データ（shareholding_detail）

DB パス: `notebook/NSE/data/cache/nse/nse_index.db`

## 🔴 MUST: 破損再発防止の絶対ルール

### 1. Jupyter 実行中は DB に外部からアクセスしない

**禁止**:
- `sqlite3 nse_index.db` CLI で DML（INSERT / UPDATE / DELETE）を叩く
- DB Browser for SQLite 等の GUI ツールで編集モードで開く
- 複数 Jupyter セル / 複数 kernel から同時に書き込む
- `git stash` や `git checkout` で DB ファイルを上書きする

**理由**: SQLite は WAL mode でも、別プロセスからの書き込みが
`PRAGMA busy_timeout` を超過するとインデックス btree ページ
（特に tree 8 など大きめのテーブル）を破損させることがある。
実際に 2026-04-14 に Phase 4 実行中の外部 DELETE が原因で
shareholdings 40,000 行が tree 8 page 2360+ で失われた。

**許可**:
- 読み取り専用クエリ（`SELECT`）は実行 OK（sqlite3 は MVCC 的に分離）
- ただし `.backup` や `VACUUM` 等はファイルロックを取るので禁止

### 2. カーネル再起動後は必ず Cell 2/3 から実行

**禁止**:
- 旧 import を抱えたカーネルで修正済みコードを実行する
- Cell 5/7/9/11 を単独実行（前提の変数が未定義）

**理由**: `market.nse.*` モジュールを書き換えた際、カーネル再起動なしでは
旧 parser が実行され `NseParseError: namespace mismatch` や
`IntegrityError: FOREIGN KEY` が再発する。

## 🟡 SHOULD: 推奨運用プラクティス

### 3. Phase 3/4 実行前の snapshot backup

長時間実行 (>10 分) の Phase 3/4 の前には DB snapshot を取る:

```python
# Notebook の Cell 3 末尾 or 独立セルで
import shutil, datetime
_snap = f"data/cache/nse/nse_index.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2(DB_PATH, _snap)
print(f"Snapshot saved: {_snap}")
```

破損時にこの snapshot + WAL から `.recover` で被害最小限化できる。

### 4. レジューム機構の活用

Phase 3/4 は冪等 (`INSERT OR REPLACE` / `INSERT OR IGNORE` + LEFT JOIN で
既取得 symbol を除外) に設計されているため、**中断しても安全**。

中断時の判断:
- 400 系エラーが 10 件以上連続 → kernel 停止 → 時間をおいて再実行
- 進捗が 10 分以上止まる → kernel 停止 → 再実行

### 5. 並列 worker 数の上限

| Phase | 推奨 workers | 最大 workers |
|-------|-------------|-------------|
| Phase 3 | 3 | 4 |
| Phase 4 | 3 | 5 |

NSE API は `www.nseindia.com` で rate limit が厳しい（cookie invalidation
を誘発）。4 並列超は IP block の恐れあり。XBRL は
`nsearchives.nseindia.com` で緩めだが 5 並列が実用上限。

### 6. ログの監視ポイント

実行中以下のワーニングが出たら即対応:
- `Unknown BSE SHP taxonomy revision detected` → 新 tax リリース。
  手動で `_VERIFIED_TAXONOMIES` と `_DECIMAL_PCT_TAXONOMIES` の更新要
- `割合値が範囲外 (fmt=unknown)` → 想定外 pct フォーマット。`to_normalized_pcts`
  の detection rule を拡張要
- `NseCookieError` 連発 → 並列度下げる + `cookie_refresh_interval` を短く

## 🟢 INFO: 障害時の復旧手順

### ケース A: SQLite DB 破損

`PRAGMA integrity_check` が `btreeInitPage returns error code 11` 等を返す場合。

**手順**:

```bash
# 1. バックアップ作成（必ず最初に実行）
cp notebook/NSE/data/cache/nse/nse_index.db /tmp/nse_corrupt.db
cp notebook/NSE/data/cache/nse/nse_index.db-wal /tmp/nse_corrupt.db-wal 2>/dev/null
cp notebook/NSE/data/cache/nse/nse_index.db-shm /tmp/nse_corrupt.db-shm 2>/dev/null

# 2. .recover で抽出
sqlite3 /tmp/nse_corrupt.db ".recover" > /tmp/nse_recover.sql

# 3. 新 DB を構築
rm -f /tmp/nse_recovered.db
sqlite3 /tmp/nse_recovered.db < /tmp/nse_recover.sql

# 4. integrity 確認
sqlite3 /tmp/nse_recovered.db "PRAGMA integrity_check"   # → ok を確認

# 5. 件数確認
sqlite3 /tmp/nse_recovered.db "SELECT 'stocks', COUNT(*) FROM stocks UNION ALL SELECT 'shareholdings', COUNT(*) FROM shareholdings"

# 6. 本体に置き換え
mv notebook/NSE/data/cache/nse/nse_index.db /tmp/nse_corrupt.db.bak
rm -f notebook/NSE/data/cache/nse/nse_index.db-wal notebook/NSE/data/cache/nse/nse_index.db-shm
cp /tmp/nse_recovered.db notebook/NSE/data/cache/nse/nse_index.db

# 7. 失われた Phase 3/4 データは再実行
```

**既知の失われやすいデータ**: tree 8 に格納される大きなテーブル
（`shareholdings` / `shareholding_detail`）。stocks / index_members は
概ね無事で救出可能。

### ケース B: Phase 4 で IntegrityError

FOREIGN KEY constraint failed の場合、XBRL 内部 Symbol 値と stocks
テーブルの FK 不整合が原因。修正済 (commit `eb8520c`) だが将来類似
バグが出た場合:

1. Phase 4 セル停止（Jupyter Interrupt）
2. `shareholding_detail` の部分 data を確認:
   ```sql
   SELECT d.symbol FROM shareholding_detail d
   LEFT JOIN stocks s ON s.symbol = d.symbol WHERE s.symbol IS NULL;
   ```
3. 不整合 row を DELETE
4. Cell 11 の `_pending_batch.append((_sym, ...))` で必ずクエリ由来の
   `_sym` を FK として使っているか確認
5. Phase 4 レジューム再実行

### ケース C: Phase 3 API が異常値を返す

`promoter + public + trust = 10000` 等の percent×100 形式の場合:

- 自動対処: `CorporateShareHolding.to_normalized_pcts()` が sum 検出で
  auto scale。何もしなくて OK。
- `[INFO] 銘柄 YYYY-MM-DD: pct を x100 形式から自動補正` ログが出る。
- 頻度が想定外に高い場合（>10% of filings）は NSE API 仕様変更の可能性。
  memory `feedback_bse_xbrl_taxonomy_transitions.md` を参照。

## 📊 Phase 4 再実行の資格条件

Phase 4 を再実行する典型シナリオ:

| トリガー | 再実行範囲 |
|---------|----------|
| Unknown カテゴリが発生 | 該当 symbol の全 detail rows を DELETE → Cell 11 |
| 新タクソノミ・マッピング追加 | 該当 symbol の全 detail rows を DELETE → Cell 11 |
| IntegrityError 部分入庫 | 部分 rows を DELETE → Cell 11 |
| 破損復旧後 | `shareholding_detail` 全 TRUNCATE → Cell 11 |

DELETE 例:
```sql
-- Unknown 含む symbol をすべて再取得対象に
DELETE FROM shareholding_detail
WHERE symbol IN (
    SELECT DISTINCT symbol FROM shareholding_detail WHERE category='Unknown'
);
```

再実行時の注意:
- Jupyter kernel restart 必須（新しい parser / axis map を読込むため）
- `SKIP_PHASE_3 = True` にして Phase 3 をスキップ
- `SKIP_PHASE_4 = False` で Phase 4 のみ実行

## 📋 チェックリスト（Phase 3/4 実行前）

- [ ] `git status` で DB ファイルが他で変更中でない
- [ ] `lsof notebook/NSE/data/cache/nse/nse_index.db` で他プロセスが開いてない
- [ ] Jupyter カーネルを Restart（前回 import を clear）
- [ ] `src/market/nse/*.py` の最新版が反映されている
- [ ] snapshot backup を作成（長時間実行時）
- [ ] 別ターミナル監視を準備:
      ```bash
      watch -n 15 'sqlite3 notebook/NSE/data/cache/nse/nse_index.db \
        "SELECT COUNT(DISTINCT symbol) || \" symbols\" FROM shareholding_detail"'
      ```

## 参考リソース

- 設計メモリ: `~/.claude/projects/-Users-yukihata-Desktop-quants/memory/feedback_bse_xbrl_taxonomy_transitions.md`
- 議論メモ: `docs/plan/2026-04-14_discussion-nse-phase4-completion.md`
- parser 実装: `src/market/nse/xbrl.py`, `src/market/nse/types.py`
- Notebook: `notebook/NSE/nse_full_download.ipynb`
- 修正 commit: `174285e`, `eb8520c`, `2f0ab22`
