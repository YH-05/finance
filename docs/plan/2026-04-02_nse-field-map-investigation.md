# NSE API フィールドマップ調査結果

**調査日**: 2026-04-02
**Issue**: #3871
**対象銘柄**: INFY（Infosys Limited）

## 調査エンドポイント一覧

| エンドポイント | ファイル |
|--------------|---------|
| `/api/results-comparision?symbol=INFY` | `data/raw/nse/results_comparision_INFY.json` |
| `/api/quote-equity?symbol=INFY` | `data/raw/nse/quote_equity_INFY.json` |
| `/api/equity-stockIndices?index=NIFTY 50` | `data/raw/nse/equity_stockIndices_NIFTY50.json` |
| `/api/event-calendar` | `data/raw/nse/event_calendar.json` |

---

## 1. FINANCIAL_FIELD_MAP（完全版）

**エンドポイント**: `/api/results-comparision?symbol=INFY`
**レスポンス構造**: `{ "resCmpData": [...], "bankNonBnking": "N" }`
**フラグ**: `bankNonBnking` — `"N"` = 非金融企業, `"B"` = 銀行（銀行用フィールドは異なる）

### 全フィールド一覧（63フィールド）

| APIキー | 推奨スネークケース名 | 説明 | INFY実績値 (Q3 FY25) | nullableか |
|---------|-----------------|------|---------------------|-----------|
| `re_to_dt` | `period_to` | 四半期終了日 | `"31-DEC-2024"` | No |
| `re_from_dt` | `period_from` | 四半期開始日 | `"01-OCT-2024"` | No |
| `re_create_dt` | `created_date` | レコード作成日 | `"16-JAN-2025"` | No |
| `re_res_type` | `result_type` | 決算種別（A=監査済, U=未監査） | `"A"` | No |
| `re_seq_num` | `seq_num` | シーケンス番号 | `"1189815"` | No |
| `re_net_sale` | `net_sales` | 純売上高（千ルピー） | `"3491500"` | No |
| `re_total_inc` | `total_income` | 総収益（一部銘柄のみ） | `null` | Yes |
| `re_tot_inc` | `total_income_alt` | 総収益（別フィールド） | `"3591600"` (re_total_inc) | Yes |
| `re_oth_inc_new` | `other_income` | その他収益 | `"100100"` | Yes |
| `re_oth_inc` | `other_income_legacy` | その他収益（旧フィールド） | `null` | Yes |
| `re_staff_cost` | `staff_cost` | 人件費 | `"1684900"` | No |
| `re_oth_exp` | `other_expenditure` | その他費用 | `"951200"` | No |
| `re_rawmat_consump` | `raw_material_consumption` | 原材料消費（製造業向け） | `"0"` | No |
| `re_pur_trd_goods` | `purchase_traded_goods` | 商品仕入 | `"0"` | No |
| `re_inc_dre_sttr` | `change_in_stock` | 在庫変動 | `"0"` | No |
| `re_int_new` | `interest_expense` | 支払利息 | `"5000"` | No |
| `re_int_expd` | `interest_expended` | 支払利息（銀行用） | `null` | Yes |
| `re_depr_und_exp` | `depreciation` | 減価償却費 | `"66100"` | No |
| `re_oth_tot_exp` | `total_other_expenditure` | その他費用合計 | `"2707200"` | No |
| `re_tot_exp_exc_pro_cont` | `total_exp_excl_provisions` | 引当金除く費用合計（銀行用） | `null` | Yes |
| `re_oper_exp` | `operating_expenditure` | 営業費用（銀行用） | `null` | Yes |
| `re_oper_exp_bef_pro_cont` | `op_exp_before_provisions` | 引当金前営業費用（銀行用） | `null` | Yes |
| `re_pro_loss_bef_tax` | `profit_before_tax` | 税前利益 | `"884400"` | No |
| `re_pro_loss_bef_tax_sum` | `profit_before_tax_sum` | 税前利益合計（一部銘柄） | `null` | Yes |
| `re_curr_tax` | `current_tax` | 当期税 | `"278500"` | No |
| `re_deff_tax` | `deferred_tax` | 繰延税 | `"-29900"` | Yes |
| `re_tax` | `tax` | 法人税合計 | `"248600"` | No |
| `re_tax_expens_of_dis_opr` | `tax_discontinued_ops` | 非継続事業税 | `"0"` | No |
| `re_net_profit` | `net_profit` | 当期純利益 | `"635800"` | No |
| `re_con_pro_loss` | `consolidated_profit_loss` | 連結純損益 | `"635800"` | No |
| `re_proloss_ord_act` | `profit_loss_ordinary` | 経常活動損益 | `"635800"` | No |
| `re_pro_los_frm_dis_opr` | `profit_discontinued_ops` | 非継続事業損益 | `"0"` | No |
| `re_prolos_dis_opr_aftr_tax` | `profit_discontinued_after_tax` | 非継続事業税後損益 | `"0"` | No |
| `re_minority_int` | `minority_interest` | 少数株主持分 | `null` | Yes |
| `re_share_associate` | `share_of_associates` | 関連会社持分 | `"0"` | No |
| `re_basic_eps_for_cont_dic_opr` | `eps_basic` | 基本EPS（継続事業） | `"15.31"` | No |
| `re_dilut_eps_for_cont_dic_opr` | `eps_diluted` | 希薄化EPS（継続事業） | `"15.29"` | No |
| `re_basic_eps` | `eps_basic_legacy` | 基本EPS（旧フィールド） | `null` | Yes |
| `re_diluted_eps` | `eps_diluted_legacy` | 希薄化EPS（旧フィールド） | `null` | Yes |
| `re_bsc_eps_bfr_exi` | `eps_basic_before_extraordinary` | 特別項目前基本EPS | `null` | Yes |
| `re_dil_eps_bfr_exi` | `eps_diluted_before_extraordinary` | 特別項目前希薄化EPS | `null` | Yes |
| `re_face_val` | `face_value` | 額面価格 | `"5"` | No |
| `re_face_value_debt` | `face_value_debt` | 負債額面価格（銀行用） | `null` | Yes |
| `re_pdup` | `paid_up_capital` | 払込資本 | `"207500"` | No |
| `re_extraord_items` | `extraordinary_items` | 特別損益 | `null` | Yes |
| `re_excepn_items` | `exceptional_items` | 例外的項目（旧） | `null` | Yes |
| `re_excepn_items_new` | `exceptional_items_new` | 例外的項目（新） | `"0"` | No |
| `re_pro_aft_int_bef_excep` | `profit_after_int_before_exceptional` | 利払い後例外前利益 | `null` | Yes |
| `re_oth_pro_cont` | `other_provisions` | その他引当金（銀行用） | `null` | Yes |
| `re_oth_oper_exp` | `other_operating_expenses` | その他営業費用 | `null` | Yes |
| `re_oth` | `other_misc` | その他雑費 | `null` | Yes |
| `re_int_earned` | `interest_earned` | 受取利息（銀行用） | `null` | Yes |
| `re_int_dis_adv_bills` | `interest_discounted_bills` | 手形割引利息（銀行用） | `null` | Yes |
| `re_income_inv` | `income_from_investments` | 投資収益（銀行用） | `null` | Yes |
| `re_grs_npa` | `gross_npa` | 総不良資産（銀行用） | `null` | Yes |
| `re_grs_npa_per` | `gross_npa_percent` | 総不良資産比率（銀行用） | `null` | Yes |
| `re_per_grs_npa` | `per_gross_npa` | 総NPA比率（銀行用・別） | `null` | Yes |
| `re_bal_rbi_oth_bnk_funds` | `balance_rbi_funds` | RBI資金残高（銀行用） | `null` | Yes |
| `re_cap_ade_rat` | `capital_adequacy_ratio` | 自己資本比率（銀行用） | `null` | Yes |
| `re_cet_1_ret` | `cet1_ratio` | CET1比率（銀行用） | `null` | Yes |
| `re_int_ser_cov` | `interest_service_coverage` | 利息カバレッジ（銀行用） | `null` | Yes |
| `re_debt_ser_cov` | `debt_service_coverage` | 債務カバレッジ（銀行用） | `null` | Yes |
| `re_debt_eqt_rat` | `debt_equity_ratio` | 負債自己資本比率（銀行用） | `null` | Yes |
| `re_paid_debt` | `paid_debt` | 払込負債（銀行用） | `null` | Yes |
| `re_debt_rdmption` | `debt_redemption` | 負債償還（銀行用） | `null` | Yes |
| `re_ret_asset` | `return_on_assets` | 総資産収益率 | `null` | Yes |
| `re_goi_per_shhd` | `govt_holding_percent` | 政府持株比率 | `null` | Yes |
| `re_amt_grs_np_asst` | `gross_np_assets` | 総NP資産額（銀行用） | `null` | Yes |
| `re_prov_emp_pay` | `provisions_employee_pay` | 従業員給与引当金 | `null` | Yes |
| `re_res_reval` | `revaluation_reserve` | 再評価積立金 | `null` | Yes |
| `re_desc_note_seg` | `note_segment` | セグメント注記 | `"-"` | No |
| `re_desc_note_fin` | `note_financial` | 財務注記 | `"-"` | No |
| `re_notes_to_ac` | `notes_to_accounts` | 勘定科目注記 | `""` | No |
| `re_remarks` | `remarks` | 備考 | `null` | Yes |
| `re_seg_remarks` | `segment_remarks` | セグメント備考 | `null` | Yes |

