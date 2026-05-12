# rev1 再ラベリング差分レポート (2026-05-12)

**生成元**: act-2026-05-12-004 (`disc-2026-05-12-nse-owner-rev1-rerun`)
**比較**: HEAD `nifty750_universe.csv` (800 銘柄) vs 新版 (855 銘柄)

## サマリー

| 項目 | 旧版 | 新版 | 差分 |
|------|------|------|------|
| 総銘柄数 | 800 | 855 | +55 |
| OWNER 銘柄数 | 600 | 614 | +14 |
| NOT_OWNER 銘柄数 | 200 | 241 | +41 |
| rev1 ∩ universe | 577 / 632 (91.3%) | **632 / 632 (100.0%)** | 完了 |

## 評価メトリクス (rev1 GT)

| 段階 | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|--------|-----|
| 旧版 (2026-05-07) | 410 | 3 | 0 | 99.3% | 100.0% | 99.6% |
| **新版 (2026-05-12)** | **424** | **30** | **0** | **93.4%** | **100.0%** | **96.6%** |

**観察**: Recall 100% を維持しつつ FP が +27 件増加。原因は **Tier 2 director_only ルールの副作用**:
- 旧版: rev1 圏内のみ評価対象 → Tier 2 director_only の FP は少数
- 新版: 38 銘柄追加で HDFCBANK/ICICIBANK/ITC など Professional 系の director_only flag が新規 FP に
- これらは元から既知の問題（`act-2026-04-17-006`: director_only ルール厳格化案）

## nse_fetch_status 内訳

| status | 銘柄数 | 説明 |
|--------|--------|------|
| `ok` | 837 | Phase 3 + Phase 4 取得成功 |
| `phase4_failed_xbrl` | 1 | BSE (XBRL namespace mismatch) |
| `unresolvable_isin` | 17 | NSE stocks テーブルで symbol 解決不能 (REIT/M&A消滅/上場廃止) |

詳細: `rev1_unresolvable_resolution.md`

## 新規 55 銘柄の内訳

### rev1=Owner で is_owner_company=True (新規 OWNER カバレッジ)

NSE 取得済み 6 銘柄:
- ASTRAMICRO, DISHTV, GOKEX, KARURVYSYA, MFSL (passive), ZEEL

rev1 流用 8 銘柄:
- EMBASSY REIT, MINDSPACE REIT, PIRAMAL, DHANI, JAIPRAKASH, FUTURE RETAIL, TCNS, TV18

### rev1=Owner で is_owner_company=False (要確認)

**SAMMAANCAP (INE148I01020)**: 名称変更後 (Indiabulls Housing Finance → Sammaan Capital) で promoter_total=0.0%, dir_pct=0.36% のみ。`owner_flag=owner_confirmed_director_only` + `yaml_classification=UNKNOWN` → hybrid 後 `OWNER_WEAK` → `is_owner_company=False`。

→ rev1 では Owner ラベル付されているため不整合。**フォローアップ対象**（`act-2026-05-12-005`）。

### rev1=Professional / MNC / State (大企業群、is_owner=False が期待)

NSE 取得済み 31 銘柄: HDFCBANK, ICICIBANK, ITC, AXISBANK, YESBANK, LT, SWIGGY, BSE 等
- 大半は `owner_confirmed_director_only` で OWNER_WEAK → is_owner=False (期待通り、ただし FP に計上)
- AXISBANK, KTKBANK, SOUTHBANK, YESBANK は `excluded_no_natural_no_holding` → is_owner=False (期待通り)
- MCX は as_on=2018-12-31 の古い四半期データで natural_pct=0 → `excluded_no_natural_no_holding` (要再取得)

### 未取得・解決不能 (rev1 流用、9 銘柄が NOT_OWNER 期待通り、6 銘柄が OWNER)

上記 `unresolvable_isin` 17 件 + BSE 1 件。詳細は `rev1_unresolvable_resolution.md`。

## 既知のフォローアップ課題

| ID | 内容 | 優先度 |
|----|------|--------|
| `act-2026-05-12-005` | SAMMAANCAP の Tier 2 副作用修正（rev1=Owner 一致なら OWNER 優先 or director_only 厳格化） | 中 |
| `act-2026-04-17-006` (既存) | director_only ルール厳格化 (`dir_pct+kmp_pct >= 1%` 等) → FP 30 件削減 | 中 |
| `act-2026-05-12-006` | MCX の Phase 4 再取得（2018 年データのため Tier 判定が不適切） | 低 |
| `act-2026-05-12-007` | BSE の XBRL parser を拡張（BSE 自社 taxonomy 対応） | 低 |

## 検証コマンド

```python
import pandas as pd
df = pd.read_csv("notebook/NSE/data/exports/nse/nifty750_universe.csv")

# rev1 GT カバレッジ
import json
rev1 = json.load(open("notebook/NSE/data/cache/nse/owners_rev1.json"))
rev1_isin = {e["isin"] for e in rev1}
print(f"rev1 ∩ universe: {len(rev1_isin & set(df['isin']))} / {len(rev1_isin)}")  # 632 / 632

# NSE 取得済みのみ
fully = df[df["nse_fetch_status"] == "ok"]
print(f"Fully resolved: {len(fully)}")  # 837

# rev1=Owner で universe is_owner=False (フォローアップ対象)
import pandas as pd
rev1_owner = {e["isin"] for e in rev1 if e["Category (Owner, MNC, State, Professional)"] == "Owner"}
suspect = df[df["isin"].isin(rev1_owner) & ~df["is_owner_company"]]
print(suspect[["symbol", "isin", "owner_flag", "nse_fetch_status"]])
```
