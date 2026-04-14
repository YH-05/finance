# 議論メモ: NSE Phase 4 完了 + DB 破損復旧 + FK バグ修正 + Unknown 解消

**日付**: 2026-04-14
**議論ID**: disc-2026-04-14-nse-phase4-completion
**参加**: ユーザー + AI
**関連コミット**: `174285e..2f0ab22` (main, +4 commits since previous discussion save)

## 背景・コンテキスト

前回セッション（`disc-2026-04-14-nse-xbrl-taxonomy-fix`）で Phase 4 の並列化とタクソノミ対応を実装。その後 Jupyter で Phase 4 を実行したところ、以下の連鎖障害が発生:

1. Phase 3 の WARNING: `CHENNPETRO: 割合値が範囲外 (promoter=6729.0, public=3271.0)` — NSE API が稀に pct を percent×100 形式で返す仕様バグ
2. Phase 4 実行中に `IntegrityError: FOREIGN KEY constraint failed` — parser が XBRL 内部の Symbol 値を FK に使用していた
3. ロールバック時に SQLite DB 破損（`integrity_check` で tree 8 page 2360+ btreeInitPage error）→ Phase 3 の 750 銘柄データ大量ロスト
4. Phase 4 完了後、`shareholding_detail` に Unknown カテゴリ 420 行が発生 — 2025-10-31 taxonomy の追加 axis/member 名が未マップ

## 議論のサマリー

### pct 正規化（ルールベース対処）

CHENNPETRO の警告を契機に、NSE API が散発的に pct を percent×100 (6729)
や ratio (0.6729) で返す仕様を発見。`CorporateShareHolding.to_normalized_pcts()`
を新規実装し、promoter + public + employee_trust の合計値から格納形式を
推定して自動スケーリング（sum ≈ 100 / 10000 / 1 / unknown の 4 区分）。
ライブラリ層実装により future consumer 全てが恩恵。

### Phase 4 FK 違反バグ

`_result.symbol` は XBRL 内部の Symbol タグ値で、BSE 形式や空文字の場合があり
`stocks` テーブルと FK 不整合を起こす。クエリ由来の `_sym`（NSE symbol）に
変更して FK を確実に満たすように修正。

### DB 破損からの復旧

`sqlite3 .recover` で抽出成功:
- stocks: 2794 (無傷)
- index_members: 9153 (無傷)
- shareholdings: 40,624 → **523** に欠損（tree 8 ページが壊滅的に破損）
- shareholding_detail: 8670 の partial data は FK 違反込みだったため TRUNCATE

Phase 3 を再実行（~15 分）後、修正版の Phase 4 を実行。

### Phase 4 完了結果

- shareholdings: 40,634 行 / 758 銘柄
- shareholding_detail: 53,893 行 / 713 銘柄
- Phase 3 ↔ Phase 4 整合性: **713/713 銘柄で promoter_pct が完全一致**
- Unknown カテゴリ: 420 行（pattern 検出 → 追加マッピングで解消）

### 追加マッピング（104 members + 56 axes）

新 2025-10-31 taxonomy で発見された:
- Axis +8 件（`PersonsInConcertForPublic`, `GovernmentsAxis`（末尾s）, `CorporateWhereCentral...`, `NBFCsRegisteredWithRBIAxis`, `Trusts...Is...Axis`, `RelativesOfPromotersAxis`, `OtherInstitutionsAxis`, `InstitutionsForeignPortfolioInvestorAxis`）
- Member +9 件（`PersonsActingInConcertForPublic`, `OtherInstitutions`, `Institutions`, `IndividualShareholdersHolding...UpTo/InExcessOfRsTwoLakh`, `InstitutionsForeignPortfolioInvestor`, `FinancialInstitutionOrBanks`, `EmployeeTrusts`, `CentralGovernment...OrPresidentOfIndia`）

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-14-009 | pct 正規化は **ライブラリ層**（`CorporateShareHolding.to_normalized_pcts()`）で実装 | future consumer 全てが恩恵を受ける。既存 `to_float_*` は非破壊で維持 |
| dec-2026-04-14-010 | sum ≈ 100 / 10000 / 1 の 4 区分で format を自動判定 | ルールベース。他のセンチネル（decimals 属性等）は format 判別に使えない |
| dec-2026-04-14-011 | Phase 4 の FK には XBRL 内部の `_result.symbol` ではなく**クエリ由来の `_sym`** を使用 | `_sym` は `stocks` JOIN 経由で得られ FK を確実に満たす |
| dec-2026-04-14-012 | DB 破損時は `sqlite3 .recover` で salvage + Phase 3 から再構築 | 1 次復旧 15 分、`/tmp/nse_corrupt.db` に破損版を保持 |
| dec-2026-04-14-013 | Unknown カテゴリは旧パーサー時代の artifact として**データロスなしと判定**し即時削除しない | `Total` 行 100% で data integrity は確認済み。再実行したい場合のみ該当 symbol を DELETE |
| dec-2026-04-14-014 | 将来の新 taxonomy revision は `_VERIFIED_TAXONOMIES` と WARNING ログで運用者に通知 | 自動補正は silent にしない |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-14-008 | （完了）pct 正規化を library 実装 | 高 | ✅ 完了 (`174285e`) |
| act-2026-04-14-009 | （完了）Phase 4 FK バグ修正 + DB 復旧 | 高 | ✅ 完了 (`eb8520c`) |
| act-2026-04-14-010 | （完了）2025-10-31 追加 axis/member マッピング | 高 | ✅ 完了 (`2f0ab22`) |
| act-2026-04-14-011 | 既存の Unknown 420 行を cleanup したい場合のみ: 該当 symbol を DELETE + Phase 4 レジューム再実行 | 低 | 任意 |
| act-2026-04-14-012 | DB (`nse_index.db`, 現 7MB 想定) を main に commit | 中 | 待機 |
| act-2026-04-14-013 | ABBOTINDIA / BAYERCROP の Phase 3 個別再実行（latest=31-DEC-2018 問題） | 低 | 任意 |
| act-2026-04-14-014 | Docker / Neo4j 起動後に本議論メモ + 前回メモを Neo4j に MERGE 保存 | 低 | 待機 |
| act-2026-04-14-015 | Phase 4 の re-run 時に Jupyter 同時アクセスを避ける運用ルールをドキュメント化（破損再発防止） | 中 | 待機 |