### 実装用 FINANCIAL_FIELD_MAP（非 nullable フィールドのコアセット）

```python
FINANCIAL_FIELD_MAP: Final[dict[str, str]] = {
    # 期間
    "re_from_dt": "period_from",
    "re_to_dt": "period_to",
    "re_create_dt": "created_date",
    "re_res_type": "result_type",
    "re_seq_num": "seq_num",
    # 収益
    "re_net_sale": "net_sales",
    "re_oth_inc_new": "other_income",
    "re_total_inc": "total_income",      # 注: 一部銘柄は null、re_oth_inc_new + re_net_sale で計算可
    # 費用
    "re_staff_cost": "staff_cost",
    "re_oth_exp": "other_expenditure",
    "re_rawmat_consump": "raw_material_consumption",
    "re_pur_trd_goods": "purchase_traded_goods",
    "re_inc_dre_sttr": "change_in_stock",
    "re_int_new": "interest_expense",
    "re_depr_und_exp": "depreciation",
    "re_oth_tot_exp": "total_other_expenditure",
    # 利益
    "re_pro_loss_bef_tax": "profit_before_tax",
    "re_curr_tax": "current_tax",
    "re_deff_tax": "deferred_tax",
    "re_tax": "tax",
    "re_net_profit": "net_profit",
    "re_con_pro_loss": "consolidated_profit_loss",
    "re_proloss_ord_act": "profit_loss_ordinary",
    "re_pro_los_frm_dis_opr": "profit_discontinued_ops",
    "re_prolos_dis_opr_aftr_tax": "profit_discontinued_after_tax",
    "re_tax_expens_of_dis_opr": "tax_discontinued_ops",
    # EPS
    "re_basic_eps_for_cont_dic_opr": "eps_basic",
    "re_dilut_eps_for_cont_dic_opr": "eps_diluted",
    # 資本
    "re_face_val": "face_value",
    "re_pdup": "paid_up_capital",
    "re_share_associate": "share_of_associates",
    "re_excepn_items_new": "exceptional_items",
    # 注記
    "re_desc_note_seg": "note_segment",
    "re_desc_note_fin": "note_financial",
    "re_notes_to_ac": "notes_to_accounts",
}

# 銀行・金融機関専用フィールド（bankNonBnking == "B" の場合のみ有効）
FINANCIAL_FIELD_MAP_BANK: Final[dict[str, str]] = {
    "re_int_earned": "interest_earned",
    "re_int_expd": "interest_expended",
    "re_int_dis_adv_bills": "interest_discounted_bills",
    "re_income_inv": "income_from_investments",
    "re_grs_npa": "gross_npa",
    "re_grs_npa_per": "gross_npa_percent",
    "re_per_grs_npa": "per_gross_npa",
    "re_bal_rbi_oth_bnk_funds": "balance_rbi_funds",
    "re_cap_ade_rat": "capital_adequacy_ratio",
    "re_cet_1_ret": "cet1_ratio",
    "re_int_ser_cov": "interest_service_coverage",
    "re_debt_ser_cov": "debt_service_coverage",
    "re_debt_eqt_rat": "debt_equity_ratio",
    "re_paid_debt": "paid_debt",
    "re_debt_rdmption": "debt_redemption",
    "re_face_value_debt": "face_value_debt",
    "re_tot_exp_exc_pro_cont": "total_exp_excl_provisions",
    "re_oper_exp": "operating_expenditure",
    "re_oper_exp_bef_pro_cont": "op_exp_before_provisions",
    "re_oth_pro_cont": "other_provisions",
}
```

