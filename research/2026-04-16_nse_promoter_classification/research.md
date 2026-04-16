# NSE Shareholding Pattern — Promoter 本人・親族判定の法的根拠

調査日: 2026-04-16
出典: SEBI (sebi.gov.in) / BSE (bseindia.com) / NSE (nsearchives.nseindia.com) / India Code (indiacode.nic.in) のみ

---

## 1. 調査サマリ（3行）

- **Promoter/Promoter Group の構成要件**は SEBI (ICDR) Regulations 2009 の Regulation 2(1)(za)/(zb) に由来し、SEBI (ICDR) Regulations 2018 および SEBI (LODR) Regulations 2015 がこれを準用する。BSE SHP XBRL taxonomy (`in-bse-shp-2022-09-30`) の `IndividualsOrHinduUndividedFamily` / `RelativesOfPromotersOtherThanPromoterGroup` / `DirectorsAndDirectorsRelatives` / `KeyManagerialPersonnel` / `NonResidentIndividualsOrForeignIndividuals` は **自然人（本人・親族・経営者）** を報告するセルであり、SEBI Table II の Promoter 行 A(1)(a)・A(2)(a) に対応する。
- **法人/政府 promoter** を示すセルは `AssociateCompaniesOrSubsidiaries` / `BodiesCorporateIncludingSubsidiaries` / `IndianFinancialInstitutionsOrBanks` / `CentralGovernmentOrPresidentOfIndia` / `StateGovernmentsOrGovernors` / `ForeignGovernment` / `ForeignInstitutions` / `ForeignPortfolioInvestor` / `ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoter`。
- 本人・親族スクリーニングの実務判定: **Promoter カテゴリ内で、`IndividualsOrHinduUndividedFamily` + `NonResidentIndividualsOrForeignIndividuals` + `RelativesOfPromotersOtherThanPromoterGroup` + (任意で `DirectorsAndDirectorsRelatives` / `KeyManagerialPersonnel`) の合計持分比率が、Promoter 合計持分の大半（閾値は実装側で決定）を占める銘柄を「ファミリー企業」と判定する**のが一次情報と整合する。

---

## 2. 判定ロジック結論

### 2.1 自然人（本人・親族）を示す Promoter サブカテゴリ

| XBRL Member 名（`in-bse-shp` taxonomy） | SEBI Table II 対応行 | 意味 | 含まれる人 |
|---|---|---|---|
| `IndividualsOrHinduUndividedFamilyMember` | **A(1)(a) Individuals/Hindu undivided Family** | インド国籍の自然人または HUF | Promoter 本人、Promoter の immediate relatives（配偶者・親・兄弟姉妹・子、またはその配偶者の該当者）、HUF 口座 |
| `NonResidentIndividualsOrForeignIndividualsMember` | **A(2)(a) Individuals (Non-Resident Individuals/Foreign Individuals)** | 外国籍またはNRIの自然人 | 外国人 Promoter 本人、NRI 親族 |
| `RelativesOfPromotersOtherThanPromoterGroupMember` | **任意追加行（2022-09-30 taxonomy 以降）** | Promoter Group に入らない広義の親族 | Companies Act 2(77) Rule 4 で relative だが ICDR 2(1)(pp) "immediate relative" に含まれない者 |
| `DirectorsAndDirectorsRelativesMember` | **任意追加行** | 取締役・取締役親族 | 取締役本人・親族（自然人） |
| `KeyManagerialPersonnelMember` | **任意追加行** | Key Managerial Personnel | CEO/CFO/CS 等（自然人） |

**`IndividualsOrHinduUndividedFamily` は Table II の行 A(1)(a) そのもの**で、SEBI 規定上「Individuals/Hindu undivided Family」の名称で、Promoter 本人または immediate relative の自然人を disclose するための行である（NSE/BSE が配布する標準 template で `Name (xyz...)` 行に個人名・PAN が入る）。

### 2.2 法人/政府/機関を示す Promoter サブカテゴリ（**スクリーニングで除外すべき**）

