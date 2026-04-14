# 議論メモ: NSE XBRL タクソノミ 2025-10-31 対応と Phase 3/4 並列化

**日付**: 2026-04-14
**議論ID**: disc-2026-04-14-nse-xbrl-taxonomy-fix
**参加**: ユーザー + AI
**関連コミット**: `8eaa237..945dfaf` (main)

## 背景・コンテキスト

`notebook/NSE/nse_full_download.ipynb` で NIFTY TOTAL MKT 750 銘柄の株主構成（Phase 3）と XBRL 詳細（Phase 4）を取得中、以下の問題が連鎖的に発生:

1. `tqdm.notebook` の `IProgress not found` ← `ipywidgets` 未インストール
2. Phase 3 直列実行で 24 時間所要
3. Phase 4 が全銘柄で `XBRL namespace mismatch: expected 2022-09-30` エラー
4. SQLite `MAX()` テキスト比較バグで 1 年前の XBRL を「最新」と誤認

背景には BSE が 2025 年に SHP タクソノミを 2 回改版（2025-05-31 → 2025-10-31）し、タグ名・構造・pct フォーマットを変更したことがある。

## 議論のサマリー

### 調査フェーズ

- **切り替えタイミング調査**: 105 サンプル実測で、BSE タクソノミ切替は四半期単位でほぼ同期（≥95%一致）と判明。例外は NAM-INDIA 1 例のみ（30-SEP-2025 に 2025-10-31 を前倒し採用）
- **3-way 構造差分**: 2022-09-30 ↔ 2025-05-31 ↔ 2025-10-31 を比較
  - member 名称改名 7 件（Uti→UTI, Rbi→RBI, typo 修正等）
  - axis 改名 1 件（MutualFundsOrUTIAxis）
  - numeric element 改名 1 件（...AndWarrants → ...WarrantsAndESOP）
  - metadata context 改名（OneD/OneI → MainD/MainI）
- **決定的発見**: 2025-10-31 taxonomy は pct フィールドを **小数ratio**（0.649 = 64.9%）で格納。旧 parser はパーセント前提のため全銘柄の promoter 比率を 1% 未満と誤認する致命バグ
- **SQLite MAX バグ**: `as_on_date` が `DD-MMM-YYYY` 形式 TEXT のため、`"31-MAR-2025" > "31-DEC-2025"` が true（`M > D` in ASCII）。Phase 4 対象選定で 1 年前データを latest と誤認していた

### 実装フェーズ

- `src/market/nse/xbrl.py` を多タクソノミ対応に改修（エイリアス追加方式）
- Namespace を regex で吸収、任意の dated revision を許容
- 2025-10-31 で pct を自動的に ×100 スケーリング
- Phase 4 SQL に ISO 日付変換 CTE を追加
- Phase 3/4 を `ThreadPoolExecutor(3 workers)` + スレッドローカル `NseSession` で並列化
- 全 52 tests pass、ruff/pyright クリーン

### 検証フェーズ