---

## 2. QUOTE_FIELD_MAP（quote-equity）

**エンドポイント**: `/api/quote-equity?symbol=INFY`

### レスポンス構造

```
{
  "info": { ... }         # 基本情報（静的）
  "metadata": { ... }     # メタデータ（PE, セクター等）
  "securityInfo": { ... } # 証券情報
  "sddDetails": { ... }   # SDD（追加開示）
  "currentMarketType": "NM"
  "priceInfo": { ... }    # 価格データ（動的）
  "industryInfo": { ... } # 業種情報
  "preOpenMarket": { ... } # プレオープン
}
```

### info フィールド

| APIキー | 推奨名 | 説明 |
|--------|--------|------|
| `symbol` | `symbol` | ティッカー |
| `companyName` | `company_name` | 会社名 |
| `industry` | `industry` | 業種（詳細） |
| `activeSeries` | `active_series` | アクティブシリーズ |
| `debtSeries` | `debt_series` | 負債シリーズ |
| `isFNOSec` | `is_fno` | F&O対象 |
| `isCASec` | `is_ca` | 資本行動対象 |
| `isSLBSec` | `is_slb` | SLB対象 |
| `isDebtSec` | `is_debt` | 負債証券 |
| `isSuspended` | `is_suspended` | 取引停止 |
| `isETFSec` | `is_etf` | ETF |
| `isDelisted` | `is_delisted` | 上場廃止 |
| `isin` | `isin` | ISINコード |
| `listingDate` | `listing_date` | 上場日 |
| `segment` | `segment` | セグメント（EQUITY等） |
| `identifier` | `identifier` | 内部識別子 |

