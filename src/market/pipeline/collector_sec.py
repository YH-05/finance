"""SEC EDGAR financial statement data collector.

This module provides the ``SecEdgarCollector`` class that uses the edgartools
library to fetch IS/BS/CF financial data from SEC EDGAR filings, and persists
results via ``SecEdgarStorage``.

Key components
--------------
- ``CF_LABEL_FALLBACK`` -- Dict mapping common cash flow label strings to
  ``standard_concept`` values when edgartools ``standard_concept`` is absent.
- ``SecEdgarCollector._import_company()`` -- Uses ``importlib.machinery.PathFinder``
  to load the edgartools ``Company`` class from site-packages, avoiding the
  name collision with ``src/edgar``.

Notes
-----
edgartools installs as ``edgar`` in site-packages, which conflicts with the
project's ``src/edgar`` package.  ``_import_company()`` resolves this using
``importlib.machinery.PathFinder`` — the same technique as
``src/edgar/fetcher.py::_import_edgartools_company()``.

SEC rate limiting
-----------------
The SEC limits EDGAR access to 10 requests per second. A ``time.sleep(0.1)``
delay is applied between filing fetches to stay within this budget.

Examples
--------
>>> collector = SecEdgarCollector()
>>> result = collector.collect_symbol("AAPL")
>>> result["records_upserted"]
6

See Also
--------
src/edgar/fetcher.py : Reference importlib pattern for edgartools Company.
market.pipeline.storage_sec : Storage layer for financial statement records.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import time
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from market.pipeline.errors import CollectorError
from market.pipeline.models import FinancialStatementRecord
from market.pipeline.storage_sec import SecEdgarStorage
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# CF label fallback dictionary
# ---------------------------------------------------------------------------

# AIDEV-NOTE: Populated based on real SEC EDGAR XBRL data smoke tests.
# Keys are raw concept labels from edgartools; values are normalized
# standard_concept names used in FinancialStatementRecord.
CF_LABEL_FALLBACK: dict[str, str] = {
    # Operating activities
    "NetCashProvidedByUsedInOperatingActivities": "operating_cashflow",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": "operating_cashflow",
    "CashGeneratedFromOperations": "operating_cashflow",
    # Investing activities
    "NetCashProvidedByUsedInInvestingActivities": "investing_cashflow",
    "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations": "investing_cashflow",
    # Financing activities
    "NetCashProvidedByUsedInFinancingActivities": "financing_cashflow",
    "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations": "financing_cashflow",
    # Capital expenditures
    "PaymentsToAcquirePropertyPlantAndEquipment": "capex",
    "CapitalExpendituresIncurredButNotYetPaid": "capex",
    # Free cash flow proxies (not standard, but sometimes needed)
    "FreeCashFlow": "free_cashflow",
    # Depreciation
    "DepreciationDepletionAndAmortization": "depreciation_amortization",
    "DepreciationAndAmortization": "depreciation_amortization",
}

# Mapping from edgartools filing form type to report_type string.
_FORM_TO_REPORT_TYPE: dict[str, str] = {
    "10-K": "annual",
    "10-Q": "quarterly",
}

# Mapping from standard_concept values to FinancialStatementRecord field names.
_CONCEPT_TO_FIELD: dict[str, str] = {
    # Income statement
    "revenue": "revenue",
    "revenues": "revenue",
    "net_sales": "revenue",
    "total_revenue": "revenue",
    "net_income": "net_income",
    "net_income_loss": "net_income",
    # Balance sheet
    "total_assets": "total_assets",
    "assets": "total_assets",
    "total_liabilities": "total_liabilities",
    "liabilities": "total_liabilities",
    # Cash flow
    "operating_cashflow": "operating_cashflow",
    "operating_cash_flow": "operating_cashflow",
}

# SEC rate limit: 10 requests/sec → 0.1s between requests.
_SEC_RATE_LIMIT_SLEEP = 0.1

# Default filing types to collect per symbol.
_DEFAULT_FILING_TYPES: list[str] = ["10-K", "10-Q"]


# ---------------------------------------------------------------------------
# Statement type detection helpers
# ---------------------------------------------------------------------------


def _detect_statement_type(form_type: str, concept: str, label: str) -> str:
    """Heuristically determine statement type from concept/label strings."""
    concept_lower = concept.lower()
    _ = label.lower()  # label kept for potential future use

    # Cash flow
    if any(
        kw in concept_lower
        for kw in ["cashflow", "cash_flow", "operatingactivities", "operatingcash"]
    ):
        return "cash_flow"
    if "cash" in concept_lower and "operat" in concept_lower:
        return "cash_flow"

    # Balance sheet
    if any(
        kw in concept_lower
        for kw in ["assets", "liabilities", "equity", "balancesheet"]
    ):
        return "balance_sheet"

    # Income statement (fallback)
    return "income"


def _safe_float(value: Any) -> float | None:
    """Convert a value to float, returning None on failure."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _extract_operating_cashflow_fallback(financials: Any) -> float | None:
    """Extract operating cash flow from XBRL raw data using CF_LABEL_FALLBACK.

    Called when ``financials.get_operating_cash_flow()`` returns ``None``.
    Iterates through the ``cashflow_statement`` DataFrame and matches concept
    names against the keys of ``CF_LABEL_FALLBACK`` that map to
    ``"operating_cashflow"``.

    Parameters
    ----------
    financials : Any
        The edgartools ``Financials`` object with a ``cashflow_statement()``
        method.

    Returns
    -------
    float | None
        The first non-None operating cash flow value found via XBRL concept
        matching, or ``None`` if no match is found.

    Notes
    -----
    The function uses the ``concept`` column of the cash flow statement
    DataFrame.  edgartools populates this column with raw XBRL concept names
    (e.g. ``"NetCashProvidedByUsedInOperatingActivities"``), which are the
    keys of ``CF_LABEL_FALLBACK``.  This approach bypasses the label-pattern
    matching in ``Financials.get_operating_cash_flow()`` and works directly
    with XBRL taxonomy names.
    """
    # AIDEV-NOTE: CF_LABEL_FALLBACK maps XBRL concept names → standard_concept.
    # Here we only care about keys that map to "operating_cashflow".
    operating_cf_concepts: frozenset[str] = frozenset(
        k for k, v in CF_LABEL_FALLBACK.items() if v == "operating_cashflow"
    )

    try:
        cf_stmt = financials.cashflow_statement()
        if cf_stmt is None:
            logger.debug("cashflow_statement() returned None; fallback unavailable")
            return None

        df = cf_stmt.to_dataframe()
        if df is None or not hasattr(df, "empty") or df.empty:
            logger.debug("cashflow_statement DataFrame is empty; fallback unavailable")
            return None

        if "concept" not in df.columns:
            logger.debug(
                "cashflow_statement DataFrame has no 'concept' column",
                columns=list(df.columns),
            )
            return None

        # Period columns are those that are not metadata columns
        meta_cols = {
            "concept",
            "label",
            "level",
            "abstract",
            "dimension",
            "is_breakdown",
        }
        period_cols = [c for c in df.columns if c not in meta_cols]
        if not period_cols:
            logger.debug("No period columns found in cashflow_statement DataFrame")
            return None

        # Use the most-recent period (first period column)
        recent_col = period_cols[0]

        for concept in operating_cf_concepts:
            matches = df[df["concept"] == concept]
            if matches.empty:
                continue

            value = _safe_float(matches.iloc[0][recent_col])
            if value is not None:
                logger.info(
                    "operating_cashflow extracted via CF_LABEL_FALLBACK",
                    concept=concept,
                    value=value,
                )
                return value

    except Exception as exc:
        logger.debug(
            "CF_LABEL_FALLBACK extraction failed",
            error=str(exc),
        )

    return None


