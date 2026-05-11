# yaml v0.5.0 拡張提案 (act-2026-05-07-001 から導出)

**日付**: 2026-05-07
**対象**: rev1 圏外 P0 (OWNER_WEAK 10件) + P1/P2 (確認推奨 18件)
**目的**: 圏外銘柄も含めた NIFTY 750 全 800 銘柄のラベル品質を改善

## P0 (10 件) ユーザー判定推奨

下記の判定はpromoter_names と外部知識ベースのドラフト案。**ユーザー目視で確定後、yaml に追加**。

| symbol | promoter_% | 推奨判定 | 推奨 yaml keyword (case-insensitive substring) | 推奨カテゴリ | 根拠 |
|--------|-----------|---------|----------------------------------------------|------------|------|
| WAAREERTL | 74.3% | **Owner** | `WAAREE ENERGIES LIMITED` | owner_keywords (family: Doshi/Waaree) | Doshi 一族支配の Waaree Group 系。Waaree Energies が筆頭 promoter |
| HCG | 64.2% | **Owner** | `Ajaikumar` | owner_keywords (family: Ajaikumar) | B S Ajaikumar 創業の owner-led 病院グループ。HECTOR ASIA は KKR PE 投資だが Ajaikumar 主導 |
| THYROCARE | 60.9% | **Professional** | `API Holdings Limited` | professional_keywords (parent: PharmEasy/PE) | PharmEasy (API Holdings) が買収済み、TPG/Prosus 等 PE backed |
| FEDFINA | 60.8% | **Professional** | `The Federal Bank Limited` | professional_keywords (parent: Federal Bank) | Federal Bank の subsidiary。Bank-controlled NBFC |
| AXISCADES | 58.0% | **Owner** | `JUPITER CAPITAL` または `Rajeev Chandrasekhar` | owner_keywords (family: Chandrasekhar/Jupiter) | Jupiter Capital = 元 Karnataka MP Rajeev Chandrasekhar の PE。一族 family office |
| REFEX | 55.8% | **Owner** | `REFEX HOLDING` | owner_keywords (family: Jain/Refex) | Anil Jain T 他 Jain 一族支配。"Refex Holding" で固有限定 |
| GVT&D | 51.0% | **MNC** | `GE Grid Solutions` | mnc_keywords (parent: GE Vernova) | GE Vernova T&D India。GE Grid Solutions 各国子会社が promoter group |
| STYRENIX | 46.2% | **要 web check** | (確定後追加) | 要確認 | Shiva Performance Materials 1社のみ。INEOS Reliance JV か独立か要確認 |
| ITCHOTELS | 39.9% | **Professional** | `ITC Limited` | professional_keywords (parent: ITC Ltd) | ITC Limited (rev1=Professional) の spin-off、ITC が 39.85% promoter |
| JSFB | 21.9% | **Professional** | `Jana Capital Limited` または `Jana Holdings Limited` | professional_keywords (parent: Jana Group/PE) | Jana Urban Foundation NPO 起源、TPG/Vinod Khosla PE backed |

## P1 (5 件) — 既に Tier 1.5 救済で OWNER 判定、確認推奨

これらは既に救済済みで概ね Owner family 確定。スポット確認のみ:

| symbol | promoter_% | yaml で既に OWNER マッチ? | 確認ポイント |
|--------|-----------|----------------------------|-------------|
| TRAVELFOOD | 86.2% | UNKNOWN (Kapur family 一族保有) | yaml に "Kapur" or "Talreja" 追加検討 (固有性低い) |
| BHARTIHEXA | 70.0% | OWNER (Mittal/Airtel match ✅) | 救済正解 |
| PFOCUS | 60.8% | UNKNOWN (Malhotra/A2R Holdings) | 既に owner_keywords ambiguous で OWNER 判定 |
| SMLMAH | 59.0% | OWNER (Mahindra match ✅) | 救済正解 |
| KITEX | 56.7% | UNKNOWN (Sabu Jacob family、A-3 で救済) | A-3 自然人検出が有効 |

## P2 (13 件) — 新興上場の Owner family、低 promoter

すべて IPO 後 promoter が薄まった Owner-led スタートアップ・新興企業。Tier 1 個人 promoter が顕在化しているので **判定は妥当**。yaml 追加不要 (一族名は固有性低い):

GROWW (Jain/Aatrey family) / LENSKART (Bansal family) / MEESHO (Aatrey/Bidwai family) / URBANCO (Bhal/Singh family) / BLUESTONE (Kushwaha/Tomar) / AWFIS (Ramani family) / WEBELSOLAR (Agarwal) / A2ZINFRA (Mittal — yaml にあり) / ONESOURCE (Pillai) / AURIONPRO (Sheth/Zaveri) / TDPOWERSYS (Khericha) / BLACKBUCK (Aramvalarthanathan) / WABAG (Varadarajan/Mittal)