### metadata フィールド

| APIキー | 推奨名 | 説明 |
|--------|--------|------|
| `series` | `series` | シリーズ（EQ等） |
| `status` | `status` | 上場状態 |
| `lastUpdateTime` | `last_update_time` | 最終更新時刻 |
| `pdSectorPe` | `sector_pe` | セクターPER |
| `pdSymbolPe` | `symbol_pe` | 銘柄PER |
| `pdSectorInd` | `sector_index` | セクターインデックス |
| `pdSectorIndAll` | `sector_indices` | 全所属インデックス |

### priceInfo フィールド

| APIキー | 推奨名 | 説明 |
|--------|--------|------|
| `lastPrice` | `last_price` | 直近価格 |
| `change` | `change` | 変動額 |
| `pChange` | `pct_change` | 変動率 |
| `previousClose` | `prev_close` | 前日終値 |
| `open` | `open` | 始値 |
| `close` | `close` | 終値（0=未確定） |
| `vwap` | `vwap` | 出来高加重平均価格 |
| `lowerCP` | `lower_circuit` | 下限サーキットブレーカー |
| `upperCP` | `upper_circuit` | 上限サーキットブレーカー |
| `basePrice` | `base_price` | 基準価格 |
| `intraDayHighLow.min` | `day_low` | 当日安値 |
| `intraDayHighLow.max` | `day_high` | 当日高値 |
| `weekHighLow.min` | `year_low` | 52週安値 |
| `weekHighLow.max` | `year_high` | 52週高値 |
| `weekHighLow.minDate` | `year_low_date` | 52週安値日 |
| `weekHighLow.maxDate` | `year_high_date` | 52週高値日 |
| `tickSize` | `tick_size` | 呼値単位 |

