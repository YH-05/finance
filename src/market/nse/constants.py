"""Constants for NSE (National Stock Exchange of India) data retrieval module.

This module defines all constants used by the NSE data retrieval module,
including the API base URL, SSRF prevention whitelist, default HTTP headers,
User-Agent rotation list, polite delay settings, cookie refresh interval,
output directory path, and column name mapping from API response keys to
snake_case.

Constants are organised into the following categories:

1. API URLs (NSE website and API base endpoints)
2. Security (SSRF prevention via ALLOWED_HOSTS)
3. Bot-blocking countermeasures (User-Agent rotation, polite delays)
4. Session management (cookie refresh interval)
5. Default HTTP headers
6. Output settings (data directory)
7. Column name mapping (API keys to snake_case)

Notes
-----
All constants use ``typing.Final`` type annotations to prevent reassignment.
The ``__all__`` list exports all public constants for use by other modules.

NSE uses a cookie-based authentication mechanism. The session cookie is
obtained by visiting ``BASE_URL`` (the NSE home page) and then must be
included in all subsequent API requests. Cookies expire after approximately
``COOKIE_REFRESH_INTERVAL`` seconds.

See Also
--------
market.bse.constants : Similar constant pattern used by the BSE module.
"""

from typing import Final

# ---------------------------------------------------------------------------
# 1. API URL constants
# ---------------------------------------------------------------------------

BASE_URL: Final[str] = "https://www.nseindia.com"
"""Base URL for the NSE website.

NSE uses a cookie-based session: a GET request to this URL must be made
first to obtain session cookies before any API endpoint can be called.
"""

API_BASE_URL: Final[str] = "https://www.nseindia.com/api"
"""Base URL for NSE JSON API endpoints.

All API requests are constructed by appending endpoint paths
to this base URL (e.g., ``API_BASE_URL + "/equity-stockIndices?index=NIFTY 50"``).
"""

# ---------------------------------------------------------------------------
# 2. Security constants
# ---------------------------------------------------------------------------

ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({"www.nseindia.com"})
"""Whitelist of allowed hostnames for SSRF prevention (CWE-918).

Only requests to these hosts are permitted by the NSE session layer.
Requests to any other host will raise ``ValueError``.
"""

# ---------------------------------------------------------------------------
# 3. Bot-blocking countermeasure constants
# ---------------------------------------------------------------------------

DEFAULT_USER_AGENTS: Final[list[str]] = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
]
"""Default User-Agent strings for HTTP requests.

Contains 12 real browser User-Agent strings covering Chrome, Firefox,
Safari, and Edge on Windows, macOS, and Linux platforms.
Rotated randomly to avoid bot detection.
"""

DEFAULT_POLITE_DELAY: Final[float] = 0.5
"""Default polite delay between requests in seconds.

A minimum wait time between consecutive requests to avoid
overloading the NSE web server and triggering rate limiting.
NSE is more sensitive than BSE to rapid requests, so a longer delay is used.
"""

DEFAULT_DELAY_JITTER: Final[float] = 0.1
"""Random jitter added to the polite delay in seconds.

Adds randomness to request timing to appear more human-like.
The actual delay is ``DEFAULT_POLITE_DELAY + random(0, DEFAULT_DELAY_JITTER)``.
"""

DEFAULT_TIMEOUT: Final[float] = 30.0
"""Default HTTP request timeout in seconds.

Maximum time to wait for a response before raising a timeout error.
"""

# ---------------------------------------------------------------------------
# 4. Session management constants
# ---------------------------------------------------------------------------

COOKIE_REFRESH_INTERVAL: Final[float] = 300.0
"""Cookie refresh interval in seconds (5 minutes).

NSE session cookies expire after approximately 5 minutes of inactivity.
The session layer should re-initialise (re-visit ``BASE_URL``) when
the cookie age exceeds this interval to prevent ``NseCookieError``.
"""