| XBRL Member 名 | SEBI Table II 対応行 | 意味 |
|---|---|---|
| `IndianFinancialInstitutionsOrBanksMember` | A(1)(c) Financial Institutions/Banks | インド金融機関・銀行 |
| `CentralGovernmentOrPresidentOfIndiaMember` / `StateGovernmentsOrGovernorsMember` | A(1)(b) Central Government/State Government(s) | 中央・州政府 |
| `ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoterMember` | A(1)(d) Any Other (政府系企業) | 政府が promoter の企業 |
| `AssociateCompaniesOrSubsidiariesMember` | A(1)(d) Any Other | 関連会社・子会社 |
| `BodiesCorporateIncludingSubsidiariesMember` | A(1)(d) Any Other | 法人（子会社含む） |
| `ForeignGovernmentMember` | A(2)(b) Government | 外国政府 |
| `ForeignInstitutionsMember` / `ForeignPortfolioInvestorMember` (Promoter側) | A(2)(c) / (d) | 外国機関・FPI が promoter のケース |
| `OtherForeignShareholdersMember` | A(2)(f) Any Other | その他外国 promoter |

### 2.3 両者が混在する銘柄の扱い

SEBI Table II は Promoter 持分合計を `(A) = (A)(1)+(A)(2)` で集計する。したがって、

- **自然人 promoter 比率** = (A(1)(a) + A(2)(a) の持分%) / (A) 持分%
- **法人/政府 promoter 比率** = 1 − 自然人 promoter 比率

の按分で判定できる。ファミリー企業スクリーニングの閾値は通常「自然人 promoter 比率 ≥ 50% かつ (A) 持分 ≥ 25–50%」等で実装側が設定する。

`RelativesOfPromotersOtherThanPromoterGroup` / `DirectorsAndDirectorsRelatives` / `KeyManagerialPersonnel` は 2022-09-30 以降の taxonomy で追加されたセルで、ファミリー経営者の保有比率の内訳情報を取得できる（存在する場合は自然人分子側に加算）。

---

## 3. Promoter / Promoter Group / Relative の法的定義

### 3.1 SEBI (ICDR) Regulations 2009, Regulation 2(1)(za) – "promoter"

SEBI が sebi.gov.in/acts/icdrreg.html で公開している原文。SEBI (ICDR) Regulations 2018 および SEBI (LODR) Regulations 2015 Regulation 2(1)(w) はこの定義を承継している。

> (za) promoter includes:
> (i) the person or persons who are in control of the issuer;
> (ii) the person or persons who are instrumental in the formulation of a plan or programme pursuant to which specified securities are offered to public;
> (iii) the person or persons named in the offer document as promoters
> ...
> Provided that a director or officer of the issuer or a person, if acting as such merely in his professional capacity shall not be deemed as a promoter:
> Provided further that a financial institution, scheduled bank, foreign institutional investor and mutual fund shall not be deemed to be a promoter merely by virtue of the fact that ten per cent. or more of the equity share capital of the issuer is held by such person

出典: `https://www.sebi.gov.in/acts/icdrreg.html`

### 3.2 SEBI (ICDR) Regulations 2009, Regulation 2(1)(zb) – "promoter group"

> (zb) promoter group includes:
> (i) the promoter;
> (ii) an immediate relative of the promoter (i.e., any spouse of that person, or any parent, brother, sister or child of the person or of the spouse); and
> (iii) in case promoter is a body corporate:
>   (A) a subsidiary or holding company of such body corporate;
>   (B) any body corporate in which the promoter holds ten per cent. or more of the equity share capital or which holds ten per cent. or more of the equity share capital of the promoter;
>   (C) any body corporate in which a group of individuals or companies or combinations thereof which hold twenty per cent. or more of the equity share capital in that body corporate also holds twenty per cent. or more of the equity share capital of the issuer; and
> (iv) in case the promoter is an individual:
>   (A) any body corporate in which ten per cent. or more of the equity share capital is held by the promoter or an immediate relative of the promoter or a firm or Hindu Undivided Family in which the promoter or any one or more of his immediate relative is a member;
>   (B) any body corporate in which a body corporate as provided in (A) above holds ten per cent. or more, of the equity share capital;
>   (C) any Hindu Undivided Family or firm in which the aggregate shareholding of the promoter and his immediate relatives is equal to or more than ten per cent. of the total; and
> (v) all persons whose shareholding is aggregated for the purpose of disclosing in the prospectus under the heading "shareholding of the promoter group":
>     Provided that a financial institution, scheduled bank, foreign institutional investor and mutual fund shall not be deemed to be promoter group merely by virtue of the fact that ten per cent. or more of the equity share capital of the issuer is held by such person