### securityInfo フィールド

| APIキー | 推奨名 | 説明 |
|--------|--------|------|
| `faceValue` | `face_value` | 額面価格 |
| `issuedSize` | `issued_size` | 発行株数 |
| `derivatives` | `has_derivatives` | デリバティブ対象 |
| `slb` | `slb_eligible` | SLB適格 |
| `boardStatus` | `board_status` | Main/SME等 |
| `tradingStatus` | `trading_status` | Active等 |
| `tradingSegment` | `trading_segment` | Normal Market等 |

### industryInfo フィールド

| APIキー | 推奨名 | 説明 |
|--------|--------|------|
| `macro` | `macro_sector` | マクロセクター |
| `sector` | `sector` | セクター |
| `industry` | `industry` | 業種 |
| `basicIndustry` | `basic_industry` | 詳細業種 |

### 実装用マッピング辞書

```python
QUOTE_INFO_FIELD_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "companyName": "company_name",
    "industry": "industry",
    "isFNOSec": "is_fno",
    "isSLBSec": "is_slb",
    "isDebtSec": "is_debt",
    "isSuspended": "is_suspended",
    "isETFSec": "is_etf",
    "isDelisted": "is_delisted",
    "isin": "isin",
    "listingDate": "listing_date",
    "segment": "segment",
    "identifier": "identifier",
}

QUOTE_PRICE_FIELD_MAP: Final[dict[str, str]] = {
    "lastPrice": "last_price",
    "change": "change",
    "pChange": "pct_change",
    "previousClose": "prev_close",
    "open": "open",
    "vwap": "vwap",
    "lowerCP": "lower_circuit",
    "upperCP": "upper_circuit",
    "basePrice": "base_price",
    "tickSize": "tick_size",
}

QUOTE_METADATA_FIELD_MAP: Final[dict[str, str]] = {
    "series": "series",
    "status": "status",
    "pdSectorPe": "sector_pe",
    "pdSymbolPe": "symbol_pe",
    "pdSectorInd": "sector_index",
}

QUOTE_SECURITY_FIELD_MAP: Final[dict[str, str]] = {
    "faceValue": "face_value",
    "issuedSize": "issued_size",
    "boardStatus": "board_status",
    "tradingStatus": "trading_status",
}

QUOTE_INDUSTRY_FIELD_MAP: Final[dict[str, str]] = {
    "macro": "macro_sector",
    "sector": "sector",
    "industry": "industry",
    "basicIndustry": "basic_industry",
}
```

---

## 3. INDEX_FIELD_MAP（equity-stockIndices）

**エンドポイント**: `/api/equity-stockIndices?index=NIFTY 50`

### 構成銘柄（data[1..N]）フィールド

| APIキー | 推奨名 | 説明 |
|--------|--------|------|
| `symbol` | `symbol` | ティッカー |
| `identifier` | `identifier` | 内部識別子 |
| `series` | `series` | シリーズ（EQ等） |
| `open` | `open` | 始値 |
| `dayHigh` | `day_high` | 当日高値 |
| `dayLow` | `day_low` | 当日安値 |
| `lastPrice` | `last_price` | 直近価格 |
| `previousClose` | `prev_close` | 前日終値 |
| `change` | `change` | 変動額 |
| `pChange` | `pct_change` | 変動率 |
| `totalTradedVolume` | `volume` | 出来高 |
| `totalTradedValue` | `traded_value` | 売買代金 |
| `yearHigh` | `year_high` | 52週高値 |
| `yearLow` | `year_low` | 52週安値 |
| `ffmc` | `free_float_mkt_cap` | 浮動株時価総額 |
| `nearWKH` | `pct_from_year_high` | 52週高値からの乖離率 |
| `nearWKL` | `pct_from_year_low` | 52週安値からの乖離率 |
| `perChange365d` | `pct_change_365d` | 365日変動率 |
| `perChange30d` | `pct_change_30d` | 30日変動率 |
| `stockIndClosePrice` | `index_close_price` | インデックス終値参照 |
| `priority` | `priority` | 優先度（インデックス=1, 銘柄=0） |
| `meta.symbol` | - | 銘柄基本情報（info と同等） |
| `meta.companyName` | - | 会社名 |
| `meta.isin` | - | ISINコード |