# ---------------------------------------------------------------------------
# 5. Default HTTP headers
# ---------------------------------------------------------------------------

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "X-Requested-With": "XMLHttpRequest",
}
"""Default HTTP headers for NSE API requests.

Includes a static User-Agent for simple requests, Referer set to
the NSE website (required by NSE API), standard Accept headers, and
``X-Requested-With: XMLHttpRequest`` which NSE checks to distinguish
AJAX requests from direct browser navigation.
For session-based requests with User-Agent rotation, use
``DEFAULT_USER_AGENTS`` instead.
"""

# ---------------------------------------------------------------------------
# 6. Output settings
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_SUBDIR: Final[str] = "raw/nse"
"""Default subdirectory (relative to DATA_DIR) for output files.

Appended to the base data directory resolved by
``database.db.connection.get_data_dir()`` at runtime.

See Also
--------
database.db.connection.get_data_dir : Resolves the base data directory
    from the ``DATA_DIR`` environment variable.
"""

# ---------------------------------------------------------------------------
# 7. Column name mapping
# ---------------------------------------------------------------------------

EQUITY_QUOTE_COLUMN_NAME_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "companyName": "company_name",
    "series": "series",
    "lastPrice": "last_price",
    "change": "change",
    "pChange": "pct_change",
    "previousClose": "prev_close",
    "open": "open",
    "close": "close",
    "vwap": "vwap",
    "stockIndClosePrice": "stock_ind_close_price",
    "lowerCP": "lower_circuit_price",
    "upperCP": "upper_circuit_price",
    "priceBand": "price_band",
    "basePrice": "base_price",
    "intraDayHighLow": "intraday_high_low",
    "weekHighLow": "week_high_low",
    "quantity": "quantity",
    "totalTradedVolume": "total_traded_volume",
    "totalTradedValue": "total_traded_value",
    "lastUpdateTime": "last_update_time",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "activeSeries": "active_series",
    "deliveryToTradedQuantity": "delivery_to_traded_quantity",
    "deliverableVolumetoTotalTradedVolume": "deliverable_volume_to_total_traded_volume",
}
"""Mapping from NSE equity quote API response keys to snake_case column names.

The NSE equity quote API (``/api/quote-equity``) returns camelCase JSON keys.
This mapping normalises them to consistent snake_case for use in pandas DataFrames.
"""

INDEX_CONSTITUENTS_COLUMN_NAME_MAP: Final[dict[str, str]] = {
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
    "totalTradedVolume": "total_traded_volume",
    "totalTradedValue": "total_traded_value",
    "lastUpdateTime": "last_update_time",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "perChange365d": "pct_change_365d",
    "date365dAgo": "date_365d_ago",
    "chart365dPath": "chart_365d_path",
    "date30dAgo": "date_30d_ago",
    "perChange30d": "pct_change_30d",
    "chart30dPath": "chart_30d_path",
    "chartTodayPath": "chart_today_path",
}
"""Mapping from NSE index constituents API response keys to snake_case column names.

The NSE equity-stockIndices API returns camelCase JSON keys per constituent.
This mapping normalises them to consistent snake_case for use in pandas DataFrames.
"""

FINANCIAL_RESULT_COLUMN_NAME_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "fromDate": "from_date",
    "toDate": "to_date",
    "expenditure": "expenditure",
    "income": "income",
    "profitBeforeTax": "profit_before_tax",
    "profitAfterTax": "profit_after_tax",
    "revenueFromOperations": "revenue_from_operations",
    "netSales": "net_sales",
    "eps": "eps",
    "resultType": "result_type",
    "broadcastDate": "broadcast_date",
}
"""Mapping from NSE financial results API response keys to snake_case column names.

The NSE financial results API returns camelCase JSON keys.
This mapping normalises them to consistent snake_case for use in pandas DataFrames.
"""

