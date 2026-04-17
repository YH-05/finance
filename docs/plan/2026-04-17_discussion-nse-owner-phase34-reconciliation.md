# 議論メモ: NSE Phase 3/4 完了 + AI 結果復旧 + owners.json 照合

**日付**: 2026-04-17
**議論ID**: `disc-2026-04-17-nse-owner-phase34-reconciliation`
**前回議論**: `disc-2026-04-17-nse-owner-analysis-impl`
**関連プロジェクト**: project-106 (NSE パッケージ拡張)

## 背景・コンテキスト

朝のセッション (`disc-2026-04-17-nse-owner-analysis-impl`) で `nse_owner_analysis.ipynb` と AI 判定を完成させた後、残アクション `act-2026-04-17-001` (Phase 3/4 で +75 銘柄取得) と `act-2026-04-17-003` (Jupyter 正式実行 + owners.json 照合) を実行。実行中に想定外のデータ消失事故が発生し、緊急救済を経て最終検証まで到達。

## 議論のサマリー

### Phase 3/4 実行 (act-2026-04-17-001)

`nse_full_download.ipynb` を Jupyter で実行。`PHASE3_EXTRA_OWNERS_JSON` パッチで owners.json の Owner ラベル銘柄（NIFTY TOTAL MKT 未所属）を追加 Union。

**結果**:
- `shareholdings`: 40,634 行 / 758 銘柄 → **44,546 行 / 833 銘柄** (+75)
- `shareholding_detail`: 53,893 行 / 713 銘柄 → **57,820 行 / 787 銘柄** (+74)

### データ消失事故と救済

`nse_owner_analysis.ipynb` の Section 4 まで実行した結果、`owner_candidates.csv` の AI 判定 49 件が上書き消失。

**原因**:
- Section 1 の CSV 退避対象は `shareholdings.csv` と `shareholding_detail.csv` のみ
- Section 3 Cell 14 で `feat["owner_flag_ai"] = ""` により新 CSV の AI 結果列が空初期化
- Section 3 Cell 15 で CSV 上書き保存 → 旧 AI 結果は消失
- Section 4 Cell 16 実行で `owner_flag_final` も再計算されるが、AI 結果空のため Tier 2/3 が PENDING_AI_REVIEW に

**救済**:
- コミット `f757f94` に旧 CSV が無傷で残存
- `git show f757f94:notebook/NSE/data/exports/nse/owner_candidates.csv` で 601 銘柄分を復元
- 49 件の AI 判定を symbol キーで新 CSV (787 銘柄) に merge → 全件復元成功
- 残 PENDING は 9 件のみ（75 追加銘柄由来の新規発生分）

### 残 PENDING 9 件の追加 AI 判定

個別調査に基づき分類:

| Symbol | 会社 | AI 判定 | conf | 根拠 |
|---|---|---|---:|---|
| ABBOTINDIA | Abbott India | `ai_mnc` | 0.98 | Abbott Laboratories (USA) 子会社 |
| BAYERCROP | Bayer Cropscience | `ai_mnc` | 0.98 | Bayer AG (独) 子会社 |
| FUSION | Fusion Finance | `ai_owner` | 0.80 | Sachdev 家創業 + HUF/Family Trust |
| GSPL | Gujarat State Petronet | `ai_state` | 0.99 | Gujarat 州政府系 (GSPC+GUVNL) |
| PDSL | PDS Limited | `ai_owner` | 0.95 | Seth 家 NRI ファミリー nri=61.37% |
| SMLMAH | SML Mahindra | `ai_owner` | 0.75 | Mahindra Group 傘下 |
| SPANDANA | Spandana Sphoorty | `ai_professional` | 0.95 | Kedaara Capital (PE) 支配、創業家退出 |
| SULA | Sula Vineyards | `ai_owner` | 0.98 | Rajeev Samant 創業家 + Rasa Trust |
| VEDL | Vedanta | `ai_owner` | 0.95 | Anil Agarwal 一族 (hufi=4 + Trust) |

### 最終分布 (787 銘柄)

| owner_flag_final | 件数 | 前回比 (601 銘柄時点) |
|---|---:|---:|
| OWNER | 638 | +115 |
| OWNER_WEAK | 6 | ±0 |
| NOT_OWNER | 143 | +71 |
| PENDING_AI_REVIEW | 0 | -0 |

AI 判定累計 58 件: ai_owner 20 / ai_mnc 17 / ai_professional 10 / ai_owner_weak 6 / ai_state 5

### owners.json 照合 (act-2026-04-17-003)