実 XBRL 5 サンプルで Phase 3 API と Phase 4 XBRL の完全一致を確認:
- AADHARHFC 2025-03-31 / 2025-06-30 / 2026-03-31: 一致
- ADANIGREEN 2026-03-31: 62.43% 一致
- ADANIPORTS 2026-03-31: 68.02% 一致

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-14-001 | Phase 3 ユニバースを `NIFTY TOTAL MKT` (750 銘柄) に限定 | 全上場 2,794 は 24h コース。NIFTY TOTAL MKT は Smallcap 250 / Microcap 250 を完全包含し投資対象を網羅 |
| dec-2026-04-14-002 | Phase 3/4 を `ThreadPoolExecutor(3 workers)` + スレッドローカル `NseSession` で並列化 | 直列 37min → 並列 10-15min。NSE レートリミット許容域 |
| dec-2026-04-14-003 | XBRL parser を多タクソノミ対応（**エイリアス追加方式**） | 既存 2022-09-30 対応は一切削除せず、新タクソノミの名称を同義キーとして追加。後方互換を維持 |
| dec-2026-04-14-004 | 2025-10-31 の pct 小数表記を **parser 内で自動 ×100** スケーリング | DB 一貫性のため。Phase 3 API は常に % 表記なので揃える |
| dec-2026-04-14-005 | Phase 4 SQL に `sh_iso` CTE を追加して `MAX(iso_date)` で chronological latest を取得 | TEXT MAX バグの根本修正 |
| dec-2026-04-14-006 | Phase 4 対象を `promoter_pct > 10%` に絞り込み | 投資対象として promoter が一定以上の銘柄に詳細分析を限定 |
| dec-2026-04-14-007 | `_VERIFIED_TAXONOMIES` に未知 revision の WARNING ログ機構を実装 | 将来 BSE が新 revision をリリースしたとき運用者が気付けるように |
| dec-2026-04-14-008 | ipywidgets を dev 依存に追加 | `tqdm.notebook` の `IProgress` 解決 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-14-001 | Phase 4 現在の実行完了を待つ | 高 | 進行中 |
| act-2026-04-14-002 | 12 stale 銘柄（`report_date=2025-03-31`）を `shareholding_detail` から DELETE → Phase 4 再実行で新 SQL 経由の正しい latest を取得 | 高 | 待機 |
| act-2026-04-14-003 | Phase 4 完了後に `category='Unknown'` 行を再チェック | 中 | 待機 |
| act-2026-04-14-004 | Phase 4 完了後に Phase 3 promoter_pct ↔ Phase 4 detail の整合性を再検証 | 中 | 待機 |
| act-2026-04-14-005 | ABBOTINDIA / BAYERCROP の Phase 3 を個別再実行（latest が 31-DEC-2018 で止まっているため） | 低 | 任意 |
| act-2026-04-14-006 | Phase 4 完了後に DB ファイル (`nse_index.db`) を commit | 低 | 待機 |
| act-2026-04-14-007 | Neo4j / Docker を起動し直した後、本議論メモを Neo4j に MERGE 保存 | 低 | 待機 |

### DELETE 実行コマンド (act-2026-04-14-002)

```sql
DELETE FROM shareholding_detail
WHERE report_date = '2025-03-31'
  AND symbol IN ('20MICRONS','360ONE','3MINDIA','3PLAND','5PAISA','A2ZINFRA',
                 'AAATECH','AARTIDRUGS','AARTIIND','AARTIPHARM','AAVAS','ABB');
-- 986 行削除 → Phase 4 再実行で 12 銘柄が正しい最新 XBRL から再取得される
```

## 次回の議論トピック

- Phase 4 完了後の結果レビュー（データ整合性、Unknown 件数、未知 revision WARNING の有無）
- ABBOTINDIA / BAYERCROP の扱い（2018 年スナップショットで妥協 vs 個別再実行）
- DB (`nse_index.db`) のサイズ増加（1.4MB → 推定 20MB+）のバージョン管理方針

## 参考情報

### BSE SHP タクソノミ遷移マップ（実測）

| Revision | 適用四半期 | pct 形式 |
|---|---|---|
| 2018-03-31 | 超旧 filing | percentage |
| 2022-09-30 | 〜31-MAR-2025 | percentage |
| 2025-05-31 | 30-JUN-2025〜30-SEP-2025 | percentage |
| **2025-10-31** | **31-DEC-2025〜** | **decimal (0.xxx)** |

### 変更ファイル

- `src/market/nse/xbrl.py` — 多タクソノミ対応 + pct 正規化 + metadata context 両対応
- `src/market/nse/constants.py` — `XBRL_SHP_NS_PATTERN` 追加
- `tests/market/nse/unit/test_xbrl.py` — 11 regression tests 追加 (52 tests total)
- `tests/market/nse/unit/test_constants.py` — `__all__` 数更新
- `tests/market/nse/fixtures/xbrl_sample_2025_05_31.xml` — 新 fixture
- `tests/market/nse/fixtures/xbrl_sample_2025_10_31.xml` — 新 fixture
- `notebook/NSE/nse_full_download.ipynb` — Phase 3/4 並列化 + MAX バグ修正 + promoter 絞り込み

### コミット履歴

- `8f05fe8` chore(nse): notebook 改善と ipywidgets 追加で tqdm.notebook のエラーを解消
- `6fc7afc` chore(nse): NSE index SQLite DB を追跡対象に追加
- `8dc37e3` fix(nse): BSE XBRL タクソノミ 2025-10-31 対応と Phase 4 並列化/レジューム
- `945dfaf` test(nse): 2025-05-31/2025-10-31 XBRL fixture + 未知タクソノミ警告機構を追加

### メモリ保存

`~/.claude/projects/-Users-yukihata-Desktop-quants/memory/feedback_bse_xbrl_taxonomy_transitions.md` に BSE タクソノミ遷移・小数フォーマット仕様・SQLite MAX 罠の知見を永続化。