### Unknown クリーンアップ用 SQL (act-2026-04-14-011)

```sql
-- Unknown 含む銘柄を抽出
SELECT DISTINCT symbol FROM shareholding_detail WHERE category='Unknown';

-- 削除してレジューム再実行で正しいカテゴリに
DELETE FROM shareholding_detail
WHERE symbol IN (
    SELECT DISTINCT symbol FROM shareholding_detail WHERE category='Unknown'
);
-- Jupyter カーネル再起動 → Phase 4 実行で自動再取得
```

## 次回の議論トピック

- DB サイズ増加（1.4MB → 7MB+）のバージョン管理方針（LFS 検討 / snapshot 戦略）
- Phase 3/4 実行前後の `.backup` スナップショット機構（破損再発防止）
- BSE 次期 taxonomy（2026-xx-xx 仮）リリース時の早期検知・対応体制
- shareholding_detail の分析用途（機関投資家ランキング、FII 動向トラッキング等）

## 参考情報

### 累計コミット（本 session）
1. `174285e` feat(nse): to_normalized_pcts で pct 形式を自動正規化
2. `eb8520c` fix(nse): Phase 4 FK 違反バグ + SQLite DB 破損からの復旧
3. `2f0ab22` fix(nse): 2025-10-31 tax. の axis/member 追加マッピング

### テストカバレッジ
- `src/market/nse/types.py`: 6 新 tests (percent/x100/ratio/unknown/empty)
- `src/market/nse/xbrl.py`: 既存 52 tests 全通過、counts 更新
- 合計 **586 tests pass**

### DB 統計（最終）
| テーブル | 行数 | 銘柄数 |
|---|---|---|
| stocks | 2,794 | 2,794 |
| index_members | 9,153 | 1,364 |
| shareholdings | 40,634 | 758 |
| shareholding_detail | 53,893 | 713 |

### 残 Unknown の分布（マッピング追加前 → 追加後の予測）
- 追加前: 420 行 / 10+ distinct sub_category
- 追加後（次回 Phase 4 実行時）: 0 行想定
- 既存 DB の Unknown はマッピング追加前データなので残存（データ自体は正常）

### BSE SHP タクソノミ遷移マップ（確定版）

| Revision | 採用四半期 | pct 形式 | parser 対応状況 |
|---|---|---|---|
| 2018-03-31 | 超旧 filing | percentage | ✅ エイリアス経由 |
| 2022-09-30 | 〜31-MAR-2025 | percentage | ✅ canonical |
| 2025-05-31 | 30-JUN-2025〜30-SEP-2025 | percentage | ✅ エイリアス経由 |
| 2025-10-31 | 31-DEC-2025〜 | **decimal (0.xxx)** | ✅ auto ×100 scaling |

### Memory 保存

`~/.claude/projects/-Users-yukihata-Desktop-quants/memory/feedback_bse_xbrl_taxonomy_transitions.md` は既存。本議論の追加知見（pct ×100 NSE API バグ、FK に `_sym` 使用、DB 破損 `.recover` 手順）は今後の類似セッションで自動参照される。
