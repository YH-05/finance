# NSE/BSE XBRL Shareholding Pattern カテゴリ/サブカテゴリ分類体系

**生成日**: 2026-04-16
**対象 taxonomy**: BSE SHP XBRL (2018-03-31 / 2022-09-30 / 2025-05-31 / 2025-10-31)
**出典**:
- SEBI (ICDR) Regulations 2009/2018 (sebi.gov.in)
- SEBI (LODR) Regulations 2015 (sebi.gov.in)
- Companies Act 2013 (indiacode.nic.in)
- BSE XBRL Taxonomy (bseindia.com/xbrl/)

---

## 目次

1. [データ構造](#1-データ構造)
2. [Top-level Category](#2-top-level-category)
3. [PromoterAndPromoterGroup サブカテゴリ](#3-promoterandpromotergroup-サブカテゴリ)
4. [PublicShareholding サブカテゴリ](#4-publicshareholding-サブカテゴリ)
5. [NonPromoterNonPublic サブカテゴリ](#5-nonpromoternonpublic-サブカテゴリ)
6. [is_category_total フラグの意味](#6-is_category_total-フラグの意味)
7. [Filers の慣習・注意点](#7-filers-の慣習注意点)
8. [Owner 判定ロジック対応表](#8-owner-判定ロジック対応表)
9. [出典（1 次情報）](#9-出典1-次情報)

---

## 1. データ構造

`shareholding_detail.csv` は 3 階層構造:

- **`category`** (top-level): 3 種 (Promoter / Public / NonPromoterNonPublic)
- **`sub_category`**: 約 60 種の細分類
- **`shareholder_name`**: 個別株主名 (is_category_total=0 の明細行のみ)

1 銘柄 × 1 四半期あたり、集計行と個別明細行が合わせて 50〜200 行出力される。

---

## 2. Top-level Category

| category | 日本語 | 意味 |
|---|---|---|
| `PromoterAndPromoterGroup` | Promoter and Promoter Group | 創業者・支配株主・その親族・関連会社 |
| `PublicShareholding` | Public Shareholding | 一般公開株主（機関投資家・個人投資家） |
| `NonPromoterNonPublic` | Non-Promoter Non-Public | 上記以外（信託・Custodian 等） |

---

## 3. PromoterAndPromoterGroup サブカテゴリ

SEBI (ICDR) 2009 Reg 2(1)(zb) の promoter group 定義に対応する XBRL 分類。

### 3.1 自然人系 (Natural Persons)

本人・親族・取締役・KMP・ファミリートラスト。**Owner 判定の核**。

| sub_category (XBRL) | 日本語 | SEBI Table II 行 |
|---|---|---|
| `IndividualsOrHinduUndividedFamily` | 個人・Hindu Undivided Family | **A(1)(a)** |
| `NonResidentIndividualsOrForeignIndividuals` | NRI・外国人個人 | **A(2)(a)** |
| `DirectorsAndDirectorsRelatives` | 取締役と親族 | A(1)(d) 内訳 |
| `KeyManagerialPersonnel` | Key Managerial Personnel (CEO/CFO/CS) | A(1)(d) 内訳 |
| `RelativesOfPromotersOtherThanPromoterGroup` | 狭義 promoter group 外の親族 | A(1)(d) 内訳 |
| `TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroupIsisTrusteeOrBeneficiaryOrAuthorOfTrust` | ファミリートラスト | A(1)(d) 内訳 |

### 3.2 法人系 (Bodies Corporate)

| sub_category (XBRL) | 日本語 |
|---|---|
| `AssociateCompaniesOrSubsidiaries` | 関連会社・子会社 |
| `BodiesCorporateIncludingSubsidiaries` | 法人（子会社含む） |
| `OtherIndianShareholders` | その他 Indian 株主（家族 holding company が多い） |
| `OtherForeignShareholders` | その他 Foreign 株主（外国 holding company 等） |
| `IndianFinancialInstitutionsOrBanks` | Indian 金融機関・銀行 |

### 3.3 政府系 (Government)

| sub_category (XBRL) | 日本語 |
|---|---|
| `CentralGovernmentOrPresidentOfIndia` | 中央政府・大統領 |
| `StateGovernmentsOrGovernors` | 州政府・知事 |
| `ForeignGovernment` | 外国政府 |
| `ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoter` | 政府系 body corporate |
| `CentralGovernmentOrStateGovernmentS` | 中央・州政府（旧 taxonomy） |

### 3.4 外国系 Institutions / FPI (promoter 側)

| sub_category (XBRL) | 日本語 |
|---|---|
| `ForeignInstitutions` | 外国機関 |
| `ForeignPortfolioInvestor` | FPI |

### 3.5 再集計行 (⚠️ 二重計上注意)

これらは他 sub_category の**小計**。素朴に SUM すると二重計上になる。

| sub_category | 集計対象 |
|---|---|
| `Indian` | Individuals/HUF + Governments + Banks + OtherIndian 等の合算 |
| `Foreign` | NRI + Foreign Govt + Foreign Inst + FPI + Other Foreign 等の合算 |
| `Governments` / `Goverments` | 中央 + 州 + Foreign 政府の合算（綴り違いは taxonomy 版依存）|
| `CentralAndStateGovernments` | 中央 + 州政府の合算 |
| `ForeignPromotersCumulativeOrAggregation` | 外国 promoter の cumulative |

**集計時のルール**: 個別 sub_category を明示列挙して SUM すること。

---

## 4. PublicShareholding サブカテゴリ

### 4.1 国内機関投資家 (Institutions Domestic)

| sub_category | 日本語 |
|---|---|
| `MutualFundsOrUti` | Mutual Funds / UTI |
| `VentureCapitalFunds` | VC |
| `AlternativeInvestmentFunds` | AIF |
| `Banks` | 銀行 |
| `InsuranceCompanies` | 保険会社 |
| `ProvidentFundsOrPensionFunds` | 年金基金 |
| `AssetReconstructionCompanies` | ARC |
| `SovereignWealthFundsDomestic` | 国内 SWF |
| `NBFCsRegisteredWithRbi` | NBFC (RBI 登録) |
| `OtherFinancialInstitutions` | その他金融機関 |
| `OtherInstitutionsDomestic` | その他国内機関 |
| `InstitutionsDomestic` | **（再集計）** 国内機関合計 |

### 4.2 外国機関投資家 (Institutions Foreign)

| sub_category | 日本語 |
|---|---|
| `ForeignDirectInvestment` | FDI |
| `ForeignVentureCapitalInvestors` | 外国 VC |
| `SovereignWealthFundsForeign` | 外国 SWF |
| `InstitutionsForeignPortfolioInvestorCatergoryOne` | FPI Category 1 |
| `InstitutionsForeignPortfolioInvestorCatergoryTwo` | FPI Category 2 |
| `OverseasDepositories` | Overseas Depositories |
| `OtherInstitutionsForeign` | その他外国機関 |
| `InstitutionsForeign` | **（再集計）** 外国機関合計 |

### 4.3 個人投資家・その他

| sub_category | 日本語 |
|---|---|
| `ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh` | 国内個人 保有額 ≤ 2 Lakh |
| `ResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakh` | 国内個人 保有額 > 2 Lakh (HNI) |
| `NonResidentIndians` | NRI |
| `ForeignNationals` | 外国人個人 |
| `ForeignCompanies` | 外国企業 |
| `BodiesCorporate` | 法人 |
| `OtherNonInstitutions` | その他非機関 |
| `NonInstitutions` | **（再集計）** 非機関合計 |
| `InvestorEducationAndProtectionFund` | IEPF |

---

## 5. NonPromoterNonPublic サブカテゴリ

| sub_category | 日本語 |
|---|---|
| `CustodianOrDRHolder` | ADR/GDR Custodian |
| `EmployeeBenefitsTrusts` | 従業員福利厚生信託 |

---

## 6. `is_category_total` フラグの意味

| 値 | 意味 | 特徴 |
|---|---|---|
| `1` | 集計行 | shareholder_name が空、num_shareholders は集計数 |
| `0` | 個別株主明細行 | shareholder_name に個人名 or 法人名 |

集計行 (`is_category_total=1`) の中にも 2 階層:
- `sub_category=""`: **カテゴリ合計** (例: Promoter 合計 50.11%)
- `sub_category="IndividualsOrHinduUndividedFamily"`: **sub-category 小計** (例: 0.84%)

---

## 7. Filers の慣習・注意点

### 7.1 創業家は Individuals/HUF にのみ報告される

SEBI 規定では同じ個人を 2 つの sub_category に重複報告しない慣習。
取締役兼 promoter の創業家は `IndividualsOrHinduUndividedFamily` にのみ現れ、
`DirectorsAndDirectorsRelatives` が空欄のケースが多い。

**例**:
- Britannia (Nusli Wadia): hufi に Wadia 家、dir = 0
- Apollo Tyres (Kanwar): hufi に 3 名、dir = 0
- Asahi India Glass (Labroo): hufi に 33 名、dir = 0

この慣習のため、「経営陣に promoter 在籍」判定には `IndividualsOrHinduUndividedFamily >= 1` も
経営陣兼任の proxy として採用する必要がある。

### 7.2 `OtherIndianShareholders` / `OtherForeignShareholders` の両義性

これらには複数の本質的に異なる entity が混在し、sub_category だけでは区別不能:

| 混在パターン | 実例 |
|---|---|
| 家族 holding company (真の Owner) | PCBL / Rainbow Investments (Goenka)、OLECTRA / MEIL Holdings (Reddy) |
| 外国多国籍企業 (MNC) | GLAND / Fosun Pharma (中国)、ROUTE / Proximus (ベルギー) |
| 信託系 (Professional-managed) | TCS / Tata Sons (Tata Trusts 経由) |
| 政府系 body corporate (filers 誤分類) | IGL / MGL (GAIL, BPCL 系) |

**対処**: `shareholder_name` 詳細行（`is_category_total=0`）の実名を確認する必要あり。

### 7.3 2025-10-31 taxonomy の pct 小数表記

2025-10-31 revision では pct フィールドが小数表記 (0.649 = 64.9%)。
`market.nse.xbrl._DECIMAL_PCT_TAXONOMIES` で自動 ×100 スケーリング実施済み。

---

## 8. Owner 判定ロジック対応表

各 sub_category が `owner_flag` 判定のどの条件に使用されるか:

| sub_category | owner_flag 判定上の役割 | 関連 Tier |
|---|---|---|
| `IndividualsOrHinduUndividedFamily` | `hufi_num` (core シグナル) | Tier 1/3 |
| `NonResidentIndividualsOrForeignIndividuals` | `nri_num` (NRI family シグナル) | Tier 2 |
| `DirectorsAndDirectorsRelatives` | `dir_num` (formal 取締役報告) | Tier 1 |
| `KeyManagerialPersonnel` | `kmp_num` (KMP 報告) | Tier 1 |
| `RelativesOfPromotersOtherThanPromoterGroup` | `rel_num` (広義親族) | Tier 2 |
| `TrustsWhereAnyPerson...Trustee...` | `trust_num` (family trust) | Tier 2 |
| `OtherIndianShareholders` | `other_indian_pct` (holding 経由型) | Tier 3 |
| `OtherForeignShareholders` | `other_foreign_pct` (foreign holding) | Tier 3 |
| `ForeignInstitutions`, `ForeignPortfolioInvestor` | `foreign_non_govt_pct` (MNC-JV 判定) | Tier 3 |
| `CentralGovernmentOrPresidentOfIndia`, `StateGovernmentsOrGovernors`, etc. | `govt_pct` (PSU 除外) | Tier 4 |

### owner_flag ラベル一覧 (notebook 内 `assign_owner_flag()` と一致)

**Tier 1: 高信頼 Owner (AI 不要)**

| ラベル | 条件 |
|---|---|
| `owner_confirmed_individual_and_director` | `promoter≥10 AND hufi≥1 AND (dir≥1 OR kmp≥1) AND foreign_non_govt<50` |
| `owner_confirmed_individual` | `promoter≥10 AND hufi≥1 AND foreign_non_govt<50` |
| `owner_confirmed_director_only` | `promoter≥10 AND (dir≥1 OR kmp≥1) AND hufi=0 AND nri=0 AND foreign_non_govt<50` |

**Tier 2: 確率中 (AI review 対象)**

| ラベル | 条件 |
|---|---|
| `owner_probable_nri_family` | `promoter≥10 AND nri≥1 AND hufi=0` |
| `owner_probable_relatives_trust` | `promoter≥10 AND (rel≥1 OR trust≥1) AND hufi=0 AND nri=0 AND dir=0 AND kmp=0` |

**Tier 3: 要 AI 判定**

| ラベル | 条件 |
|---|---|
| `ambiguous_mnc_jv_candidate` | `promoter≥10 AND hufi≥1 AND foreign_non_govt≥50` |
| `ambiguous_minor_individual` | `promoter≥10 AND hufi≥1 AND hufi_pct<0.5 AND dir=0 AND kmp=0` |
| `ambiguous_holding_indian` | `promoter≥10 AND natural_num_sum=0 AND other_indian_pct≥10` |
| `ambiguous_holding_foreign` | `promoter≥10 AND natural_num_sum=0 AND other_foreign_pct≥10` |

**Tier 4: 除外 (AI 不要)**

| ラベル | 条件 |
|---|---|
| `excluded_low_promoter` | `promoter<10` |
| `excluded_state_dominant` | `govt_pct≥10` |
| `excluded_no_natural_no_holding` | 上記いずれにも該当せず |

---

## 9. 出典（1 次情報）

| 規則 / 文書 | URL |
|---|---|
| SEBI (ICDR) Regulations 2009 | https://www.sebi.gov.in/acts/icdrreg.html |
| SEBI (ICDR) Regulations 2018 (2025-03-08) | https://www.sebi.gov.in/legal/regulations/mar-2025/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-march-8-2025-_93559.html |
| SEBI (SAST) Regulations 2011 Gazette | https://www.sebi.gov.in/sebi_data/attachdocs/1367922725672.pdf |
| SEBI (LODR) Regulations 2015 Gazette | https://www.sebi.gov.in/sebi_data/attachdocs/1441284401427.pdf |
| Companies Act 2013 | https://www.indiacode.nic.in/bitstream/123456789/2114/5/A2013-18.pdf |
| BSE XBRL SHP Taxonomy ZIP | https://www.bseindia.com/downloads1/SHPTaxonomy.zip |
| NSE Shareholding Pattern 開示様式 | https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Shareholding_Pattern_UR_31%2030062021.pdf |

**本プロジェクトの 1 次情報調査**:
`research/2026-04-16_nse_promoter_classification/research.md`
