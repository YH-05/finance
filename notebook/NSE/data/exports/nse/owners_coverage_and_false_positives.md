# owners.json 取得可否 + 偽陽性レポート

**生成日時**: 2026-04-27T15:04:32
**対象**: `notebook/NSE/data/cache/nse/owners.json` (635 銘柄)
**取得済みデータ**: shareholdings.csv (833 銘柄) / shareholding_detail.csv (787 銘柄) / owner_candidates.csv (787 銘柄)

---

## 1. owners.json 全体カバレッジ

| ステータス | 件数 | 割合 | 説明 |
|---|---:|---:|---|
| fully_covered | 546 | 86.0% | shareholdings + detail + owner_candidates 全て取得済み |
| partially_covered | 38 | 6.0% | shareholdings のみ取得（XBRL detail 未取得） |
| not_collected | 11 | 1.7% | stocks に存在するが Phase 3/4 対象外 |
| isin_unresolved | 16 | 2.5% | stocks.csv に ISIN 該当なし（上場廃止・REIT 等） |
| isin_missing | 24 | 3.8% | owners.json 側で ISIN 欄が空 |
| **合計** | **635** | **100.0%** | — |

**実質取得率 (fully + partially)**: 584 / 635 = **92.0%**

---

## 2. Category 別カバレッジ

| Category | fully | partial | not_coll | isin_unres | isin_missing | 合計 | 取得率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Owner | 397 | 5 | 0 | 8 | 18 | 428 | 93.9% |
| MNC | 37 | 2 | 3 | 1 | 1 | 44 | 88.6% |
| State | 78 | 0 | 5 | 1 | 0 | 84 | 92.9% |
| Professional | 34 | 31 | 2 | 6 | 5 | 78 | 83.3% |
| abb | 0 | 0 | 1 | 0 | 0 | 1 | 0.0% |

---

## 3. Owner カテゴリの未取得・部分取得銘柄（owners.json Owner 428 件中）

### 3.1 partially_covered (5 件) — shareholdings 取得済 / XBRL detail 未取得

| Symbol | ISIN | 会社名 | shareholdings | detail | candidates |
|---|---|---|:---:|:---:|:---:|
| `MFSL` | INE180A01020 | MAX FINANCIAL SERVICES LTD | ✓ | — | — |
| `ZEEL` | INE256A01028 | ZEE ENTERTAINMENT ENTERPRISE | ✓ | — | — |
| `DISHTV` | INE836F01026 | DISH TV INDIA LTD | ✓ | — | — |
| `360ONE` | INE466L01038 | 360 ONE WAM LTD | ✓ | — | — |
| `ASTRAMICRO` | INE386C01029 | ASTRA MICROWAVE PRODUCTS LTD | ✓ | — | — |

### 3.2 not_collected (0 件)

該当なし — Owner カテゴリの全銘柄は stocks に存在し、Phase 3/4 の対象に含まれた。

### 3.3 isin_unresolved (8 件) — stocks.csv に ISIN 該当なし（上場廃止・REIT 等で取得不可）

| ISIN | 会社名 | 推定理由 |
|---|---|---|
| INE274G01010 | DHANI SERVICES LTD | 上場廃止 (DHANI SERVICES) |
| INE752P01024 | FUTURE RETAIL LTD | 上場廃止 (FUTURE RETAIL) |
| INE140A01024 | PIRAMAL ENTERPRISES LTD | 上場廃止/組織再編 (PIRAMAL ENTERPRISES) |
| INE886H01027 | TV18 BROADCAST LTD | 上場廃止 (TV18 BROADCAST) |
| INE0CCU25019 | MINDSPACE BUSINESS PARKS REI | REIT (MINDSPACE BUSINESS PARKS) |
| INE041025011 | EMBASSY OFFICE PARKS REIT | REIT (EMBASSY OFFICE PARKS) |
| INE778U01029 | TCNS CLOTHING CO LTD | 上場廃止 (TCNS CLOTHING) |
| INE455F01025 | JAIPRAKASH ASSOCIATES LTD | 上場廃止 (JAIPRAKASH ASSOCIATES) |