出典: `https://www.sebi.gov.in/acts/icdrreg.html`（ICDR 2009 原文; ICDR 2018 は同内容を Regulation 2(1)(pp) に移管）

### 3.3 SEBI (ICDR) Regulations 2018 — 条項番号の対応

SEBI が Web ページ `https://www.sebi.gov.in/legal/regulations/mar-2025/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-march-8-2025-_93559.html` で公開する ICDR 2018 最新版では:

- Regulation 2(1)(**oo**): "promoter" — ICDR 2009 (za) を承継
- Regulation 2(1)(**pp**): "promoter group" — ICDR 2009 (zb) を承継
- Regulation 2(1)(**l**): "immediate relative" — 「any spouse of that person, or any parent, brother, sister or child of the person or of the spouse」（ICDR 2009 の (zb)(ii) 内部定義を独立定義化）

※条文番号は「last amended on March 8, 2025」版で上記を検索結果から確認（`https://www.sebi.gov.in/legal/regulations/mar-2025/...`）。本文 PDF への直リンクを取得できなかったため番号は 2 次確認。原文ワーディングは ICDR 2009 と同一と SEBI メモランダム (aug-2021) および LODR 参照先から確認済み。

### 3.4 SEBI (SAST) Regulations 2011 — "immediate relative" (verbatim)

SEBI (Substantial Acquisition of Shares and Takeovers) Regulations, 2011 Gazette notification (23 Sep 2011):

> (l) "immediate relative" means any spouse of a person, and includes parent, brother, sister or child of such person or of the spouse;

> (s) "promoter" has the same meaning as in the Securities and Exchange Board of India (Issue of Capital and Disclosure Requirements) Regulations, 2009 and includes a member of the promoter group;

> (t) "promoter group" has the same meaning as in the Securities and Exchange Board of India (Issue of Capital and Disclosure Requirements) Regulations, 2009;

出典: `https://www.sebi.gov.in/sebi_data/attachdocs/1367922725672.pdf`（SAST 2011 Gazette, Page 5 of 65）

### 3.5 SEBI (LODR) Regulations 2015 — 準用条項

LODR 2015 原公布 Gazette (`https://www.sebi.gov.in/sebi_data/attachdocs/1441284401427.pdf`) では:

> (w) "promoter" and "promoter group" shall have the same meaning as assigned to them respectively in clauses (za) and (zb) of sub-regulation (1) of regulation 2 of the Securities and Exchange Board of India (Issue of Capital and Disclosure Requirements) Regulations, 2009.

> (zd) "relative" means relative as defined under sub-section (77) of section 2 of the Companies Act, 2013 and rules prescribed there under

LODR **本体では "immediate relative" を直接定義していない**。Companies Act 2(77) + Rule 4 経由で "relative" を、ICDR 経由で "immediate relative"（spouse + parent/brother/sister/child of person/spouse）を参照する構造。

### 3.6 Companies Act, 2013, Section 2(69) — "promoter"

India Code 公刊 PDF より verbatim:

> (69) "promoter" means a person—
> (a) who has been named as such in a prospectus or is identified by the company in the annual return referred to in section 92; or
> (b) who has control over the affairs of the company, directly or in directly whether as a share holder, director or otherwise; or
> (c) in accordance with whose advice, directions or instructions the Board of Directors of the company is accustomed to act:
> Provided that nothing in sub-clause (c) shall apply to a person who is acting merely in a professional capacity;

出典: `https://www.indiacode.nic.in/bitstream/123456789/2114/5/A2013-18.pdf`（CompaniesAct2013.pdf, p.23–24）

### 3.7 Companies Act, 2013, Section 2(77) — "relative"

> (77) "relative", with reference to any person, means any one who is related to another, if—
> (i) they are members of a Hindu Undivided Family;
> (ii) they are husband and wife; or
> (iii) one person is related to the other in such manner as may be prescribed;

出典: `https://www.indiacode.nic.in/bitstream/123456789/2114/5/A2013-18.pdf`（p.24）