## yaml v0.5.0 追加コード (推奨)

```yaml
# === Add to owner_keywords ===
  # --- Waaree Group (Doshi family) ---
  - keyword: "WAAREE ENERGIES LIMITED"
    family: "Doshi (Waaree)"
    sample_stocks: ["WAAREERTL"]
    note: "WAAREERTL: Hitesh/Pankaj/Kirit Doshi 一族支配。Waaree Energies が筆頭 promoter"

  # --- Healthcare Global (Ajaikumar family) ---
  - keyword: "AJAIKUMAR"
    family: "Ajaikumar (HCG)"
    sample_stocks: ["HCG"]
    note: "B S Ajaikumar 創業の owner-led 病院。KKR PE もあるが Ajaikumar 主導"

  # --- AXISCADES (Jupiter Capital / Rajeev Chandrasekhar) ---
  - keyword: "JUPITER CAPITAL PRIVATE LIMITED"
    family: "Chandrasekhar (Jupiter)"
    sample_stocks: ["AXISCADES"]
    note: "元 Karnataka MP Rajeev Chandrasekhar の family office"

  # --- Refex (Jain family) ---
  - keyword: "REFEX HOLDING PRIVATE LIMITED"
    family: "Jain (Refex)"
    sample_stocks: ["REFEX"]
    note: "Anil Jain T 他 Jain 一族の Refex グループ"

# === Add to professional_keywords ===
  # --- Federal Bank (NBFC parent) ---
  - keyword: "The Federal Bank Limited"
    parent: "Federal Bank"
    sample_stocks: ["FEDFINA"]
    note: "FEDFINA = Fedbank Financial Services は Federal Bank の subsidiary"

  # --- ITC Limited (conglomerate parent) ---
  - keyword: "ITC Limited"
    parent: "ITC Limited"
    sample_stocks: ["ITCHOTELS"]
    note: "ITCHOTELS は ITC Limited (rev1=Professional) の spin-off"

  # --- API Holdings (PharmEasy / PE-backed) ---
  - keyword: "API Holdings Limited"
    parent: "PharmEasy / TPG/Prosus PE"
    sample_stocks: ["THYROCARE"]
    note: "Thyrocare は PharmEasy (API Holdings) が買収済み"

  # --- Jana Group ---
  - keyword: "JANA CAPITAL LIMITED"
    parent: "Jana Group / TPG-Khosla PE"
    sample_stocks: ["JSFB"]
  - keyword: "JANA HOLDINGS LIMITED"
    parent: "Jana Group / TPG-Khosla PE"
    sample_stocks: ["JSFB"]
  - keyword: "JANA URBAN FOUNDATION"
    parent: "Jana Group (NPO origin)"
    sample_stocks: ["JSFB"]

# === Add to mnc_keywords ===
  # --- GE Vernova / GE Grid Solutions ---
  - keyword: "GE Grid Solutions"
    parent: "GE Vernova"
    sample_stocks: ["GVT&D"]
    note: "GVT&D = GE Vernova T&D India。GE Grid 各国子会社が promoter group"
  - keyword: "GE Grid"
    parent: "GE Vernova"
    sample_stocks: ["GVT&D"]
  - keyword: "ALSTOM"
    parent: "GE Vernova (旧 Alstom Grid)"
    sample_stocks: ["GVT&D"]
```

## 期待効果 (yaml v0.5.0 適用後)

| 指標 | 現状 (v0.4.0) | v0.5.0 適用後 (推定) |
|------|---------------|---------------------|
| 圏外 OWNER_WEAK | 13 (うち 10 が P0) | 3-4 件まで削減 (STYRENIX 等) |
| 圏外 OWNER 判定 | 180 | 181-182 (WAAREERTL/HCG/AXISCADES/REFEX を Tier 2 hybrid で OWNER 化) |
| 圏外 NOT_OWNER 判定 | 33 | 38-39 (THYROCARE/FEDFINA/ITCHOTELS/JSFB/GVT&D を Professional/MNC で確定) |

## STYRENIX (1件) の追加調査が必要

`Shiva Performance Materials Private Limited` 1 社のみが promoter。Web 調査が必要:
- INEOS Group (英国 MNC) との関係
- Reliance Industries との JV か独立か
- 旧名 INEOS Styrolution India

判定後 yaml に追加。