### 3.4 isin_missing (18 件) — owners.json 側 ISIN 欄が空（補完すれば取得可能）

| 会社名 |
|---|
| JINDAL STEEL & POWER LTD |
| CENTURY TEXTILES & INDS LTD |
| INDIABULLS REAL ESTATE LTD |
| INDIABULLS HOUSING FINANCE L |
| GMR INFRASTRUCTURE LTD |
| INFIBEAM AVENUES LTD |
| AMARA RAJA BATTERIES LTD |
| AEGIS LOGISTICS LTD |
| ADANI TRANSMISSION  LTD |
| ADANI WILMAR LTD |
| GLENMARK LIFE SCIENCES LTD |
| AMI ORGANICS LTD |
| WELSPUN INDIA LTD |
| MAHINDRA LIFESPACE DEVELOPER |
| SWAN ENERGY LTD |
| HBL POWER SYSTEMS LTD |
| LT FOODS LTD |
| D B REALTY LTD |

**合計 ISIN 由来の問題で取得不可**: 8 (unresolved) + 18 (missing) = **26 件**

---

## 4. 全 Category の未取得銘柄一覧（参考）

### 4.1 not_collected (11 件)

| Category | Symbol | ISIN | 会社名 |
|---|---|---|---|
| MNC | `PGHL` | INE199A01012 | PROCTER & GAMBLE HEALTH LTD |
| MNC | `PGHH` | INE179A01014 | PROCTER & GAMBLE HYGIENE |
| MNC | `SANOFI` | INE058A01010 | SANOFI INDIA LTD |
| State | `GUJGASLTD` | INE844O01030 | GUJARAT GAS LTD |
| Professional | `FINOPB` | INE02NC01014 | FINO PAYMENTS BANK LTD |
| State | `PSB` | INE608A01012 | PUNJAB & SIND BANK |
| State | `KIOCL` | INE880L01014 | KIOCL LTD |
| Professional | `TICL` | INE388G01026 | TATA INVESTMENT CORP LTD |
| abb | `UTKARSHBNK` | INE735W01017 | UTKARSH SMALL FINANCE BANK L |
| State | `GUJALKALI` | INE186A01019 | GUJARAT ALKALIES & CHEMICALS |
| State | `BALMLAWRIE` | INE164A01016 | BALMER LAWRIE & CO LTD |

### 4.2 isin_unresolved (16 件)

| Category | ISIN | 会社名 |
|---|---|---|
| Owner | INE274G01010 | DHANI SERVICES LTD |
| Owner | INE752P01024 | FUTURE RETAIL LTD |
| Owner | INE140A01024 | PIRAMAL ENTERPRISES LTD |
| Professional | INE001A01036 | HOUSING DEVELOPMENT FINANCE |
| Professional | INE334L01012 | UJJIVAN FINANCIAL SERVICES L |
| Professional | INE043D01016 | IDFC LTD |
| Owner | INE886H01027 | TV18 BROADCAST LTD |
| Professional | INE763G01038 | ICICI SECURITIES LTD |
| Professional | INE0NDH25011 | NEXUS SELECT TRUST |
| State | INE0GGX23010 | POWERGRID INFRASTRUCTURE INV |
| MNC | INE0FDU25010 | BROOKFIELD INDIA REAL ESTATE |
| Owner | INE0CCU25019 | MINDSPACE BUSINESS PARKS REI |
| Owner | INE041025011 | EMBASSY OFFICE PARKS REIT |
| Owner | INE778U01029 | TCNS CLOTHING CO LTD |
| Professional | INE493A01027 | TATA COFFEE LTD |
| Owner | INE455F01025 | JAIPRAKASH ASSOCIATES LTD |

### 4.3 isin_missing (24 件)