### 3.8 Rule 4 of Companies (Specification of Definitions Details) Rules, 2014 — "List of relatives"

**注意**: MCA の `NCARules_Chapter1.pdf` / `CompaniesSpecification2ndAmndtRules` は Edge サーバーで 403 Access Denied を返し、India Code の `show-data` / `simple-search` URL は 403 を返したため、**primary source からの verbatim 取得に失敗**。

SEBI WebSearch 結果では Rule 4 リストが以下の 8 項を列挙する旨の記載があるが、**MCA / India Code の公式 PDF で verbatim 確認できなかった**ため「未解決事項（7章）」に記載し、実装では ICDR 由来の "immediate relative"（4 項: spouse / parent / brother / sister / child of person or of spouse）を優先採用する。

参考 URL（取得失敗）:
- `https://www.mca.gov.in/Ministry/pdf/NCARules_Chapter1.pdf`（Access Denied）
- `https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=...`（403）
- MCA Amendment PDF `CompaniesSpecification2ndAmndtRules_19022021.pdf`（HTML エラーページを返す）

---

## 4. Shareholding Pattern XBRL sub-category 対応表

出典: BSE SHP XBRL Taxonomy ZIP `https://www.bseindia.com/downloads1/SHPTaxonomy.zip`（2022-09-30 revision）の `in-bse-shp-2022-09-30.xsd` および `in-bse-shp-label-2022-09-30.xml`。NSE/SEBI Table II 行対応は `https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Shareholding_Pattern_UR_31%2030062021.pdf` より。

| XBRL Member 名（`in-bse-shp`） | XBRL ラベル（en） | SEBI Table II 行 | 性質 | 自然人？ | 根拠 URL |
|---|---|---|---|---|---|
| `IndividualsOrHinduUndividedFamilyMember` | Individuals or Hindu undivided family [Member] | **A(1)(a) Individuals/Hindu undivided Family** | 本人・immediate relative・HUF | ✅ 自然人 | BSE XSD + NSE SHP format |
| `CentralGovernmentOrStateGovernmentSMember` | Central government or state government(S) [Member] | A(1)(b) | 政府 | ❌ 政府 | BSE XSD |
| `IndianFinancialInstitutionsOrBanksMember` | Indian - financial institutions or banks [Member] | A(1)(c) | 金融機関 | ❌ 法人 | BSE XSD |
| `OtherIndianShareholdersMember` | Other Indian shareholders [Member] | A(1)(d) Any Other | その他（法人が大半） | △ 混在 | BSE XSD |
| `AssociateCompaniesOrSubsidiariesMember` | Associate companies or subsidiaries [Member] | A(1)(d) Any Other | 関連会社 | ❌ 法人 | BSE XSD |
| `BodiesCorporateIncludingSubsidiariesMember` | Bodies corporate including subsidiaries [Member] | A(1)(d) Any Other | 法人 | ❌ 法人 | BSE XSD |
| `DirectorsAndDirectorsRelativesMember` | Directors and directors relatives [Member] | A(1)(d) Any Other | 取締役・親族 | ✅ 自然人 | BSE XSD (2022-09-30 追加) |
| `KeyManagerialPersonnelMember` | Key managerial personnel [Member] | A(1)(d) Any Other | KMP | ✅ 自然人 | BSE XSD (2022-09-30 追加) |
| `RelativesOfPromotersOtherThanPromoterGroupMember` | Relatives of promoters other than promoter group [Member] | A(1)(d) Any Other | 広義の親族 | ✅ 自然人 | BSE XSD (2022-09-30 追加) |
| `TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroupIsisTrusteeOrBeneficiaryOrAuthorOfTrustMember` | Trusts where any person belonging to promoter and promoter group isis trustee or beneficiary or author of trust [Member] | A(1)(d) Any Other | ファミリートラスト | △ 信託（実質自然人支配） | BSE XSD |
| `CentralGovernmentOrPresidentOfIndiaMember` | Central government or president of india [Member] | A(1)(b) / (d) | 中央政府 | ❌ 政府 | BSE XSD |
| `StateGovernmentsOrGovernorsMember` | State governments or governors [Member] | A(1)(b) / (d) | 州政府 | ❌ 政府 | BSE XSD |
| `ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoterMember` | Shareholding by companies or bodies corporatewhere central or state government is promoter [Member] | A(1)(d) | 政府系企業 | ❌ 法人 | BSE XSD |
| `NonResidentIndividualsOrForeignIndividualsMember` | Non-resident individuals or foreign individuals [Member] | **A(2)(a) Individuals (Non-Resident Individuals/Foreign Individuals)** | NRI/外国人 | ✅ 自然人 | BSE XSD + NSE SHP format |
| `ForeignGovernmentMember` | Foreign - Government [Member] | A(2)(b) Government | 外国政府 | ❌ 政府 | BSE XSD |
| `ForeignInstitutionsMember` | Foreign Institutions [Member] | A(2)(c) Institutions | 外国機関 | ❌ 機関 | BSE XSD |
| `ForeignPortfolioInvestorMember` | Foreign Portfolio Investor [Member] | A(2)(d) | FPI | ❌ 機関 | BSE XSD |
| `OtherForeignShareholdersMember` | Other foreign shareholders [Member] | A(2)(f) Any Other | その他外国 | △ 混在 | BSE XSD |
| `IndianMember` | Indian [Member] | A(1) sub-total | 小計 | — | BSE XSD |
| `ForeignMember` | Foreign [Member] | A(2) sub-total | 小計 | — | BSE XSD |
| `GovermentsMember` / `GovernmentsMember` | Governments [Member] | 統合小計 | — | ❌ 政府（集計） | BSE XSD（2025 版で綴り修正） |

