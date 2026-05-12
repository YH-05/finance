# 議論メモ: NSE オーナー企業ラベリング rev1 再実行 (rev2 廃止 + 漏れ 55 銘柄統合)

**日付**: 2026-05-12
**議論ID**: `disc-2026-05-12-nse-owner-rev1-rerun`
**前回議論**: `disc-2026-05-07-nse-owner-labeling-completion-plan`
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)
**関連メモリ**: `project_nse_owner_analysis_2026_04_17`, `feedback_nse_universe_is_nifty750`

## 背景・コンテキスト

ユーザーが `notebook/NSE/data/cache/nse/owners_rev1.json` を `owners_rev2.json` に更新したと報告。
SAMMAAN CAPITAL が `nifty750_universe.csv` (800 銘柄) に含まれていないと指摘し、rev2 + NIFTY750 の和集合で再ラベリングを要請。

## 議論のサマリー

### 初期診断

```
rev1: 632 ISIN  /  rev2: 632 ISIN
追加 0 / 削除 0 / カテゴリ変更 0 / 企業名変更 0
normalize 後 SHA256 一致 → 差分はインデント等のフォーマットのみ
```

SAMMAAN (INE148I01020) は **rev1 にも元から含まれていた**。
真の問題は `build_owner_review_sheet.py` の **LEFT MERGE ロジック**:

```python
merged = cand.merge(rev1, on="isin", how="left")
```

`owner_candidates.csv` (787 銘柄、NSE Phase 3/4 取得済み) に LEFT MERGE するため、
rev1 にあるが NSE 取得側で漏れた 55 銘柄 (SAMMAAN 含む) が universe から欠落していた。

### ユーザー方針

1. rev2 は trash に移動 (rev1 と完全一致のため)
2. NSE から再取得してフル分類 (推奨)
3. 取得失敗・解決不能銘柄は rev1 ラベルだけで universe に追加 + 識別ラベル付与

### 実行結果

| Phase | 内容 | 結果 |
|-------|------|------|
| 0 | rev2 → trash/ + 廃止経緯ドキュメント | 完了 (`docs/plan/2026-05-12_obsolete-owners_rev2.md`) |
| 1 | 漏れ銘柄 55 件 export | 完了 (`rev1_missing_from_universe.csv`: 38 resolvable / 17 unresolvable) |
| 2-3 | refetch_rev1_missing.py 作成 + 38 銘柄を NSE 再取得 | Phase 3: 38/38 OK, Phase 4: 37/38 OK (BSE のみ XBRL namespace mismatch) |
| 4 | persist_rev1_missing.py で永続化 + 分類 | owner_candidates.csv: 787 → 855 行 |
| 5 | build_owner_review_sheet.py 再実行 | owner_review_sheet.csv: 855 行 |
| 6 | build_nifty750_universe.py 再実行 | nifty750_universe.csv: 800 → 855 銘柄 |
| 7 | 検証 + 差分レポート | rev1 ∩ universe: 100%, Precision 93.4% / Recall 100% / F1 96.6% |

## 主要メトリクス比較

| 項目 | 旧版 (2026-05-07) | 新版 (2026-05-12) |
|------|------------------|------------------|
| 総銘柄数 | 800 | 855 (+55) |
| OWNER 銘柄数 | 600 | 614 (+14) |
| rev1 ∩ universe | 577/632 (91.3%) | **632/632 (100.0%)** |
| TP | 410 | 424 |
| FP | 3 | 30 |
| FN | 0 | 0 |
| Precision | 99.3% | 93.4% |
| Recall | 100% | 100% |
| F1 | 99.6% | 96.6% |

## 残課題 (フォローアップ)

### SAMMAANCAP の Tier 2 副作用 ※後続で解決

- rev1=Owner、Phase 4 取得成功 (as_on=2026-03-31)
- promoter_total=0.0%, dir_pct=0.36% のみ
- `owner_flag=owner_confirmed_director_only` + `yaml_classification=UNKNOWN`
- hybrid 後 `OWNER_WEAK` → `is_owner_company=False`

**追加調査結果 (2026-05-12 後段)**: Web リサーチで rev1=Owner が誤りと判明:
- 2023.02 NSE/BSE が de-promoterization 正式承認
- Sammaan Capital 公式 ARFY2024-25: "board-run, professionally managed"
- 機械判定 OWNER_WEAK → is_owner_company=False は **実態 (Professional) と一致**
- act-2026-05-12-005 は **withdrawn** に変更

### director_only ルール副作用 (既知問題の拡大)