# ---------------------------------------------------------------------------
# Module-level cached import for edgartools Company
# ---------------------------------------------------------------------------

# Cache for the edgartools Company class (avoids repeated importlib calls).
_EDGARTOOLS_COMPANY_CACHE: Any = None


def _import_edgartools_company() -> Any:
    """Import the ``Company`` class from the edgartools site-packages.

    Uses ``importlib.machinery.PathFinder`` to locate the edgartools
    package in site-packages, bypassing the project's ``src/edgar``
    namespace that shadows the library.

    Returns
    -------
    type
        The edgartools ``Company`` class.

    Raises
    ------
    CollectorError
        If edgartools is not installed or ``Company`` class is not found.

    Notes
    -----
    The project has ``src/edgar`` on ``PYTHONPATH``, which collides with
    the edgartools library that also installs as ``edgar`` in site-packages.
    In CI, other tests may already have loaded ``edgar.config`` from
    ``src/edgar/config.py`` into ``sys.modules``.  When edgartools'
    ``edgar.attachments`` then does ``from edgar.config import SEC_BASE_URL``,
    Python finds the cached ``src/edgar/config.py`` (which lacks that symbol)
    and raises ``ImportError``.

    Solution: Temporarily stash all existing ``edgar.*`` entries from
    ``sys.modules``, register the site-packages ``edgar`` module, execute
    it (so all sub-imports fill ``sys.modules`` with site-packages versions),
    extract the Company class, then restore the original ``sys.modules``
    state.  The Company class object itself is valid after restore.
    """
    global _EDGARTOOLS_COMPANY_CACHE

    if _EDGARTOOLS_COMPANY_CACHE is not None:
        return _EDGARTOOLS_COMPANY_CACHE

    site_packages_paths = [p for p in sys.path if "site-packages" in p]
    spec = importlib.machinery.PathFinder.find_spec("edgar", site_packages_paths)

    if spec is None or spec.origin is None:
        msg = "edgartools is not installed. Install it with: uv add edgartools"
        raise CollectorError(msg)

    if spec.loader is None:
        msg = "Failed to load edgartools module: loader is None"
        raise CollectorError(msg)

    # AIDEV-NOTE: Two-phase sys.modules swap to prevent namespace collision.
    #
    # Step 1: Stash all existing ``edgar.*`` entries (project's src/edgar)
    # so that edgartools sub-imports don't accidentally find the wrong module.
    stashed: dict[str, Any] = {
        k: v for k, v in sys.modules.items() if k == "edgar" or k.startswith("edgar.")
    }
    # Remove the stashed entries from sys.modules temporarily.
    for key in stashed:
        del sys.modules[key]

    try:
        # Step 2: Register the site-packages edgar module and execute it.
        # Sub-imports (edgar.config, edgar._filings, etc.) will now be loaded
        # from site-packages because sys.modules["edgar"] points there.
        mod = importlib.util.module_from_spec(spec)
        sys.modules["edgar"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

        company_cls = getattr(mod, "Company", None)
        if company_cls is None:
            msg = "edgartools module does not export 'Company' class"
            raise CollectorError(msg)

    finally:
        # Step 3: Restore the original edgar.* entries so that the rest of
        # the codebase (src/edgar) continues to work normally.
        # Remove all edgar.* entries that were just created by exec_module.
        new_edgar_keys = [
            k for k in sys.modules if k == "edgar" or k.startswith("edgar.")
        ]
        for key in new_edgar_keys:
            del sys.modules[key]
        # Restore the original project edgar.* entries.
        sys.modules.update(stashed)

    _EDGARTOOLS_COMPANY_CACHE = company_cls
    logger.debug("edgartools Company class loaded from site-packages")
    return company_cls


# ---------------------------------------------------------------------------
# SecEdgarCollector
# ---------------------------------------------------------------------------


class SecEdgarCollector:
    """Orchestrator for SEC EDGAR financial statement data collection.

    Uses the edgartools ``Company`` class (loaded via ``importlib.machinery.PathFinder``
    to avoid name collision with ``src/edgar``) to fetch 10-K and 10-Q filings.

    For each filing, extracts IS/BS/CF data from ``filing.obj().financials``,
    applies ``dimension==False & abstract==False`` filtering, maps rows to
    ``FinancialStatementRecord``, and upserts via ``SecEdgarStorage``.

    Parameters
    ----------
    storage : SecEdgarStorage | None
        Storage layer for financial statement records. When ``None``, a default
        ``SecEdgarStorage()`` is created.

    Examples
    --------
    >>> collector = SecEdgarCollector()
    >>> result = collector.collect_symbol("AAPL", filing_types=["10-K"])
    >>> result["records_upserted"] >= 0
    True
    """

    def __init__(self, storage: SecEdgarStorage | None = None) -> None:
        """Initialize collector with optional DI parameters."""
        self._storage = storage or SecEdgarStorage()
        self._configure_identity()
        logger.debug(
            "SecEdgarCollector initialized",
            storage_type=type(self._storage).__name__,
        )

    @staticmethod
    def _configure_identity() -> None:
        """Configure edgartools identity from ``SEC_EDGAR_IDENTITY`` env var.

        edgartools requires ``set_identity("Name email")`` before making
        SEC EDGAR API requests. This reads the identity from the environment
        and applies it via the project's ``edgar.config.set_identity()``.
        """
        import os

        identity = os.environ.get("SEC_EDGAR_IDENTITY", "").strip()
        if not identity:
            logger.warning("SEC_EDGAR_IDENTITY not set; SEC EDGAR requests will fail")
            return

        # Use the same PathFinder technique as _import_edgartools_company()
        # to reach edgartools' set_identity (avoids src/edgar collision).
        site_packages_paths = [p for p in sys.path if "site-packages" in p]
        spec = importlib.machinery.PathFinder.find_spec("edgar", site_packages_paths)
        if spec is None or spec.loader is None:
            logger.warning("edgartools not found in site-packages")
            return

        stashed = {
            k: v
            for k, v in sys.modules.items()
            if k == "edgar" or k.startswith("edgar.")
        }
        for key in stashed:
            del sys.modules[key]
        try:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["edgar"] = mod
            spec.loader.exec_module(mod)
            if hasattr(mod, "set_identity"):
                mod.set_identity(identity)
                logger.debug("SEC EDGAR identity configured via edgartools")
        finally:
            new_keys = [
                k for k in sys.modules if k == "edgar" or k.startswith("edgar.")
            ]
            for key in new_keys:
                del sys.modules[key]
            sys.modules.update(stashed)

    # ------------------------------------------------------------------
    # importlib helper
    # ------------------------------------------------------------------

    def _import_company(self) -> Any:
        """Return the edgartools ``Company`` class.

        Delegates to the module-level ``_import_edgartools_company()`` function,
        which caches the result via ``sys.modules``.

        Returns
        -------
        type
            The edgartools ``Company`` class.

        Raises
        ------
        CollectorError
            If edgartools is not installed or ``Company`` class is not found.
        """
        return _import_edgartools_company()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_symbol(
        self,
        symbol: str,
        filing_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Collect financial statement data for a single ticker symbol.

        For each filing type in ``filing_types``, fetches the most recent
        filing from edgartools, extracts key financial metrics via the
        ``Financials.get_*()`` helper methods, maps to a single
        ``FinancialStatementRecord``, and upserts via storage.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. ``"AAPL"``).
        filing_types : list[str] | None
            Filing form types to process. Defaults to ``["10-K", "10-Q"]``.

        Returns
        -------
        dict[str, Any]
            Summary dict with keys:
            - ``"symbol"``: the ticker symbol
            - ``"records_upserted"``: total records persisted
            - ``"errors"``: list of error strings
        """
        if filing_types is None:
            filing_types = _DEFAULT_FILING_TYPES

        records_upserted = 0
        errors: list[str] = []
        fetched_at = datetime.now(UTC).isoformat()

        company_cls = self._import_company()

        for form_type in filing_types:
            report_type = _FORM_TO_REPORT_TYPE.get(form_type, "other")

            try:
                company = company_cls(symbol)
                filings = company.get_filings(form=form_type)
            except Exception as exc:
                msg = f"Failed to get {form_type} filings for {symbol}: {exc}"
                logger.warning(msg, symbol=symbol, form=form_type, error=str(exc))
                errors.append(msg)
                continue

            if not filings:
                continue

            # Process the most recent filing only
            filing = filings[0]
            try:
                obj = filing.obj()
                financials = obj.financials

                # Extract fiscal date from the filing
                fiscal_date = str(
                    getattr(filing, "period_of_report", "")
                    or getattr(filing, "filing_date", "")
                )

                # Use get_* helpers for robust extraction
                _primary_ocf = _safe_float(financials.get_operating_cash_flow())
                _ocf = (
                    _primary_ocf
                    if _primary_ocf is not None
                    else _extract_operating_cashflow_fallback(financials)
                )
                record = FinancialStatementRecord(
                    symbol=symbol,
                    fiscal_date_ending=fiscal_date,
                    statement_type="consolidated",
                    report_type=report_type,
                    revenue=_safe_float(financials.get_revenue()),
                    net_income=_safe_float(financials.get_net_income()),
                    total_assets=_safe_float(financials.get_total_assets()),
                    total_liabilities=_safe_float(financials.get_total_liabilities()),
                    operating_cashflow=_ocf,
                    fetched_at=fetched_at,
                )

                # Only upsert if at least one metric was extracted
                has_data = any(
                    v is not None
                    for v in [
                        record.revenue,
                        record.net_income,
                        record.total_assets,
                        record.total_liabilities,
                        record.operating_cashflow,
                    ]
                )
                if has_data:
                    upserted = self._storage.upsert([record])
                    records_upserted += upserted

                # Respect SEC 10 req/sec rate limit
                time.sleep(_SEC_RATE_LIMIT_SLEEP)

            except Exception as exc:
                msg = f"Failed to process {form_type} filing for {symbol}: {exc}"
                logger.warning(msg, symbol=symbol, form=form_type, error=str(exc))
                errors.append(msg)

        logger.info(
            "SEC EDGAR collection completed",
            symbol=symbol,
            filing_types=filing_types,
            records_upserted=records_upserted,
            error_count=len(errors),
        )

        return {
            "symbol": symbol,
            "records_upserted": records_upserted,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _df_to_records(
        self,
        df: pd.DataFrame,
        symbol: str,
        form_type: str,
        report_type: str,
    ) -> list[FinancialStatementRecord]:
        """Convert a financials DataFrame to a list of FinancialStatementRecord.

        Groups rows by fiscal_date_ending (period), aggregates key financial
        metrics into one record per period.
        """
        fetched_at = datetime.now(UTC).isoformat()
        records: list[FinancialStatementRecord] = []

        # Determine period column (edgartools uses "period" or "end_date")
        period_col = next(
            (
                c
                for c in ("period", "end_date", "fiscal_date_ending")
                if c in df.columns
            ),
            None,
        )

        # Group by period if available, else treat entire df as one period
        if period_col:
            periods = df[period_col].dropna().unique()
        else:
            periods = ["unknown"]

        for period in periods:
            if period_col:
                period_df = df[df[period_col] == period]
            else:
                period_df = df

            fiscal_date = str(period) if period != "unknown" else ""

            # Accumulate field values for this period
            field_values: dict[str, float | None] = {
                "revenue": None,
                "net_income": None,
                "total_assets": None,
                "total_liabilities": None,
                "operating_cashflow": None,
            }

            # Determine statement type for the whole record (majority vote)
            stmt_type = "income"

            for _, row in period_df.iterrows():
                concept = str(row.get("concept", ""))
                label = str(row.get("label", ""))
                value = _safe_float(row.get("value"))
                raw_std = row.get("standard_concept")

                # Use standard_concept if present, else fall back to CF_LABEL_FALLBACK
                std_concept: str | None
                if raw_std and not pd.isna(raw_std) and str(raw_std).strip():
                    std_concept = str(raw_std).strip().lower().replace(" ", "_")
                else:
                    # Try CF_LABEL_FALLBACK using concept name (strip namespace)
                    bare_concept = concept.split("/")[-1] if "/" in concept else concept
                    fallback = CF_LABEL_FALLBACK.get(bare_concept)
                    std_concept = fallback

                if std_concept is None:
                    continue

                target_field = _CONCEPT_TO_FIELD.get(std_concept)
                if (
                    target_field
                    and value is not None
                    and field_values.get(target_field) is None
                ):
                    field_values[target_field] = value

                # Detect statement type from concept
                detected = _detect_statement_type(form_type, concept, label)
                if detected == "cash_flow":
                    stmt_type = "cash_flow"
                elif detected == "balance_sheet" and stmt_type == "income":
                    stmt_type = "balance_sheet"

            if not fiscal_date:
                continue

            record = FinancialStatementRecord(
                symbol=symbol,
                fiscal_date_ending=fiscal_date,
                statement_type=stmt_type,
                report_type=report_type,
                revenue=field_values["revenue"],
                net_income=field_values["net_income"],
                total_assets=field_values["total_assets"],
                total_liabilities=field_values["total_liabilities"],
                operating_cashflow=field_values["operating_cashflow"],
                fetched_at=fetched_at,
            )
            records.append(record)

        return records


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "CF_LABEL_FALLBACK",
    "SecEdgarCollector",
    "_extract_operating_cashflow_fallback",
]