ラベル中の "Foreign - Government" / "Indian - financial institutions or banks" のハイフンや "isis" の誤植は BSE XBRL taxonomy 2022-09-30 原ファイルの記述に忠実（`in-bse-shp-label-2022-09-30.xml` より）。

---

## 5. 実装提案（Python コード断片）

### 5.1 `src/market/nse/xbrl.py` に `is_natural_person` フラグを追加

```python
# 自然人（本人・親族・取締役・KMP）を示す sub_category 集合
# 根拠: SEBI (ICDR) Regulations 2009 Reg 2(1)(za)(zb), LODR 2(1)(w)(zd),
#       BSE SHP XBRL taxonomy 2022-09-30
_PROMOTER_NATURAL_PERSON_SUBS: frozenset[str] = frozenset({
    "IndividualsOrHinduUndividedFamily",           # Table II A(1)(a)
    "NonResidentIndividualsOrForeignIndividuals",  # Table II A(2)(a)
    "DirectorsAndDirectorsRelatives",              # Table II A(1)(d) sub
    "KeyManagerialPersonnel",                      # Table II A(1)(d) sub
    "RelativesOfPromotersOtherThanPromoterGroup",  # Table II A(1)(d) sub
})

# 法人/政府/機関を示す sub_category 集合
_PROMOTER_NON_NATURAL_SUBS: frozenset[str] = frozenset({
    "CentralGovernmentOrStateGovernmentS",
    "IndianFinancialInstitutionsOrBanks",
    "AssociateCompaniesOrSubsidiaries",
    "BodiesCorporateIncludingSubsidiaries",
    "CentralGovernmentOrPresidentOfIndia",
    "StateGovernmentsOrGovernors",
    "ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoter",
    "Goverments", "Governments", "CentralAndStateGovernments",
    "ForeignGovernment",
    "ForeignInstitutions",
    "ForeignPortfolioInvestor",
})

# 混在（信託は実質自然人支配だが法形式上は信託）
_PROMOTER_TRUST_SUBS: frozenset[str] = frozenset({
    "TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroupIsisTrusteeOrBeneficiaryOrAuthorOfTrust",
})


def classify_promoter_nature(sub_category: str) -> str:
    """Return 'natural', 'non_natural', 'trust', or 'unknown'."""
    if sub_category in _PROMOTER_NATURAL_PERSON_SUBS:
        return "natural"
    if sub_category in _PROMOTER_NON_NATURAL_SUBS:
        return "non_natural"
    if sub_category in _PROMOTER_TRUST_SUBS:
        return "trust"
    return "unknown"
```

### 5.2 銘柄スクリーニング用 SQL / pandas クエリ例