旧版で FP=3 だったが新版で FP=30 に増加。原因: HDFCBANK, ICICIBANK, ITC, LT 等の Professional 系大企業が `owner_confirmed_director_only` flag を持つため、hybrid 後 OWNER_WEAK となり Recall 計算上は予測 Owner に分類される。
universe レベルでは `is_owner_company=False` で正しいが、Precision 数値上悪化。
既存 `act-2026-04-17-006` の厳格化 (`dir_pct+kmp_pct >= 1%`) で大幅改善見込み。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-12-001 | owners_rev2.json を廃止し trash/ に移動。rev1 を一次データとして維持 | rev2 は rev1 と内容上完全一致（normalize 後 SHA256 一致）のため別ファイル維持不要 |
| dec-2026-05-12-002 | rev1 圏内 632 銘柄を 100% universe に統合する方針を確立。NSE 再取得可能な 38 銘柄は Phase 3/4 を実行、解決不能 17 銘柄 + Phase 4 失敗 1 銘柄 (BSE) は rev1 ラベル流用 | LEFT MERGE バグで 55 銘柄が universe から欠落していた。SAMMAAN 等の重要銘柄を含めるため再取得 + ラベル流用 |
| dec-2026-05-12-003 | owner_candidates.csv と nifty750_universe.csv に `nse_fetch_status` カラムを追加 (`ok` / `phase4_failed_xbrl` / `unresolvable_isin`) | データ品質を識別可能にし、投資戦略側で NSE メタ完備銘柄のみ抽出可能にする |
| dec-2026-05-12-004 | SAMMAANCAP の Tier 2 director_only 副作用は本セッションのスコープ外 → フォローアップタスクとして記録 | 修正は director_only ルール全体の厳格化（act-2026-04-17-006）と統合すべき問題のため切り出し |
| dec-2026-05-12-005 | rev1 ラベルは人間チーム手動ラベルとして保護し、AI 判定で訂正したラベルは別ファイル `owners_rev1_ai-judge.json` で管理する | Pattern B 8 銘柄リサーチに基づき 2 件のラベル修正を確定 (SAMMAAN/TICL)。rev1 を上書きせず ai-judge 版を分離管理 |
| dec-2026-05-12-006 | rev1 圏外 223 銘柄の AI レビューは Z5 (hufi 1-5% + yaml=UNKNOWN) 15 銘柄に絞り込む (ROI 観点) | rev1 圏内検証で誤判定の 80% は Z1 (director_only + UNKNOWN) に集中。Z5 は誤判定率 2.3% で AI 修正の期待値最大。Z2/Z3/Z4/Z6 は誤判定率 0% で AI 不要 |

## Pattern B + Z5 リサーチ結果 (2026-05-12 後段)

### Pattern B 8 銘柄リサーチ (rev1 圏内 機械=OWNER vs rev1≠Owner)

Web リサーチ (tavily) で人間判定 vs 機械判定の不一致 8 銘柄を検証:

| 銘柄 | rev1 | リサーチ結論 | 最終 |
|------|------|------------|------|
| SAMMAANCAP | Owner | de-promoterized 2023、Banga プロ経営 | **Owner → Professional 修正** |
| TICL | Professional | Upendra Singh + Tantia 公式 promoter group、hufi 57% | **Professional → Owner 修正** |
| INFY | Professional | Murthy family promoter 維持だが Parekh CEO (2018-外部) | rev1 維持 ✓ |
| STARHEALTH | Professional | Westbridge PE 主導 + Jhunjhunwala estate passive | rev1 維持 ✓ |
| KARURVYSYA | Professional | 銀行 26% 上限制約、Suriyanarayana 2% のみ | rev1 維持 ✓ |
| GOKEX | Professional | Blackstone exit 2017、Florintree (PE) + 雇用 CEO | rev1 維持 ✓ |
| KSB | MNC | KSB SE Germany 40.5% 親会社主導 | rev1 維持 ✓ |
| UBL | MNC | Heineken Netherlands 61.5% 支配 | rev1 維持 ✓ |

### Z5 AI 判定 (rev1 圏外 hufi 1-5% 15 銘柄)

機械判定の誤判定率を信頼度別に分類した結果、**Z5 (hufi 1-5% + yaml=UNKNOWN)** が rev1 圏内で 2.3% 誤判定 (INFY 型) → 圏外 15 銘柄を AI 判定:

- **機械判定一致**: 13 件
- **機械判定不一致**: 2 件
  - INDIASHLTR: WestBridge + Aravali PE 主導、創業者 Mehta は 1.45% Chairman、雇用 CEO → **Professional**
  - WABAG: 2005 MBO で独立、Rajiv Mittal は元従業員 (management-led) → **Professional**

### 最終成果物 (855 銘柄 universe ラベル付け)

