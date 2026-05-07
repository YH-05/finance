# rev1 圏外 223 銘柄 — 目視レビュー用レポート

**生成日**: 2026-05-07 / **act-2026-05-07-001**
**対象**: 全 800 銘柄中、rev1 GT 圏外 223 銘柄
**目的**: ground truth 無しの generated label の妥当性をユーザー目視で確認

## 優先度定義

| 優先度 | 定義 | アクション |
|--------|------|----------|
| **P0** | OWNER_WEAK (yaml 未マッチ) | 目視で Owner/Professional/MNC/State を確定 → yaml 追補 |
| **P1** | Tier 1.5 corporate-vehicle rescue で OWNER 化 | 救済が妥当か確認 (NOT_OWNER の可能性) |
| **P2** | 低 promoter (<30%) で OWNER 判定 | 真の Owner か Tier 1 誤流入か判定 |
| **P3** | Tier 2 director_only + yaml 確定 | スポット確認 (大半は正しい) |
| **P4** | Tier 1 高信頼 OWNER または明確 NOT_OWNER | 大量、サンプルチェックのみ |

## 優先度別件数

| 優先度 | 件数 | 推奨レビュー時間 |
|--------|------|-----------------|
| P0 | 10 | 1-2 分/件 |
| P1 | 5 | 1 分/件 |
| P2 | 13 | 30 秒/件 |
| P3 | 9 | 10 秒/件 |
| P4 | 186 | サンプルのみ |

---

## P0 (10 銘柄)

**OWNER_WEAK** — yaml 既知一族リストにマッチせず、Tier 4 で AI レビュー対象だった銘柄。promoter_names を見て Owner/Professional/MNC/State を確定し、yaml v0.5.0 で keyword 追加してください。

