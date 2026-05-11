# yaml v0.5.0 — Web 裏取り調査結果 (2026-05-07)

**調査方法**: Tavily/web search で各 P0 銘柄の promoter 構造を裏取り
**確信度**: 🟢 高 (公式資料・複数ソース確認) / 🟡 中 (1 次資料 1 件のみ) / 🔴 低 (情報不足)

---

## 1. WAAREERTL (Waaree Renewable Technologies) — 🟢 Owner 確実

**裏取り**:
- Waaree Energies (親会社) は **Doshi 一族支配** (Hitesh/Kirit/Pankaj/Rushabh/Pujan 等 Doshi 8 名)
- Waaree Energies promoter 64.19% (2026 Mar)、Hitesh Doshi 単独で 11.45%
- Waaree Renewable は Waaree Energies の子会社、同じ Doshi 一族支配
- promoter_names に "HITESH P MEHTA / DOSHI 一族 8 名 / WAAREE ENERGIES LIMITED" あり

**判定**: **Owner**
**yaml カテゴリ**: `owner_keywords`
**追加 keyword**: `WAAREE ENERGIES LIMITED` (固有名詞、副作用なし)

**ソース**: HDFC Sky / Trendlyne / Economic Times

---

## 2. HCG (Healthcare Global Enterprises) — 🟡 Professional 推定 ⚠️ ドラフト訂正

**裏取り (重要訂正)**:
- 2025/02: **KKR が controlling stake 54% を CVC から $400M で取得**完了
- 元創業者 Dr. BS Ajaikumar は **minority position に降格** (Founder & Chairman)
- promoter_names の "HECTOR ASIA HOLDINGS II PTE. LTD." = KKR vehicle
- KKR 取得後は **Professional (PE-controlled)** が妥当

**ドラフト判定 (Owner) は誤り** → **Professional に訂正**

**判定**: **Professional** (KKR PE-backed)
**yaml カテゴリ**: `professional_keywords`
**追加 keyword**: `HECTOR ASIA HOLDINGS` (KKR vehicle、固有性高い)

**注意**: yaml 元案の `AJAIKUMAR` を `owner_keywords` に追加するのは **やめる** べき。Ajaikumar 一族は controlling power を失った。

**ソース**: BusinessWire / KKR press release / Pulse2

---

## 3. THYROCARE (Thyrocare Technologies) — 🟢 Professional 確実

**裏取り**:
- 2021/06: PharmEasy (API Holdings) が **元 promoter A. Velumani から 66.1% 取得** (Rs 6,900 crore)
- Docon Technologies (API 100% 子会社) が acquirer
- Velumani は API Holdings に Rs 1,500cr 再投資 (4.9% stake)、現 promoter 不在
- promoter は API Holdings + Docon Technologies のみ

**判定**: **Professional** (PharmEasy / API Holdings、TPG-Prosus PE-backed)
**yaml カテゴリ**: `professional_keywords`
**追加 keyword**: `API Holdings Limited`、`Docon Technologies`

**ソース**: TechCrunch / Times of India / Economic Times

---

## 4. FEDFINA (Fedbank Financial Services) — 🟢 Professional 確実

**裏取り**:
- The Federal Bank Limited の subsidiary
- IPO 2023/11、依然として Federal Bank が筆頭 promoter
- promoter_names は "The Federal Bank Limited" + Federal Bank 役員数名 (Jointly)

**判定**: **Professional** (Federal Bank、rev1 で Professional 分類済み)
**yaml カテゴリ**: `professional_keywords`
**追加 keyword**: `The Federal Bank Limited`

**ソース**: Moneycontrol / Groww / mStock IPO ページ

---

## 5. AXISCADES (AXISCADES Technologies) — 🟡 Owner 推定

**裏取り**:
- Jupiter Capital Private Limited が promoter (51%)
- Jupiter Capital = **Rajeev Chandrasekhar 1 人が 2005 創業した family office**
- Rajeev Chandrasekhar = 元 Karnataka MP (BJP)、起業家・technocrat
- 一族支配というより**個人投資家の家族企業**だが、Wadia 家・Bajaj 家と同様に family office 系列の Owner と見なすのが筋

**判定**: **Owner** (Chandrasekhar family office)
**yaml カテゴリ**: `owner_keywords`
**追加 keyword**: `JUPITER CAPITAL PRIVATE LIMITED` (固有性高い、AXISCADES のみ)

**ソース**: Wikipedia (Rajeev Chandrasekhar) / MatrixBCG / Planify

---

## 6. REFEX (Refex Industries) — 🟢 Owner 確実

**裏取り**:
- Anil Jain (Executive Chairman & MD) が **Refex Group の創業者・Self-made 起業家**
- promoter_names に Anil Jain T / Dimple Jain / Tarachand Jain / Yash Jain (Jain 一族 5 名) + REFEX HOLDING PRIVATE LIMITED
- 2026/02 SEBI exemption order: Anil Jain が 44.96% を gift で family member へ移転

**判定**: **Owner** (Jain family、Refex Group)
**yaml カテゴリ**: `owner_keywords`
**追加 keyword**: `REFEX HOLDING PRIVATE LIMITED` (固有性高い)

**ソース**: Yahoo Finance / LinkedIn / Medium / SEBI exemption order

---

## 7. GVT&D (GE Vernova T&D India) — 🟢 MNC 確実