ISIN→symbol 解決 595/611 (未解決 16 = 上場廃止・統合銘柄)、候補内 546 銘柄で精度検証。

**精度指標**:

| 指標 | 値 |
|---|---:|
| Recall (strict) | **97.7%** (388/397) |
| Recall (incl. OWNER_WEAK) | 98.7% (392/397) |
| Precision (strict) | **90.2%** (388/430) |
| F1 (strict) | **93.8%** |

**Confusion Matrix**:

| owners.json \ 予測 | NOT_OWNER | OWNER | OWNER_WEAK | 計 |
|---|---:|---:|---:|---:|
| Owner | 5 | 388 | 4 | 397 |
| MNC | 31 | 6 | 0 | 37 |
| State | 70 | 8 | 0 | 78 |
| Professional | 6 | 28 | 0 | 34 |

**不一致 (A) Owner → NOT_OWNER/OWNER_WEAK 9 件**:
- HINDZINC (state_dominant 除外), ASHOKLEY (holding 漏れ) — ルール改善対象
- SPANDANA (ai_professional) / GLAND / ROUTE (ai_mnc) — 私の判定と owners.json の乖離

**不一致 (B) 非Owner → OWNER 42 件** (Precision 劣化の主犯):
- **全 42 件が `owner_confirmed_director_only` 起因**
- Tata Group 10, 金融 11, State 5, MNC 6, その他 Professional 10
- Director/KMP の名目 1 株保有で誤 OWNER 判定

### owners.json Owner 428 → 照合対象 397 の差分トラッキング

31 件減少の内訳を完全特定:

| ステップ | 残数 | 減少 | 原因 |
|---|---:|---:|---|
| raw Category='Owner' | 428 | — | 起点 |
| ISIN あり | 410 | **-18** | owners.json の ISIN 欄が空 |
| symbol 解決済み | 402 | -8 | 上場廃止・合併・REIT |
| 候補内（照合対象） | **397** | -5 | 事前除外（4 件は低 promoter、1 件は XBRL 取得失敗） |

**ISIN 欠損 18 件**:
JINDAL STEEL, CENTURY TEXTILES, INDIABULLS REAL ESTATE, INDIABULLS HOUSING, GMR INFRA, INFIBEAM, AMARA RAJA, AEGIS LOGISTICS, ADANI TRANSMISSION, ADANI WILMAR, GLENMARK LIFE SCIENCES, AMI ORGANICS, WELSPUN INDIA, MAHINDRA LIFESPACE, SWAN ENERGY, HBL POWER, LT FOODS, D B REALTY → owners.json 側メンテナンス漏れ。補完必要

**ISIN 解決不能 8 件**:
DHANI SERVICES, FUTURE RETAIL, PIRAMAL ENTERPRISES, TV18 BROADCAST, TCNS CLOTHING, JAIPRAKASH ASSOCIATES（上場廃止）+ MINDSPACE REIT, EMBASSY OFFICE PARKS REIT（REIT） → 放置可

**候補外 5 件**:
MFSL (1.25%), ZEEL (3.99%), DISHTV (4.04%), ASTRAMICRO (6.54%) → 正当な低 promoter 除外。**360ONE (14.2%)** → Phase 4 XBRL 取得失敗で detail_rows=0、別バグ

### 再発防止: Section 1 退避パッチ

`nse_owner_analysis.ipynb` Cell 4 を修正し `owner_candidates.csv` を退避対象に追加:

```python
for name in ["shareholdings.csv", "shareholding_detail.csv", "owner_candidates.csv"]:
```