| symbol | company | flag (Tier 2) | final | yaml_cls | promoter% | promoter_names (先頭150文字) |
|---|---|---|---|---|---|---|
| WAAREERTL | Waaree Renewable Technologies Limit | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 74.3% | HITESH P MEHTA / BINDIYA KIRIT DOSHI / BINITA H DOSHI / HITESH C DOSHI / KIRIT CHIMANLAL DOSHI / NEEPA VIREN DOSHI / PANKAJ CHIMANLAL DOSHI / PUJAN PANKAJ DOSHI / RUS |
| HCG | Healthcare Global Enterprises Limit | ambiguous_mnc_jv_candidate | OWNER_WEAK | UNKNOWN | 64.2% | AAGNIKA AJAIKUMAR / ANJALI AJAIKUMAR ROSSI / ASMITHA AJAIKUMAR / B S AJAIKUMAR / BHAGYA A AJAIKUMAR / HECTOR ASIA HOLDINGS II PTE. LTD. / CATALYST TRUSTEESHIP LIM |
| THYROCARE | Thyrocare Technologies Limited | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 60.9% | API Holdings Limited / Docon Technologies Private Limited |
| FEDFINA | Fedbank Financial Services Limited | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 60.8% | The Federal Bank Limited / Mr. Ajith Kumar K K Jointly with The Federal Bank Ltd / Mr. Ashutosh Khajuria Jointly with The Federal Bank Ltd / Mr. Divakar Dix |
| AXISCADES | AXISCADES Technologies Limited | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 58.0% | INDIAN AERO VENTURES PRIVATE LIMITED / JUPITER CAPITAL PRIVATE LIMITED |
| REFEX | Refex Industries Limited | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 55.8% | ANIL JAIN T / DIMPLE JAIN / TARACHAND JAIN / UGAMDEVI JAIN / YASH JAIN / REFEX HOLDING PRIVATE LIMITED |
| GVT&D | GE Vernova T&D India Limited | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 51.0% | ALSTOM (Wuxi) Disconnector Co., Ltd. / AO Grid Solutions / COGELEX / FRENCH LIBYAN ELECTRICAL SERVICES COMPANY (FLESCO) / GE GRID SOLUTIONS, S.A. / GE Grid (Sha |
| STYRENIX | Styrenix Performance Materials Limi | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 46.2% | Shiva Performance Materials Private Limited |
| ITCHOTELS | ITC Hotels Limited | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 39.9% | Blazeclan Americas Inc. / Blazeclan Europe SRL. / Blazeclan Technologies Corporation / Blazeclan Technologies Inc. / Blazeclan Technologies LLC / Blazeclan Tech |
| JSFB | Jana Small Finance Bank Limited | owner_confirmed_director_only | OWNER_WEAK | UNKNOWN | 21.9% | JANA CAPITAL LIMITED / JANA HOLDINGS LIMITED / JANA URBAN FOUNDATION |

---

## P1 (5 銘柄)

**Tier 1.5 corporate-vehicle rescue** で `excluded_*` / `ambiguous_*` から OWNER に救済された銘柄。yaml owner_keyword がマッチしていますが、本当に Owner 一族支配かを確認してください。

| symbol | company | flag (Tier 2) | final | yaml_cls | promoter% | promoter_names (先頭150文字) |
|---|---|---|---|---|---|---|
| TRAVELFOOD | Travel Food Services Limited | ambiguous_holding_indian | OWNER | UNKNOWN | 86.2% | Aditi Varun Kapur / Aisha Kapur / Harish Balram Talreja / Inaaya Kapur / Jay Kapur / Karan Kapur / Malti Harish Talreja / Neelu Kapur / Shivani Saahil Murarka / Sunil K |
| BHARTIHEXA | Bharti Hexacom Limited | ambiguous_holding_indian | OWNER | OWNER | 70.0% | Airtel (M) Telesonic Holdings (UK) Limited / Airtel (M) Telesonic Limited / Airtel (Seychelles) Limited / Airtel (Seychelles) Telesonic Limited / Airtel Afric |
| PFOCUS | Prime Focus Limited | ambiguous_mnc_jv_candidate | OWNER | UNKNOWN | 60.8% | Namit Malhotra / Naresh Mahendranath Malhotra / A2R Holdings |
| SMLMAH | SML Mahindra Limited | ambiguous_holding_indian | OWNER | OWNER | 59.0% | Automobili Pininfarina Americas Inc.  (formerly known as Harkey Acquisition, L.L.C., USA ) / Automobili Pininfarina GmbH [Formerly known as Blitz 18-371 |
| KITEX | Kitex Garments Limited | ambiguous_holding_indian | OWNER | UNKNOWN | 56.7% | BOBY M JACOB / KITEX CHILDRENSWEAR LIMITED / RENJITHA JOSEPH / SABU M JACOB |

---

## P2 (13 銘柄)

**低 promoter (<30%) で OWNER 判定** — Tier 1 ロジックで個人 promoter が顕在化しているが、promoter 比率自体が低い銘柄。Murthy/Jhunjhunwala 系の Tier 1 流入と同じ構造的限界の可能性。

| symbol | company | flag (Tier 2) | final | yaml_cls | promoter% | promoter_names (先頭150文字) |
|---|---|---|---|---|---|---|
| ONESOURCE | Onesource Specialty Pharma Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 29.9% | ADITYA ARUN KUMAR / ARUN KUMAR PILLAI / HEMALATHA PILLAI / PADMAKUMAR KARUNAKARAN PILLAI / RAJITHA GOPALAKRISHNAN / SAJITHA PILLAI / VINEETHA MOHANAKUMAR PILLAI / A |
| WEBELSOLAR | Websol Energy System Limited | owner_confirmed_individual | OWNER | UNKNOWN | 29.7% | CHIRANJI LALL AGARWAL / RAJKUMARI AGARWAL / SOHAN LAL AGARWAL / S  L INDUSTRIES PVT LTD / WEBSOL GREEN PROJECTS PRIVATE LIMITED |
| A2ZINFRA | A2Z Infra Engineering Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 28.1% | AMIT MITTAL / DIPALI MITTAL / PRIYA GOEL / DEVDHAR TRADING AND CONSULTANTS PVT. LTD. / MESTRIC CONSULTANTS PRIVATE LIMITED |
| GROWW | Billionbrains Garage Ventures Limit | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 27.8% | Aarav Jain / Aashna Gupta / Advit Singh / Ajay Gupta / Alka Kapse / Anagha Kapse / Avani Keshre / Avni Singh / Bharti Gupta / Harsh Jain / Harsh Jain HUF / Hina Mohnot / Inay |
| AURIONPRO | Aurionpro Solutions Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 26.9% | AJAY DILKUSH SARUPRIA / ASHISH  RAI / AMIT SHETH / ASHISH RAMESH SHETH / BHAVESH ZAVERI / HITESH CHANDULAL ZAVERI / NALINI RAMESH SHETH / NIHARIKA B ZAVERI / RAMESH L |
| TDPOWERSYS | TD Power Systems Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 26.9% | Mohib Nomanbhai Khericha / Nikhil Kumar / Hitoshi  Matsuo / Aarya Sankaran Kumar / Chartered Capital & Investment Ltd / Sagir Mohib Khericha / Saphire Finman Serv |
| BLACKBUCK | BLACKBUCK LIMITED | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 25.1% | Amurugam A Aramvalarthanathan / Anusha Thummala / Apurva Jain / Arumugam Pillai Aramvalarthanathan / Balasubramaniam Easwaramurthy / Balasubramaniam Ramasubrama |
| URBANCO | Urban Company Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 20.3% | Abhiraj Singh Bhal / Ashok Bhal / Deepa Shah / Deepak Kanwar / Deepak Kanwar & Sons HUF / Dev Khaitan / Har Sharan Singh / Ira Singh Bhal / Manali Singh / Monika Singh /  |
| WABAG | VA Tech Wabag Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 19.1% | VARADARAJAN S / RAJIV MITTAL |
| LENSKART | Lenskart Solutions Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 17.6% | Amit Chaudhary / Amit Mittal / Ankit Chaudhary / Bal Kishan Bansal / Bal Kishan Bansal HUF / Ivaan Bansal / Kanika Gupta / Kartik Kapahi / Kiran Bansal / Manu Singal / Ma |
| AWFIS | Awfis Space Solutions Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 17.0% | AMIT RAMANI / Anya Ramani / Deepa Devnani / Kewal Ramani Bhagwan / Lakshmi Kewal Ramani / MONEESHA RAMANI / Nitesh Devnani / Prem Devnani / Vipin Ramani / BLR Investmen |
| MEESHO | Meesho Limited | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 16.6% | Ahilya Devi / Annie Sebi Menachery / Ashika Raj / Avyaan Barnwal / Chandramohan Prasad / Ira Margeret Aatrey / Karnika Raj / Mamta Devi / Minu Margeret / Nisi Ann Mary  |
| BLUESTONE | BlueStone Jewellery and Lifestyle L | owner_confirmed_individual_and_director | OWNER | UNKNOWN | 16.4% | ARPITA TOMAR / Anurag Tomar / Arvind Pratap Singh Tomar / GAURAV SINGH KUSHWAHA / Kayna Singh Kushwaha / Mina Tomar / Nivaan Singh Kushwaha / Prabha Kushwaha / Prasha |

---

## P3 (9 銘柄)

**Tier 2 director_only + yaml 確定** — yaml が OWNER/PROFESSIONAL/STATE/MNC のいずれかにマッチして確定済み。サンプルでスポット確認するのみで OK。

| symbol | company | flag (Tier 2) | final | yaml_cls | promoter% | promoter_names (先頭150文字) |
|---|---|---|---|---|---|---|
| AEGISVOPAK | Aegis Vopak Terminals Limited | owner_confirmed_director_only | OWNER | OWNER | 86.9% | ASIA INFRASTRUCTURE INVESTMENT  LIMITED / Aegis Group International Pte Limited / Aegis International Marine Services Pte Limited / B V Maatschappij Bierhav |
| BAJAJHFL | Bajaj Housing Finance Limited | owner_confirmed_director_only | OWNER | OWNER | 86.7% | Sanjivnayan Bajaj / Bajaj Technology Services Inc / VH International LLC / Bajaj AIF Trustee Limited / Bajaj Alternate Investment Management Limited / Bajaj Fin |
| TATACAP | Tata Capital Limited | owner_confirmed_director_only | NOT_OWNER | PROFESSIONAL | 85.4% | 3-101-951221 SOCIEDAD ANONIMA / 915 Labs Inc / AFCL Ghana Limited / AFCL Premium Services Limited / AFCL RSA Pty Limited / AFCL Zambia Limited / Agratas LLC / Agrat |
| HDBFS | HDB Financial Services Limited | owner_confirmed_director_only | NOT_OWNER | PROFESSIONAL | 74.2% | Griha Investments / Griha Pte Limited / HDFC AMC International (IFSC) Limited / HDFC Asset Management Company Limited / HDFC Capital Advisors Limited / HDFC ERG |
| TATAINVEST | Tata Investment Corporation Limited | owner_confirmed_director_only | NOT_OWNER | PROFESSIONAL | 73.4% | 3-101-951221 SOCIEDAD ANONIMA / 915 Labs Inc / AFCL Ghana Ltd. / AFCL Premium Services Ltd. / AFCL RSA (Pty) Limited / AFCL Zambia Ltd. / AI Fleet Services IFSC L |
| CANHLIFE | Canara HSBC Life Insurance Company  | owner_confirmed_director_only | NOT_OWNER | STATE | 62.0% | HSBC INSURANCE (ASIA-PACIFIC) HOLDINGS LIMITED / CANARA BANK / Canara Tanzania Limited / HSBC FinTech Services (Shanghai) Company Limited / HSBC Financial Adv |
| TATATECH | Tata Technologies Limited | owner_confirmed_director_only | NOT_OWNER | PROFESSIONAL | 55.2% | AWC Industries Limited / Bowler Motors Limited / Cambric Limited / Changshu Tata Autocomp Systems Limited / Chery Jaguar Land Rover Auto Sales Company Limited |
| MAHSCOOTER | Maharashtra Scooters Limited | owner_confirmed_director_only | OWNER | OWNER | 51.0% | Aarav Swamy / Aryan Bajaj / DEEPA BAJAJ / GEETIKA BAJAJ / KIRAN BAJAJ / KUMUD BAJAJ / Kriti Bajaj / MINAL BAJAJ / NEELIMA BAJAJ SWAMY / NIMISHA JAIPURIA / NIRAJ BAJAJ / NIR |
| TMCV | Tata Motors Limited | owner_confirmed_director_only | NOT_OWNER | PROFESSIONAL | 42.6% | 3-101-951221 SOCIEDAD ANONIMA / 915 Labs Inc / AFCL Ghana Ltd / AFCL Premium Services Ltd. / AFCL RSA (Pty) Limited / AFCL Zambia Ltd / Agratas LLC / Agratas Limite |

---

## P4 (186 銘柄) — 低優先度

Tier 1 高信頼 OWNER または明確 NOT_OWNER の銘柄群。サンプルのみ確認推奨。

### owner_flag 分布

| owner_flag | 件数 |
|---|---|
| owner_confirmed_individual_and_director | 109 |
| owner_confirmed_individual | 49 |
| excluded_no_natural_no_holding | 15 |
| ambiguous_holding_foreign | 7 |
| ambiguous_holding_indian | 3 |
| excluded_state_dominant | 2 |
| owner_probable_nri_family | 1 |

### owner_flag_final_hybrid 分布

| final | 件数 |
|---|---|
| OWNER | 159 |
| NOT_OWNER | 27 |

**詳細は `rev1_outside_review.csv` を Excel で開いて priority=P4 でフィルタ**