### インデックス全体（metadata）フィールド

| APIキー | 推奨名 | 説明 |
|--------|--------|------|
| `indexName` | `index_name` | インデックス名 |
| `open` | `open` | 始値 |
| `high` | `high` | 高値 |
| `low` | `low` | 安値 |
| `previousClose` | `prev_close` | 前日終値 |
| `last` | `last` | 直近値 |
| `percChange` | `pct_change` | 変動率 |
| `change` | `change` | 変動額 |
| `timeVal` | `time` | 時刻 |
| `yearHigh` | `year_high` | 52週高値 |
| `yearLow` | `year_low` | 52週安値 |
| `totalTradedVolume` | `volume` | 総出来高 |
| `totalTradedValue` | `traded_value` | 総売買代金 |
| `ffmc_sum` | `free_float_mkt_cap` | 総浮動株時価総額 |
| `perChange365d` | `pct_change_365d` | 365日変動率 |
| `perChange30d` | `pct_change_30d` | 30日変動率 |

### 実装用マッピング辞書

```python
INDEX_CONSTITUENT_FIELD_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "identifier": "identifier",
    "series": "series",
    "open": "open",
    "dayHigh": "day_high",
    "dayLow": "day_low",
    "lastPrice": "last_price",
    "previousClose": "prev_close",
    "change": "change",
    "pChange": "pct_change",
    "totalTradedVolume": "volume",
    "totalTradedValue": "traded_value",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "ffmc": "free_float_mkt_cap",
    "nearWKH": "pct_from_year_high",
    "nearWKL": "pct_from_year_low",
    "perChange365d": "pct_change_365d",
    "perChange30d": "pct_change_30d",
}

INDEX_METADATA_FIELD_MAP: Final[dict[str, str]] = {
    "indexName": "index_name",
    "open": "open",
    "high": "high",
    "low": "low",
    "previousClose": "prev_close",
    "last": "last",
    "percChange": "pct_change",
    "change": "change",
    "timeVal": "time",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "totalTradedVolume": "volume",
    "totalTradedValue": "traded_value",
    "ffmc_sum": "free_float_mkt_cap",
    "perChange365d": "pct_change_365d",
    "perChange30d": "pct_change_30d",
}
```

---

## 4. EVENT_CALENDAR_FIELD_MAP（event-calendar）

**エンドポイント**: `/api/event-calendar`
**レスポンス構造**: フラットな配列（`[{...}, {...}]`）
**件数**: 98件（調査時点）

### フィールド一覧

| APIキー | 推奨名 | 説明 | サンプル値 |
|--------|--------|------|----------|
| `symbol` | `symbol` | ティッカー | `"EFCIL"` |
| `company` | `company_name` | 会社名 | `"EFC (I) Limited"` |
| `purpose` | `purpose` | イベント目的 | `"Fund Raising"` |
| `bm_desc` | `description` | 詳細説明 | `"Intimation of Board Meeting."` |
| `date` | `date` | イベント日付 | `"03-Apr-2026"` |

### 実装用マッピング辞書

```python
EVENT_CALENDAR_FIELD_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "company": "company_name",
    "purpose": "purpose",
    "bm_desc": "description",
    "date": "date",
}
```

---

## 5. FinancialResult データクラス設計確定版

上記調査に基づき、`types.py` の `FinancialResult` を以下に確定：