**裏取り**:
- 旧 Alstom T&D India。2015 年に GE が Alstom の Power 部門を買収
- promoter: **Grid Equipments Pte. Ltd. (GE 系) が 68.54%**、GE Grid Alliance B.V. (旧 Alstom Grid) が 6.46%
- 2024 年に GE Vernova spin-off で GE Vernova T&D India に改称
- promoter_names は GE Grid Solutions 各国子会社 + Alstom Grid Holding B.V.

**判定**: **MNC** (GE Vernova、米仏多国籍)
**yaml カテゴリ**: `mnc_keywords`
**追加 keyword**: `GE Grid Solutions`、`Grid Equipments`、`Alstom Grid`

**ソース**: ICICI Direct / Economic Times / GE Vernova IR PDF

---

## 8. STYRENIX (Styrenix Performance Materials) — 🟡 Owner 推定 ⚠️ ドラフト訂正

**裏取り (重要訂正)**:
- 旧 **INEOS Styrolution India**。2022 年に **Shiva Performance Materials Private Limited (Vadodara base) が INEOS Styrolution の 61.19% を取得**
- INEOS Group は完全撤退、Shiva Performance Materials が新 promoter (独立した買収者)
- 2024 年には逆に Styrenix が **INEOS の Thailand 事業を $20M で買収** (旧親会社の事業を逆買収)
- Shiva Performance Materials = Vadodara の独立 chemical entrepreneurs (INEOS や Reliance とは無関係)

**ドラフト判定 (要 web 調査) は解消** → **Owner (独立 buyer)**

**判定**: **Owner** (Shiva Performance Materials の独立ファミリー)
**yaml カテゴリ**: `owner_keywords`
**追加 keyword**: `Shiva Performance Materials Private Limited`

**注意**: Vadodara base の chemical entrepreneurs だが具体的な family 名は web 上で特定できず。yaml の note には「buyout via Shiva Performance Materials」と記載。

**ソース**: Indian Chemical News / Styrenix press release / Chemical Week / SMIFS Initiating Coverage

---

## 9. ITCHOTELS (ITC Hotels) — 🟢 Professional 確実

**裏取り**:
- 2025/01/01: ITC Limited から ITC Hotels を **正式 demerger** (1 ITC 株 → 1/10 ITC Hotels)
- ITC Limited が ITC Hotels の **39.85% promoter**
- ITC Limited 自体は **professional management、no active promoter intervention** (BAT/LIC 等の機関分散保有)
- rev1 で ITC Limited は Professional 分類済み → ITC Hotels も同じ

**判定**: **Professional** (ITC Limited)
**yaml カテゴリ**: `professional_keywords`
**追加 keyword**: `ITC Limited`

**ソース**: Finshots / Yahoo Finance / Economic Times / ICICI Direct / ITC IR

---

## 10. JSFB (Jana Small Finance Bank) — 🟢 Professional 確実

**裏取り**:
- Promoters: **Jana Capital Limited + Jana Holdings Limited** (NBFC、Jana Urban Foundation NPO 起源)
- Jana Urban Foundation = NPO、Founder Ramesh Ramanathan が 1999 創業
- 大株主: **TPG Asia VI SF Pte (PE)、Vinod Khosla** 等の institutional 投資家
- 一族支配なし、NPO + PE backed の banking entity

**判定**: **Professional** (NPO + PE-backed、no family)
**yaml カテゴリ**: `professional_keywords`
**追加 keyword**: `JANA CAPITAL`、`JANA HOLDINGS`、`JANA URBAN FOUNDATION`

**ソース**: Jana Bank IR / Moneycontrol / Tracxn

---

## 確信度サマリー

| 確信度 | 件数 | 銘柄 | 採用判定 |
|--------|------|------|---------|
| 🟢 高 | 7 | WAAREERTL, THYROCARE, FEDFINA, REFEX, GVT&D, ITCHOTELS, JSFB | yaml v0.5.0 採用 |
| 🟡 中 | 3 | HCG (KKR 取得), AXISCADES (family office), STYRENIX (独立 buyer) | yaml v0.5.0 採用 (注釈付) |
| 🔴 低 | 0 | — | — |

**全 10 件採用** (元 yaml_v0.5.0_proposal.md からの修正点):

| 項目 | 元案 | 修正版 | 理由 |
|------|------|--------|------|
| HCG | Owner (`AJAIKUMAR`) | **Professional (`HECTOR ASIA HOLDINGS`)** | 2025/02 KKR PE controlling 54% acquisition |
| STYRENIX | 保留 | **Owner (`Shiva Performance Materials Private Limited`)** | 2022 INEOS から独立 buyout |

## 期待効果

| 指標 | 現状 (v0.4.0) | v0.5.0 適用後 (推定) |
|------|---------------|---------------------|
| 圏外 OWNER_WEAK | 13 | **3** (P3 director_only 残のみ) |
| 圏外 OWNER 判定 | 180 | 184 (WAAREERTL/AXISCADES/REFEX/STYRENIX が OWNER 化) |
| 圏外 NOT_OWNER 判定 | 33 | 39 (HCG/THYROCARE/FEDFINA/GVT&D/ITCHOTELS/JSFB が確定) |
| Precision (intersection) | 98.8% | 98.8% (変わらず) |
| Recall (intersection) | 100% | 100% (変わらず) |