ただし Section 3 Cell 14 が `owner_flag_ai = ""` で再初期化するため、退避だけでは AI 結果は自動復元されない。完全再発防止には Section 3/4 に退避 CSV からの自動マージロジック追加が必要（act-2026-04-17-007）。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-17-008 | owner_candidates.csv の AI 判定消失時は git から旧 CSV を復元 + symbol キーマージで救済 | Section 3 Cell 14 で owner_flag_ai="" 再初期化により AI 結果が消える。git f757f94 コミットが唯一の復旧ソース |
| dec-2026-04-17-009 | owner_confirmed_director_only ルールは厳格化が必要（Precision 90.2% の主犯、FP 42 件全てが起因） | Tata Group / ICICI / HDFC / SBI 等で法人 promoter 配下の雇われ Director/KMP が名目 1 株保有で OWNER 確定される誤判定。閾値 dir_pct+kmp_pct≥1% or Tier 3 降格が候補 |
| dec-2026-04-17-010 | Section 1 の CSV 退避対象に owner_candidates.csv を追加（ロールバック用） | 退避するだけでは Section 3 の再初期化で AI 結果は消えるため完全対策ではないが、次回事故時の復旧ソースを手元に残す最小限の防御 |
| dec-2026-04-17-011 | 追加 AI 判定 9 件の分類結果を確定: ai_owner 5 / ai_mnc 2 / ai_state 1 / ai_professional 1 | FUSION/PDSL/SMLMAH/SULA/VEDL=ai_owner, ABBOTINDIA/BAYERCROP=ai_mnc, GSPL=ai_state, SPANDANA=ai_professional |
| dec-2026-04-17-012 | owners.json Owner 428 → 照合対象 397 の差分 31 件を完全トラッキング: ISIN 欠損 18 / ISIN 解決不能 8 / 候補外 5 | ISIN 欠損 18 件は owners.json 側メンテナンス漏れ。ISIN 解決不能 8 件は上場廃止・REIT で放置可。候補外 5 件のうち 4 件は正当な低 promoter 除外、1 件（360ONE）は Phase 4 XBRL 取得失敗による別バグ |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|----------|
| act-2026-04-17-006 | owner_confirmed_director_only ルール厳格化 (dir_pct+kmp_pct≥1% 等)。Precision 90.2→98%+ 目標 | 高 | pending |
| act-2026-04-17-007 | Section 3/4 に _owner_candidates.csv 自動マージロジック追加（完全再発防止） | 高 | pending |
| act-2026-04-17-008 | FN 5 件の個別再確認 (HINDZINC, ASHOKLEY, SPANDANA, GLAND, ROUTE) | 中 | pending |
| act-2026-04-17-009 | 候補外の owners=Owner 5 銘柄の調査 | 低 | pending |
| act-2026-04-17-010 | owners.json の ISIN 欠損 18 件補完（JINDAL STEEL, ADANI WILMAR 等）。stocks テーブル or NSE 公式 listing から ISIN を補完し PHASE3_EXTRA_OWNERS_JSON に反映 | 中 | pending |
| act-2026-04-17-011 | 360ONE の Phase 4 XBRL 取得失敗調査。promoter=14.2% (>10%) なのに detail_rows=0。xbrl_url NULL or fetch エラー検証 + 個別再取得 | 低 | pending |

## 前回 ActionItem の更新

| ID | 内容 | 新ステータス |
|----|------|------------|
| act-2026-04-17-001 | Phase 3/4 実行 | **done** (+75 銘柄取得、DB 787 銘柄) |
| act-2026-04-17-003 | Jupyter 正式実行 + owners.json 照合 | **done** (Recall 97.7%, Precision 90.2%) |
| act-2026-04-17-002 | Board Composition API 調査 | pending |
| act-2026-04-17-004 | OWNER_WEAK 6 銘柄の上司確認 | pending |
| act-2026-04-17-005 | commit + push | pending |

## 成果物

- `notebook/NSE/nse_owner_analysis.ipynb` — Cell 4 退避対象に owner_candidates.csv 追加
- `notebook/NSE/data/exports/nse/owner_candidates.csv` — 787 銘柄 × 30 列 (AI 58 件、PENDING=0)
- `notebook/NSE/data/exports/nse/owners_reconciliation.csv` — owners.json 照合レポート 546 行
- `notebook/NSE/data/exports/nse/shareholdings.csv` — 44,546 行
- `notebook/NSE/data/exports/nse/shareholding_detail.csv` — 57,820 行
- `/tmp/owner_candidates_old.csv` — git f757f94 時点の旧 CSV (601 銘柄、AI 49 件)
- `/tmp/owner_candidates_new_backup.csv` — Section 4 実行直後の状態 (787 銘柄、AI 0 件)

## 次回の議論トピック

- act-2026-04-17-006: `director_only` ルール厳格化の閾値設計（dir_pct+kmp_pct≥1% vs Tier 3 降格の比較）
- act-2026-04-17-007: Section 3/4 マージロジック実装設計（退避ファイル検出 → AI 結果 merge）
- act-2026-04-17-008: FN 5 件の個別調査（SPANDANA/GLAND/ROUTE は AI 判定 vs owners.json の乖離調整）
- OWNER_WEAK 6 銘柄の最終方針（上司判定）

## 保存先

- **Neo4j**: Discussion `disc-2026-04-17-nse-owner-phase34-reconciliation` + Decision ×4 + ActionItem ×4
- **ドキュメント**: `docs/plan/2026-04-17_discussion-nse-owner-phase34-reconciliation.md`