```python
@dataclass(frozen=True)
class FinancialResult:
    """四半期決算データ。

    NSE /api/results-comparision レスポンスの resCmpData[] 1エントリに対応。
    単位: 千ルピー（net_sales, costs, profits）。

    Notes
    -----
    - is_bank=True の場合、銀行専用フィールド（interest_earned 等）が有効
    - eps_basic / eps_diluted は継続事業ベース（for_cont_dic_opr）
    - total_income は net_sales + other_income で計算（APIでは null の場合あり）
    """
    symbol: str
    period_from: str          # "DD-MMM-YYYY"
    period_to: str            # "DD-MMM-YYYY"
    result_type: str          # "A"=Audited, "U"=UnAudited
    # 収益
    net_sales: float | None
    other_income: float | None
    # 費用
    staff_cost: float | None
    other_expenditure: float | None
    interest_expense: float | None
    depreciation: float | None
    total_other_expenditure: float | None
    # 利益
    profit_before_tax: float | None
    tax: float | None
    net_profit: float | None
    consolidated_profit_loss: float | None
    # EPS
    eps_basic: float | None
    eps_diluted: float | None
    # 資本
    face_value: float | None
    paid_up_capital: float | None
    # メタ
    created_date: str | None = None
    seq_num: str | None = None
    is_bank: bool = False
```

---

## 6. StockQuote データクラス設計確定版

```python
@dataclass(frozen=True)
class StockQuote:
    """個別銘柄気配値。

    NSE /api/quote-equity レスポンスを正規化したデータクラス。
    """
    symbol: str
    company_name: str
    isin: str
    series: str
    # 価格
    last_price: float
    prev_close: float
    open: float
    day_high: float
    day_low: float
    vwap: float
    year_high: float
    year_low: float
    year_high_date: str
    year_low_date: str
    lower_circuit: str
    upper_circuit: str
    # バリュエーション
    sector_pe: float | None
    symbol_pe: float | None
    # 基本情報
    listing_date: str
    face_value: float
    issued_size: int
    # 業種分類
    macro_sector: str
    sector: str
    industry: str
    basic_industry: str
    # フラグ
    is_fno: bool
    is_slb: bool
    is_suspended: bool
    # インデックス所属
    sector_index: str
    sector_indices: list[str]
```

---

## 7. IndexConstituent データクラス設計確定版

```python
@dataclass(frozen=True)
class IndexConstituent:
    """インデックス構成銘柄データ。

    NSE /api/equity-stockIndices レスポンスの data[] エントリ（銘柄分）に対応。
    """
    symbol: str
    identifier: str
    series: str
    open: float
    day_high: float
    day_low: float
    last_price: float
    prev_close: float
    change: float
    pct_change: float
    volume: int
    traded_value: float
    year_high: float
    year_low: float
    free_float_mkt_cap: float
    pct_from_year_high: float
    pct_from_year_low: float
    pct_change_365d: float
    pct_change_30d: float
    # メタ（meta サブオブジェクト由来）
    company_name: str | None = None
    isin: str | None = None
```

---

## 8. 重要な発見事項

### re_total_inc vs re_tot_inc の問題

- `re_total_inc`: **INFY 実績では null**（設計書が誤って `total_income` にマップしていた）
- `re_tot_inc`: **INFY 実績では null**（フィールド名は似ているが別フィールド）
- 実際の総収益は `re_net_sale + re_oth_inc_new` で再計算する必要がある

設計書の `FINANCIAL_FIELD_MAP` に `"re_tot_inc": "total_income"` の記載があったが、
実際のレスポンスでは `re_total_inc`（underscore の位置が違う）も `re_tot_inc` も `null`。

**対応**: `parsers.py` の `parse_financial_results()` で以下のフォールバック処理を実装：

```python
total_income = (
    _parse_float(raw.get("re_total_inc"))
    or _parse_float(raw.get("re_tot_inc"))
    or (
        (_parse_float(raw.get("re_net_sale")) or 0)
        + (_parse_float(raw.get("re_oth_inc_new")) or 0)
    ) or None
)
```

### bankNonBnking フラグ

- `"N"`: 非金融企業（INFY等）→ 銀行専用フィールドは null
- `"B"`: 銀行・金融機関 → 銀行専用フィールドが有効
- `parsers.py` でこのフラグを確認して分岐処理が必要

### equity-stockIndices の data[0] vs data[1..]

- `data[0]`: インデックス自体のデータ（`priority=1`, `series` フィールドなし）
- `data[1..]`: 各構成銘柄（`priority=0`, `series="EQ"` あり）
- `series` フィールドの有無でインデックス行と銘柄行を判別可能

---

## 9. constants.py 実装確定版