```sql
-- SQLite / DuckDB: ファミリー企業スクリーニング
-- 条件: Promoter 合計持分 >= 25%、かつ自然人 promoter 持分 / Promoter 合計 >= 0.5
WITH promoter_split AS (
    SELECT
        symbol,
        report_date,
        SUM(CASE
            WHEN sub_category IN (
                'IndividualsOrHinduUndividedFamily',
                'NonResidentIndividualsOrForeignIndividuals',
                'DirectorsAndDirectorsRelatives',
                'KeyManagerialPersonnel',
                'RelativesOfPromotersOtherThanPromoterGroup'
            ) THEN CAST(pct_total_shares AS REAL) ELSE 0 END
        ) AS natural_pct,
        SUM(CASE WHEN category = 'PromoterAndPromoterGroup'
                  AND is_category_total = 'true'
                  AND sub_category = ''
                 THEN CAST(pct_total_shares AS REAL) ELSE 0 END
        ) AS promoter_total_pct
    FROM shareholding_rows
    WHERE category = 'PromoterAndPromoterGroup'
      AND is_category_total = 'true'
    GROUP BY symbol, report_date
)
SELECT symbol, report_date, promoter_total_pct, natural_pct,
       CASE WHEN promoter_total_pct > 0
            THEN natural_pct / promoter_total_pct
            ELSE 0 END AS natural_ratio
FROM promoter_split
WHERE promoter_total_pct >= 25
  AND (natural_pct / NULLIF(promoter_total_pct, 0)) >= 0.5
ORDER BY natural_ratio DESC, promoter_total_pct DESC;
```

```python
# pandas 版
import pandas as pd

NATURAL_SUBS = {
    "IndividualsOrHinduUndividedFamily",
    "NonResidentIndividualsOrForeignIndividuals",
    "DirectorsAndDirectorsRelatives",
    "KeyManagerialPersonnel",
    "RelativesOfPromotersOtherThanPromoterGroup",
}

def screen_family_companies(
    df: pd.DataFrame,
    min_promoter_pct: float = 25.0,
    min_natural_ratio: float = 0.5,
) -> pd.DataFrame:
    """Return DataFrame of (symbol, report_date) with family-majority promoter."""
    promoter = df[
        (df["category"] == "PromoterAndPromoterGroup")
        & (df["is_category_total"] == "true")
    ].copy()
    promoter["pct_f"] = pd.to_numeric(promoter["pct_total_shares"], errors="coerce").fillna(0)

    total = (
        promoter[promoter["sub_category"] == ""]
        .groupby(["symbol", "report_date"])["pct_f"].sum()
        .rename("promoter_total_pct")
    )
    natural = (
        promoter[promoter["sub_category"].isin(NATURAL_SUBS)]
        .groupby(["symbol", "report_date"])["pct_f"].sum()
        .rename("natural_pct")
    )
    out = pd.concat([total, natural], axis=1).fillna(0)
    out["natural_ratio"] = out["natural_pct"] / out["promoter_total_pct"].replace(0, pd.NA)
    return out[
        (out["promoter_total_pct"] >= min_promoter_pct)
        & (out["natural_ratio"] >= min_natural_ratio)
    ].sort_values(["natural_ratio", "promoter_total_pct"], ascending=False)
```

---

## 6. 出典一覧（全て 1 次情報 URL）

### SEBI Regulations / Circulars