| Category | 会社名 |
|---|---|
| Professional | L&T FINANCE HOLDINGS LTD |
| Owner | JINDAL STEEL & POWER LTD |
| Owner | CENTURY TEXTILES & INDS LTD |
| Owner | INDIABULLS REAL ESTATE LTD |
| Owner | INDIABULLS HOUSING FINANCE L |
| Owner | GMR INFRASTRUCTURE LTD |
| Owner | INFIBEAM AVENUES LTD |
| Owner | AMARA RAJA BATTERIES LTD |
| Professional | TATA MOTORS LTD |
| Owner | AEGIS LOGISTICS LTD |
| Professional | LTIMINDTREE LTD |
| Owner | ADANI TRANSMISSION  LTD |
| Owner | ADANI WILMAR LTD |
| Owner | GLENMARK LIFE SCIENCES LTD |
| Owner | AMI ORGANICS LTD |
| Professional | DATA INFRASTRUCTURE TRUST |
| Professional | SUVEN PHARMACEUTICALS LTD |
| Owner | WELSPUN INDIA LTD |
| Owner | MAHINDRA LIFESPACE DEVELOPER |
| Owner | SWAN ENERGY LTD |
| Owner | HBL POWER SYSTEMS LTD |
| Owner | LT FOODS LTD |
| Owner | D B REALTY LTD |
| MNC | ITD CEMENTATION INDIA LTD |

### 4.4 全 partially_covered (38 件)

| Category | Symbol | ISIN | 会社名 | shareholdings | detail | candidates |
|---|---|---|---|:---:|:---:|:---:|
| Professional | `CUB` | INE491A01021 | CITY UNION BANK LTD | ✓ | — | — |
| Professional | `RBLBANK` | INE976G01028 | RBL BANK LTD | ✓ | — | — |
| MNC | `COFORGE` | INE591G01025 | COFORGE LIMITED | ✓ | — | — |
| Professional | `HDFCBANK` | INE040A01034 | HDFC BANK LIMITED | ✓ | — | — |
| Professional | `CROMPTON` | INE299U01018 | CROMPTON GREAVES CONSUMER EL | ✓ | — | — |
| Professional | `LT` | INE018A01030 | LARSEN & TOUBRO LTD | ✓ | — | — |
| Professional | `FEDERALBNK` | INE171A01029 | FEDERAL BANK LTD | ✓ | — | — |
| Professional | `ICICIBANK` | INE090A01021 | ICICI BANK LTD | ✓ | — | — |
| Professional | `AXISBANK` | INE238A01034 | AXIS BANK LTD | ✓ | — | — |
| Professional | `ITC` | INE154A01025 | ITC LTD | ✓ | — | — |
| Professional | `YESBANK` | INE528G01035 | YES BANK LTD | ✓ | — | — |
| Owner | `MFSL` | INE180A01020 | MAX FINANCIAL SERVICES LTD | ✓ | — | — |
| Owner | `ZEEL` | INE256A01028 | ZEE ENTERTAINMENT ENTERPRISE | ✓ | — | — |
| Professional | `IEX` | INE022Q01020 | INDIAN ENERGY EXCHANGE LTD | ✓ | — | — |
| Professional | `MCX` | INE745G01043 | MULTI COMMODITY EXCH INDIA | ✓ | — | — |
| Professional | `IDFCFIRSTB` | INE092T01019 | IDFC FIRST BANK LTD | ✓ | — | — |
| Owner | `DISHTV` | INE836F01026 | DISH TV INDIA LTD | ✓ | — | — |
| Owner | `360ONE` | INE466L01038 | 360 ONE WAM LTD | ✓ | — | — |
| Professional | `ETERNAL` | INE758T01015 | ZOMATO LTD | ✓ | — | — |
| Professional | `TMB` | INE668A01016 | TAMILNAD MERCANTILE BANK | ✓ | — | — |
| Professional | `DELHIVERY` | INE148O01028 | DELHIVERY LTD | ✓ | — | — |
| Professional | `CMSINFO` | INE925R01014 | CMS INFO SYSTEMS LTD | ✓ | — | — |
| Professional | `PAYTM` | INE982J01020 | ONE 97 COMMUNICATIONS LTD | ✓ | — | — |
| Professional | `POLICYBZR` | INE417T01026 | PB FINTECH LTD | ✓ | — | — |
| Professional | `CARTRADE` | INE290S01011 | CARTRADE TECH LTD | ✓ | — | — |
| Professional | `HOMEFIRST` | INE481N01025 | HOME FIRST FINANCE CO INDIA | ✓ | — | — |
| Professional | `EQUITASBNK` | INE063P01018 | EQUITAS SMALL FINANCE BANK L | ✓ | — | — |
| Professional | `UTIAMC` | INE094J01016 | UTI ASSET MANAGEMENT CO LTD | ✓ | — | — |
| Professional | `CAMS` | INE596I01020 | COMPUTER AGE MANAGEMENT SERV | ✓ | — | — |
| Professional | `UJJIVANSFB` | INE551W01018 | UJJIVAN SMALL FINANCE BANK L | ✓ | — | — |
| Professional | `BSE` | INE118H01025 | BSE LTD | ✓ | — | — |
| MNC | `REDINGTON` | INE891D01026 | REDINGTON LTD | ✓ | — | — |
| Professional | `KARURVYSYA` | INE036D01028 | KARUR VYSYA BANK LTD | ✓ | — | — |
| Professional | `KTKBANK` | INE614B01018 | KARNATAKA BANK LTD | ✓ | — | — |
| Professional | `SOUTHBANK` | INE683A01023 | SOUTH INDIAN BANK LTD | ✓ | — | — |
| Professional | `GOKEX` | INE887G01027 | GOKALDAS EXPORTS LTD | ✓ | — | — |
| Owner | `ASTRAMICRO` | INE386C01029 | ASTRA MICROWAVE PRODUCTS LTD | ✓ | — | — |
| Professional | `SWIGGY` | INE00H001014 | SWIGGY LTD | ✓ | — | — |

