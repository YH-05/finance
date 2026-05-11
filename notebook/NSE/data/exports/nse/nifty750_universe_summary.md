# NIFTY 750 Universe Summary (NSE Owner Extraction)

**生成元**: act-2026-05-07-002 (build_nifty750_universe.py)
**入力**: owner_review_sheet.csv (yaml v0.5.1)
**対象**: 全 800 銘柄 (NIFTY 750 + rev1 補完 50 銘柄)

## 全体サマリー

| 区分 | 銘柄数 | 比率 |
|---|---|---|
| OWNER | 600 | 75.0% |
| NOT_OWNER | 200 | 25.0% |
| 合計 | 800 | 100.0% |

## Index level 別 OWNER 比率

| Index | 帰属銘柄数 | OWNER 数 | OWNER 比率 |
|---|---|---|---|
| NIFTY 50 | 44 | 27 | 61.4% |
| NIFTY 100 | 94 | 52 | 55.3% |
| NIFTY 200 | 184 | 109 | 59.2% |
| NIFTY 500 | 468 | 311 | 66.5% |
| NIFTY TOTAL MKT | 707 | 517 | 73.1% |
| (上記 5 index 圏外、rev1 補完銘柄) | 93 | 83 | 89.2% |

## OWNER family 別分布 (上位 20)

| Family | 銘柄数 |
|---|---|
| Jindal | 14 |
| Bajaj | 13 |
| Adani | 10 |
| Birla | 9 |
| Mahindra | 6 |
| Ambani | 6 |
| Goenka (RPSG) | 4 |
| Vedanta | 3 |
| Rai Gupta (Havells) | 3 |
| Mittal | 3 |
| Wadia | 3 |
| Karnavati / Searles | 2 |
| Hinduja | 2 |
| Kedaara Capital (PE-backed) | 2 |
| Lodha | 2 |
| Malhotra (Aegis) | 2 |
| Patanjali | 1 |
| Bandhan (Ghosh) | 1 |
| Thapar | 1 |
| Shriram | 1 |

**family 未取得 OWNER**: 499 件 (yaml owner_keywords 未マッチで Tier 1 自然人 promoter ベースで OWNER 判定された銘柄)

## 利用例

```python
import pandas as pd

# 全 universe (800 銘柄) を読み込み
df = pd.read_csv("notebook/NSE/data/exports/nse/nifty750_universe.csv")

# OWNER 企業のみフィルタ (= owner_companies.csv 相当)
owners = df[df["is_owner_company"]]

# NIFTY 100 圏内 OWNER 企業のみ
large_owners = df[df["is_owner_company"] & df["is_nifty100"]]

# 特定 family の銘柄を抽出 (Adani グループ)
adani = df[df["owner_family"].fillna("").str.contains("Adani")]
```