# ---------------------------------------------------------------------------
# 8. FINANCIAL_FIELD_MAP (results-comparision API)
# ---------------------------------------------------------------------------

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
    "re_total_inc": "total_income",
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
"""Complete mapping from NSE results-comparision API ``re_*`` keys to snake_case.

Covers 34 core financial fields for non-banking companies.
Unit: thousands of Indian Rupees (net_sales, profits, costs).

Based on the 2026-04-02 API capture of ``/api/results-comparision?symbol=INFY``.

See Also
--------
FINANCIAL_FIELD_MAP_BANK : Additional fields for banking companies.
"""

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
"""Additional mapping for banking company financial fields (``bankNonBnking == "B"``).

Only applies when the results-comparision API returns ``bankNonBnking = "B"``.
These fields are ``null`` for non-banking companies.

See Also
--------
FINANCIAL_FIELD_MAP : Core fields applicable to all companies.
"""

EVENT_CALENDAR_FIELD_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "company": "company_name",
    "purpose": "purpose",
    "bm_desc": "description",
    "date": "date",
}
"""Mapping from NSE event-calendar API response keys to snake_case.

The NSE event-calendar API returns a flat JSON array where each item
uses these keys.

See Also
--------
market.nse.types.CorporateEvent : Typed dataclass for event-calendar entries.
"""

STOCK_LIST_COLUMN_MAP: Final[dict[str, str]] = {
    "SYMBOL": "symbol",
    "NAME OF COMPANY": "company_name",
    " NAME OF COMPANY": "company_name",
    "SERIES": "series",
    "DATE OF LISTING": "date_of_listing",
    "PAID UP VALUE": "paid_up_value",
    "MARKET LOT": "market_lot",
    "ISIN NUMBER": "isin",
    "FACE VALUE": "face_value",
}
"""Mapping from NSE EQUITY_L.csv column names to snake_case.

The NSE stock list CSV (``https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv``)
uses uppercase column names with spaces. Some column names include a leading space.
"""

PREOPEN_COLUMN_MAP: Final[dict[str, str]] = {
    "symbol": "symbol",
    "xDt": "ex_date",
    "caAct": "corporate_action",
    "iep": "iep",
    "chn": "change",
    "perChn": "pct_change",
    "pCls": "prev_close",
    "trdQnty": "traded_quantity",
    "iVal": "traded_value",
    "sumVal": "sum_value",
    "sumQnty": "sum_quantity",
    "finQnty": "final_quantity",
    "sbrdQnty": "subscribed_quantity",
}
"""Mapping from NSE market-data-pre-open API keys to snake_case.

Used by ``parse_preopen_data()`` to normalise pre-open market data.
"""

ALL_INDICES_COLUMN_MAP: Final[dict[str, str]] = {
    "indexSymbol": "index_symbol",
    "current": "current",
    "variation": "variation",
    "percentChange": "pct_change",
    "open": "open",
    "high": "high",
    "low": "low",
    "previousClose": "prev_close",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "perChange30d": "pct_change_30d",
    "perChange365d": "pct_change_365d",
    "indicativeClose": "indicative_close",
    "key": "key",
    "index": "index",
}
"""Mapping from NSE allIndices API response keys to snake_case.

Used by ``parse_all_indices()`` to normalise all-indices market data.
"""

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "ALLOWED_HOSTS",
    "ALL_INDICES_COLUMN_MAP",
    "API_BASE_URL",
    "BASE_URL",
    "COOKIE_REFRESH_INTERVAL",
    "DEFAULT_DELAY_JITTER",
    "DEFAULT_HEADERS",
    "DEFAULT_OUTPUT_SUBDIR",
    "DEFAULT_POLITE_DELAY",
    "DEFAULT_TIMEOUT",
    "DEFAULT_USER_AGENTS",
    "EQUITY_QUOTE_COLUMN_NAME_MAP",
    "EVENT_CALENDAR_FIELD_MAP",
    "FINANCIAL_FIELD_MAP",
    "FINANCIAL_FIELD_MAP_BANK",
    "FINANCIAL_RESULT_COLUMN_NAME_MAP",
    "INDEX_CONSTITUENTS_COLUMN_NAME_MAP",
    "PREOPEN_COLUMN_MAP",
    "STOCK_LIST_COLUMN_MAP",
]