---

## 5. 偽陽性 (FP) — 自前ロジックで OWNER 判定 / owners.json で Owner 以外

**判定条件**: `owner_candidates.csv` の `owner_flag_final` が OWNER または OWNER_WEAK、かつ owners.json の Category が Owner 以外。
**該当件数**: **42 件**

### 5.1 owners.json Category 別の FP 内訳

| owners.json Category | 件数 |
|---|---:|
| Professional | 28 |
| State | 8 |
| MNC | 6 |
| **合計** | **42** |

### 5.2 偽陽性の全銘柄一覧

| owners.json Category | Symbol | ISIN | 会社名 | 自前判定 (final) | rule based flag | AI flag | AI conf | promoter% | dir% | kmp% |
|---|---|---|---|---|---|---|---:|---:|---:|---:|
| State | `CANFINHOME` | INE477A01020 | CAN FIN HOMES LTD | OWNER | owner_confirmed_director_only | — | — | 29.99 | 0.00 | 0.00 |
| State | `GSFC` | INE026A01025 | GUJARAT STATE FERT & CHEMICA | OWNER | owner_confirmed_director_only | — | — | 37.84 | 0.00 | 0.00 |
| State | `HINDPETRO` | INE094A01015 | HINDUSTAN PETROLEUM CORP | OWNER | owner_confirmed_director_only | — | — | 54.90 | 0.00 | 0.00 |
| State | `MRPL` | INE103A01014 | MANGALORE REFINERY & PETRO | OWNER | owner_confirmed_director_only | — | — | 88.58 | 0.00 | 0.00 |
| State | `PETRONET` | INE347G01014 | PETRONET LNG LTD | OWNER | owner_confirmed_director_only | — | — | 50.00 | 0.00 | 0.00 |
| State | `RECLTD` | INE020B01018 | REC LTD | OWNER | owner_confirmed_director_only | — | — | 52.63 | 0.00 | 0.00 |
| State | `SBICARD` | INE018E01016 | SBI CARDS & PAYMENT SERVICES | OWNER | owner_confirmed_director_only | — | — | 68.58 | 0.00 | 0.00 |
| State | `SBILIFE` | INE123W01016 | SBI LIFE INSURANCE CO LTD | OWNER | owner_confirmed_director_only | — | — | 55.34 | 0.00 | 0.00 |
| MNC | `EPL` | INE255A01020 | EPL LTD | OWNER | owner_confirmed_director_only | — | — | 26.38 | 0.22 | 0.01 |
| MNC | `GILLETTE` | INE322A01010 | GILLETTE INDIA LTD | OWNER | owner_confirmed_director_only | — | — | 75.00 | 0.00 | 0.00 |
| MNC | `GPPL` | INE517F01014 | GUJARAT PIPAVAV PORT LTD | OWNER | owner_confirmed_director_only | — | — | 44.01 | 0.00 | 0.00 |
| MNC | `KSB` | INE999A01023 | KSB LTD | OWNER | owner_confirmed_individual | — | — | 69.80 | 0.00 | 0.00 |
| MNC | `SCHNEIDER` | INE839M01018 | SCHNEIDER ELECTRIC INFRASTRU | OWNER | owner_confirmed_director_only | — | — | 75.00 | 0.00 | 0.00 |
| MNC | `WHIRLPOOL` | INE716A01013 | WHIRLPOOL OF INDIA LTD | OWNER | owner_confirmed_director_only | — | — | 39.76 | 0.00 | 0.00 |
| Professional | `AAVAS` | INE216P01012 | AAVAS FINANCIERS LTD | OWNER | owner_confirmed_director_only | — | — | 48.95 | 0.00 | 0.93 |
| Professional | `CDSL` | INE736A01011 | CENTRAL DEPOSITORY SERVICES | OWNER | owner_confirmed_director_only | — | — | 15.00 | 0.00 | 0.00 |
| Professional | `DCBBANK` | INE503A01015 | DCB BANK LTD | OWNER | owner_confirmed_director_only | — | — | 16.24 | 0.16 | 0.01 |
| Professional | `HDFCAMC` | INE127D01025 | HDFC ASSET MANAGEMENT CO LTD | OWNER | owner_confirmed_director_only | — | — | 52.38 | 0.19 | 0.00 |
| Professional | `HDFCLIFE` | INE795G01014 | HDFC LIFE INSURANCE CO LTD | OWNER | owner_confirmed_director_only | — | — | 50.21 | 0.06 | 0.00 |
| Professional | `ICICIGI` | INE765G01017 | ICICI LOMBARD GENERAL INSURA | OWNER | owner_confirmed_director_only | — | — | 51.31 | 0.00 | 0.05 |
| Professional | `ICICIPRULI` | INE726G01019 | ICICI PRUDENTIAL LIFE INSURA | OWNER | owner_confirmed_director_only | — | — | 72.88 | 0.00 | 0.00 |
| Professional | `INDHOTEL` | INE053A01029 | INDIAN HOTELS CO LTD | OWNER | owner_confirmed_director_only | — | — | 38.12 | 0.01 | 0.00 |
| Professional | `INFY` | INE009A01021 | INFOSYS LTD | OWNER | owner_confirmed_individual_and_director | — | — | 14.52 | 0.04 | 0.01 |
| Professional | `JBCHEPHARM` | INE572A01036 | J.B. CHEMICALS & PHARMA LTD | OWNER | owner_confirmed_director_only | — | — | 48.78 | 0.00 | 0.00 |
| Professional | `LTTS` | INE010V01017 | L&T TECHNOLOGY SERVICES LTD | OWNER | owner_confirmed_director_only | — | — | 73.58 | 0.47 | 0.02 |
| Professional | `MPHASIS` | INE356A01018 | MPHASIS LTD | OWNER | owner_confirmed_director_only | — | — | 30.59 | 0.21 | 0.00 |
| Professional | `NETWORK18` | INE870H01013 | NETWORK 18 MEDIA & INVTS LTD | OWNER | owner_confirmed_director_only | — | — | 56.89 | 0.00 | 0.00 |
| Professional | `PNBHOUSING` | INE572E01012 | PNB HOUSING FINANCE LTD | OWNER | owner_confirmed_director_only | — | — | 28.04 | 0.00 | 0.01 |
| Professional | `RBA` | INE07T201019 | RESTAURANT BRANDS ASIA LTD | OWNER | owner_confirmed_director_only | — | — | 11.26 | 0.00 | 0.32 |
| Professional | `RELIGARE` | INE621H01010 | RELIGARE ENTERPRISES LTD | OWNER | owner_confirmed_director_only | — | — | 26.27 | 0.00 | 0.00 |
| Professional | `SAPPHIRE` | INE806T01020 | SAPPHIRE FOODS INDIA LTD | OWNER | owner_confirmed_director_only | — | — | 26.07 | 0.50 | 0.00 |
| Professional | `STARHEALTH` | INE575P01011 | STAR HEALTH & ALLIED INSURAN | OWNER | owner_confirmed_individual_and_director | — | — | 57.98 | 0.24 | 0.13 |
| Professional | `TATACHEM` | INE092A01019 | TATA CHEMICALS LTD | OWNER | owner_confirmed_director_only | — | — | 37.98 | 0.00 | 0.00 |
| Professional | `TATACOMM` | INE151A01013 | TATA COMMUNICATIONS LTD | OWNER | owner_confirmed_director_only | — | — | 58.86 | 0.00 | 0.00 |
| Professional | `TATACONSUM` | INE192A01025 | TATA CONSUMER PRODUCTS LTD | OWNER | owner_confirmed_director_only | — | — | 33.84 | 0.01 | 0.00 |
| Professional | `TATAELXSI` | INE670A01012 | TATA ELXSI LTD | OWNER | owner_confirmed_director_only | — | — | 43.90 | 0.00 | 0.00 |
| Professional | `TATAPOWER` | INE245A01021 | TATA POWER CO LTD | OWNER | owner_confirmed_director_only | — | — | 46.86 | 0.02 | 0.00 |
| Professional | `TATASTEEL` | INE081A01020 | TATA STEEL LTD | OWNER | owner_confirmed_director_only | — | — | 33.19 | 0.02 | 0.00 |
| Professional | `TCS` | INE467B01029 | TATA CONSULTANCY SVCS LTD | OWNER | owner_confirmed_director_only | — | — | 71.77 | 0.01 | 0.00 |
| Professional | `TEJASNET` | INE010J01012 | TEJAS NETWORKS LTD | OWNER | owner_confirmed_director_only | — | — | 53.46 | 0.19 | 0.01 |
| Professional | `TRENT` | INE849A01020 | TRENT LTD | OWNER | owner_confirmed_director_only | — | — | 37.01 | 0.27 | 0.00 |
| Professional | `TTML` | INE517B01013 | TATA TELESERVICES MAHARASHTR | OWNER | owner_confirmed_director_only | — | — | 74.36 | 0.00 | 0.00 |

### 5.3 偽陽性の主要原因（既知）

- **`owner_confirmed_director_only` ルール起因**: 法人プロモーター配下で雇われ Director / KMP が名目 1 株保有しているケースを OWNER 判定してしまう。Tata Group / ICICI / HDFC / SBI 等の関連会社が該当。
- **対策候補 (act-2026-04-17-006)**: `dir_pct + kmp_pct ≥ 1%` 閾値追加 or Tier 3 降格でルール厳格化（Precision 90.2% → 98%+ 目標）。

---

## 6. サマリー

- owners.json 全 635 銘柄中、**584 銘柄 (92.0%)** がデータ取得済み（fully + partially）
- Owner カテゴリ 428 銘柄中、**397 銘柄 (93.9%)** が完全取得済み、5 銘柄が部分取得
- ISIN 由来で取得不可な Owner 26 銘柄の内訳: 上場廃止・REIT 8 件 / owners.json ISIN 欠損 18 件
- 自前ロジックの偽陽性は **42 件**、Professional 28, State 8, MNC 6