| ファイル | 内容 |
|---------|------|
| `notebook/NSE/data/cache/nse/owners_universe_ai-judge.json` | universe 全 855 銘柄のラベル (rev1 schema 互換) |
| `notebook/NSE/data/cache/nse/owners_universe_ai-judge.csv` | 同上 + `label_source` + `reasoning` 列 |
| `notebook/NSE/data/cache/nse/owners_universe_ai-judge_corrections.csv` | 累積修正履歴 4 件 |
| `notebook/NSE/data/cache/nse/owners_rev1_ai-judge.json/csv` | rev1 (632) ベース版 |

**累積修正 4 件**: SAMMAANCAP / TICL (rev1 ラベル誤り) + INDIASHLTR / WABAG (機械判定誤り)

**最終カテゴリ分布**: Owner 607 (71.0%) / Professional 116 (13.6%) / State 85 (9.9%) / MNC 45 (5.3%) + 軽微な誤記 2 (rev1 元データ、修正不要として保留)

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|------------|
| act-2026-05-12-001 | refetch_rev1_missing.py 汎用化スクリプト作成 + 38 銘柄再取得 | 高 | **completed** |
| act-2026-05-12-002 | persist_rev1_missing.py 汎用化スクリプト作成 + 永続化/分類 | 高 | **completed** |
| act-2026-05-12-003 | rev1_unresolvable_resolution.md / rev1_unresolvable_resolution.csv 作成 (17 銘柄の根拠データ) | 中 | **completed** |
| act-2026-05-12-004 | rev1_rerun_diff_report.md 作成 (差分レポート + メトリクス比較) | 中 | **completed** |
| act-2026-05-12-005 | ~~SAMMAANCAP の Tier 2 副作用修正~~ | - | **withdrawn** (rev1=Owner が誤りと判明、機械判定が実態と一致) |
| act-2026-05-12-008 | rev1 ラベル 2 件修正 + owners_rev1_ai-judge.json/csv 出力 | 高 | **completed** |
| act-2026-05-12-009 | Z5 15 銘柄 AI 判定 + universe 全体 ai-judge ファイル統合 | 中 | **completed** |
| act-2026-05-12-010 | 上司向けオーナー企業ラベリング説明書作成 (`notebook/NSE/docs/owner_labeling_methodology.md`、605 行、16 章) | 高 | **completed** |
| act-2026-05-12-006 | MCX の Phase 4 再取得 (現在 2018-12-31 の古いデータで natural_pct=0、excluded_no_natural_no_holding 誤判定) | 低 | pending |
| act-2026-05-12-007 | BSE の XBRL parser 拡張 (BSE 自社 taxonomy 対応) | 低 | pending |
| act-2026-04-17-006 (既存) | director_only ルール厳格化 (`dir_pct+kmp_pct >= 1%`) | 中 | pending (本セッション結果で FP=30 に増加、優先度上昇) |

## 次回の議論トピック

- `act-2026-05-12-005` の SAMMAANCAP 修正方針 (rev1 hint ルール追加 vs `act-2026-04-17-006` 厳格化と統合)
- 名称変更後の銘柄（Indiabulls Housing → Sammaan Capital 等）の取り扱い
- universe 完成の判定基準（Precision/Recall 維持 + すべての rev1 銘柄が is_owner_company で一貫しているか）

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-12-nse-owner-rev1-rerun`
  - Decision: `dec-2026-05-12-001` 〜 `dec-2026-05-12-004` (4 件)
  - ActionItem: `act-2026-05-12-001` 〜 `act-2026-05-12-007` (7 件)
  - リレーション: `(curr)-[:FOLLOWS]->(disc-2026-05-07)`, `(disc)-[:RESULTED_IN]->(dec×4)`, `(disc)-[:PRODUCED]->(act×7)`, `(project-106)-[:HAS_DISCUSSION]->(disc)`
- **ドキュメント**: 本ファイル + `2026-05-12_obsolete-owners_rev2.md`
- **データ成果物**:
  - `notebook/NSE/data/exports/nse/nifty750_universe.csv` (855 銘柄、nse_fetch_status 付き)
  - `notebook/NSE/data/exports/nse/owner_candidates.csv` (855 行)
  - `notebook/NSE/data/exports/nse/rev1_missing_from_universe.csv`
  - `notebook/NSE/data/exports/nse/rev1_unresolvable_resolution.csv`
  - `notebook/NSE/data/exports/nse/rev1_unresolvable_resolution.md`
  - `notebook/NSE/data/exports/nse/rev1_rerun_diff_report.md`
  - `notebook/NSE/data/exports/nse/refetch_rev1_log.json`
  - `notebook/NSE/data/exports/nse/persist_rev1_log.json`
- **スクリプト**:
  - `notebook/NSE/scripts/refetch_rev1_missing.py`
  - `notebook/NSE/scripts/persist_rev1_missing.py`