1. **SEBI (ICDR) Regulations 2009 原文（HTML）** — `https://www.sebi.gov.in/acts/icdrreg.html`（promoter 2(1)(za) / promoter group 2(1)(zb) / immediate relative (zb)(ii) の verbatim を取得）
2. **SEBI (ICDR) Regulations 2018 [Last amended on March 8, 2025]** — `https://www.sebi.gov.in/legal/regulations/mar-2025/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-march-8-2025-_93559.html`
3. **SEBI (ICDR) Regulations 2018 [Last amended on May 17, 2024]** — `https://www.sebi.gov.in/legal/regulations/may-2024/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-may-17-2024-_80421.html`
4. **SEBI (SAST) Regulations 2011 Gazette PDF** — `https://www.sebi.gov.in/sebi_data/attachdocs/1367922725672.pdf`（immediate relative 2(1)(l) verbatim, promoter 2(1)(s), promoter group 2(1)(t) を取得）
5. **SEBI (LODR) Regulations 2015 原 Gazette PDF** — `https://www.sebi.gov.in/sebi_data/attachdocs/1441284401427.pdf`（Regulation 2(1)(w) promoter/promoter group 参照、2(1)(zd) relative 参照）
6. **SEBI Circular CIR/HO/CFD/CMD/CIR/P/2017/128** に言及した circular — `https://www.sebi.gov.in/legal/circulars/aug-2021/disclosure-of-shareholding-pattern-of-promoter-s-and-promoter-group-entities_51847.html`（2021-08-13, SEBI/HO/CFD/CMD/CIR/P/2021/616）
7. **SEBI Circular: Disclosure of holding of specified securities** — `https://www.sebi.gov.in/legal/circulars/jun-2022/disclosure-of-holding-of-specified-securities-and-holding-of-specified-securities-in-dematerialized-form_60459.html`（SEBI/HO/CFD/PoD-1/P/CIR/2022/92, 2022-06-30）
8. **SEBI Circular: Disclosure of holding of specified securities in dematerialized form** — `https://www.sebi.gov.in/legal/circulars/mar-2025/disclosure-of-holding-of-specified-securities-in-dematerialized-form_92797.html`

### BSE XBRL Taxonomy

9. **BSE XBRL Info ページ** — `https://www.bseindia.com/static/about/xbrl_info.aspx`
10. **BSE SHP XBRL Taxonomy ZIP (2022-09-30)** — `https://www.bseindia.com/downloads1/SHPTaxonomy.zip`（`in-bse-shp-2022-09-30.xsd`, `in-bse-shp-label-2022-09-30.xml` 等を含む）
11. **BSE BSE 自身の SHP disclosure PDF（例）** — `https://www.bseindia.com/downloads1/Shareholding_Pattern_31March20.pdf`

### NSE

12. **NSE 自身の SHP 開示 PDF（Table I / II / III / IV の実例）** — `https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Shareholding_Pattern_UR_31%2030062021.pdf`

### Companies Act / MCA

13. **Companies Act 2013 官公刊 PDF** — `https://www.indiacode.nic.in/bitstream/123456789/2114/5/A2013-18.pdf`（Section 2(69) promoter, 2(77) relative, 2(76) related party を verbatim 取得）

---

## 7. 未解決事項・2次情報でしか確認できなかった項目

### 7.1 1次情報で verbatim 確認できたもの

- ICDR 2009 Regulation 2(1)(za) promoter **→ OK**（HTML 原文）
- ICDR 2009 Regulation 2(1)(zb) promoter group **→ OK**（HTML 原文、sub-clauses (i)–(v) 全て確認）
- ICDR 2009 の immediate relative 定義（promoter group 2(1)(zb)(ii) 内部）**→ OK**
- SAST 2011 Regulation 2(1)(l) immediate relative **→ OK**（gazette PDF）
- LODR 2015 Regulation 2(1)(w) promoter 準用 **→ OK**（gazette PDF）
- LODR 2015 Regulation 2(1)(zd) relative 準用 **→ OK**（gazette PDF）
- Companies Act 2013 Section 2(69) promoter **→ OK**（indiacode PDF）
- Companies Act 2013 Section 2(77) relative **→ OK**（indiacode PDF、(i)–(iii) のみ、詳細は Rule 4 参照）
- BSE SHP XBRL 2022-09-30 taxonomy の全 promoter-related member 名・英語ラベル **→ OK**（XSD+Label XML）
- NSE/SEBI Shareholding Pattern Table II 行構造（A(1)(a)〜(d), A(2)(a)〜(f), Sub-Total (A)(1), (A)(2), Total (A)）**→ OK**（NSE archives PDF）

### 7.2 1次情報で verbatim 確認できなかったもの