```python
# 全63フィールドの FINANCIAL_FIELD_MAP（コアセット）
FINANCIAL_FIELD_MAP: Final[dict[str, str]] = {
    "re_from_dt": "period_from",
    "re_to_dt": "period_to",
    "re_create_dt": "created_date",
    "re_res_type": "result_type",
    "re_seq_num": "seq_num",
    "re_net_sale": "net_sales",
    "re_oth_inc_new": "other_income",
    "re_staff_cost": "staff_cost",
    "re_oth_exp": "other_expenditure",
    "re_rawmat_consump": "raw_material_consumption",
    "re_pur_trd_goods": "purchase_traded_goods",
    "re_inc_dre_sttr": "change_in_stock",
    "re_int_new": "interest_expense",
    "re_depr_und_exp": "depreciation",
    "re_oth_tot_exp": "total_other_expenditure",
    "re_pro_loss_bef_tax": "profit_before_tax",
    "re_curr_tax": "current_tax",
    "re_deff_tax": "deferred_tax",
    "re_tax": "tax",
    "re_net_profit": "net_profit",
    "re_con_pro_loss": "consolidated_profit_loss",
    "re_proloss_ord_act": "profit_loss_ordinary",
    "re_pro_los_frm_dis_opr": "profit_discontinued_ops",
    "re_prolos_dis_opr_aftr_tax": "profit_discontinued_after_tax",
    "re_tax_expens_of_dis_opr": "tax_discontinued_ops",
    "re_basic_eps_for_cont_dic_opr": "eps_basic",
    "re_dilut_eps_for_cont_dic_opr": "eps_diluted",
    "re_face_val": "face_value",
    "re_pdup": "paid_up_capital",
    "re_share_associate": "share_of_associates",
    "re_excepn_items_new": "exceptional_items",
    "re_desc_note_seg": "note_segment",
    "re_desc_note_fin": "note_financial",
    "re_notes_to_ac": "notes_to_accounts",
}

FINANCIAL_FIELD_MAP_BANK: Final[dict[str, str]] = {
    "re_int_earned": "interest_earned",
    "re_int_expd": "interest_expended",
    "re_int_dis_adv_bills": "interest_discounted_bills",
    "re_income_inv": "income_from_investments",
    "re_grs_npa": "gross_npa",
    "re_grs_npa_per": "gross_npa_percent",
    "re_bal_rbi_oth_bnk_funds": "balance_rbi_funds",
    "re_cap_ade_rat": "capital_adequacy_ratio",
    "re_cet_1_ret": "cet1_ratio",
    "re_debt_eqt_rat": "debt_equity_ratio",
    "re_tot_exp_exc_pro_cont": "total_exp_excl_provisions",
    "re_oth_pro_cont": "other_provisions",
}

QUOTE_PRICE_FIELD_MAP: Final[dict[str, str]] = {
    "lastPrice": "last_price",
    "change": "change",
    "pChange": "pct_change",
    "previousClose": "prev_close",
    "open": "open",
    "vwap": "vwap",
    "lowerCP": "lower_circuit",
    "upperCP": "upper_circuit",
    "basePrice": "base_price",
    "tickSize": "tick_size",
}

QUOTE_INDUSTRY_FIELD_MAP: Final[dict[str, str]] = {
    "macro": "macro_sector",
    "sector": "sector",
    "industry": "industry",
    "basicIndustry": "basic_industry",
}

INDEX_CONSTITUENT_FIELD_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "identifier": "identifier",
    "series": "series",
    "open": "open",
    "dayHigh": "day_high",
    "dayLow": "day_low",
    "lastPrice": "last_price",
    "previousClose": "prev_close",
    "change": "change",
    "pChange": "pct_change",
    "totalTradedVolume": "volume",
    "totalTradedValue": "traded_value",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "ffmc": "free_float_mkt_cap",
    "nearWKH": "pct_from_year_high",
    "nearWKL": "pct_from_year_low",
    "perChange365d": "pct_change_365d",
    "perChange30d": "pct_change_30d",
}

EVENT_CALENDAR_FIELD_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "company": "company_name",
    "purpose": "purpose",
    "bm_desc": "description",
    "date": "date",
}
```