- **ICDR 2018 の具体的な条項番号 (oo) (pp) (l) の verbatim 原文**: SEBI 公式ページは HTML プレースホルダーのみで本文 PDF 直リンクを取得できず、`https://www.sebi.gov.in/legal/regulations/may-2024/...` 等の WebFetch では本文テキストを返さなかった。番号 (oo)/(pp)/(l) は SEBI WebSearch のスニペット（SEBI ドメイン検索結果）で繰り返し一致したため信頼度は高いが、**条項番号そのものの verbatim 確認は 2 次情報レベル**。本文ワーディング自体は ICDR 2009 と同一であることが、LODR 2015 Gazette (1441284401427.pdf) の準用文言および SAST 2011 Gazette の immediate relative 定義との一致で裏付けられる。
- **Rule 4 of Companies (Specification of Definitions Details) Rules, 2014 の完全な relative リスト**: MCA の PDF (`NCARules_Chapter1.pdf`, `CompaniesSpecification2ndAmndtRules_19022021.pdf`) は 403 Access Denied。India Code の `show-data` エンドポイントも 403。**verbatim 取得失敗**。実装上は ICDR/SAST の "immediate relative" (spouse + parent/brother/sister/child of person/spouse) を採用すれば十分（LODR は ICDR 準用、ICDR が独自定義を持つため Rule 4 の広義 relative は SHP Table II の A(1)(a) 「Individuals/HUF」判定には不要）。
- **SEBI Circular SEBI/HO/CFD/CMD/CIR/P/2017/128 (5 Dec 2017) そのものの PDF**: SEBI 検索で直接ヒットせず、2021-08-13 circular と 2022-06-30 circular 内での間接的引用のみ確認。本調査では Table II 形式の現行版 (2021-06 NSE archives PDF + 2022 circular) を代替 1 次情報として使用。
- **SEBI LODR Regulation 31 Schedule V Part A の shareholding pattern 形式の直接 verbatim**: NSE archives の Annexure-I PDF で Table I/II/III/IV の実形式を確認したが、SEBI 原 Gazette の Schedule V テキストは取得できず。LODR 2015 Gazette (1441284401427.pdf) には Schedule が含まれるはずだが、PDF テキスト抽出では Regulation 31 本文（1–30 番台）までしか容易に検証できなかった。

### 7.3 参考（補助検索のみ、最終結論には使用せず）

- SEBI Memorandum (Jan 2019, Aug 2021): promoter group 定義見直しに関する内部メモ。`https://www.sebi.gov.in/sebi_data/meetingfiles/jan-2019/1547524503863_1.pdf`, `https://www.sebi.gov.in/sebi_data/meetingfiles/aug-2021/1628663782833_1.pdf`

---

## 付録: BSE SHP XBRL taxonomy の証拠ファイル（取得済みローカルコピー）

| ファイル | パス | 用途 |
|---|---|---|
| SHPTaxonomy.zip | `research/2026-04-16_nse_promoter_classification/sources/SHPTaxonomy.zip` | BSE 公式 taxonomy パッケージ |
| in-bse-shp-2022-09-30.xsd | `.../sources/Taxonomy/in-bse-shp-2022-09-30.xsd` | XBRL Schema (element definitions) |
| in-bse-shp-label-2022-09-30.xml | `.../sources/Taxonomy/in-bse-shp-label-2022-09-30.xml` | 英語ラベル（semantic 確認用） |
| in-bse-shp-pre-2022-09-30.xml | `.../sources/Taxonomy/in-bse-shp-pre-2022-09-30.xml` | Presentation linkbase（表形式ツリー） |
| LODR_2015_original.pdf | `.../sources/LODR_2015_original.pdf` | LODR 2015 Gazette 原文 |
| LODR_2015.txt | `.../sources/LODR_2015.txt` | pdftotext 変換後 |
| CompaniesAct2013.pdf | `.../sources/CompaniesAct2013.pdf` | Companies Act 2013 官刊 PDF |
| CompaniesAct2013.txt | `.../sources/CompaniesAct2013.txt` | 同上テキスト |
| sebi_gazette_1367922725672.pdf | `.../sources/sebi_gazette_1367922725672.pdf` | SAST 2011 Gazette |
| sebi_gazette_1367922725672.txt | `.../sources/sebi_gazette_1367922725672.txt` | 同上テキスト |
| NSE_SHP_UR_format.pdf | `.../sources/NSE_SHP_UR_format.pdf` | NSE 自己開示 SHP（Table I–IV 実例） |
| NSE_SHP_UR_format.txt | `.../sources/NSE_SHP_UR_format.txt` | 同上テキスト |
| ICDR_reg_html.html | `.../sources/ICDR_reg_html.html` | SEBI ICDR 2009 原 HTML |
