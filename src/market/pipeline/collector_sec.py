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
from pathlib import Path
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
    Temporarily prepends the edgartools site-packages parent directory to
    ``sys.path`` during the import so that ``edgar.config``, ``edgar.core``,
    and other edgartools submodules resolve to site-packages rather than the
    project's ``src/edgar`` package.

    Problem background: ``src/edgar/config.py`` (project) and
    ``site-packages/edgar/config.py`` (edgartools) share the same dotted
    module name.  In CI the project's ``src/`` is on ``sys.path`` and
    ``edgar.config`` resolves to the project file, which lacks ``SEC_BASE_URL``
    and other edgartools constants.

    Solution: Put the site-packages directory that contains edgartools at the
    front of ``sys.path`` before calling ``exec_module``.  After the load
    completes, ``sys.modules`` caches all submodules from the correct source,
    and ``sys.path`` is restored to its original order.
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

    # Identify the site-packages directory that contains edgartools.
    # spec.origin is ".../site-packages/edgar/__init__.py"
    # → parent dir is ".../site-packages/edgar"
    # → grandparent is ".../site-packages"  ← this goes to front of sys.path
    edgar_site_pkg_dir = str(Path(spec.origin).parent.parent)

    # AIDEV-NOTE: Temporarily prepend the correct site-packages directory so
    # that all ``edgar.*`` absolute imports inside edgartools resolve to
    # site-packages rather than the project's ``src/edgar``.  After the load,
    # ``sys.path`` is restored and ``sys.modules`` caches keep the right versions.
    original_sys_path = sys.path[:]
    # Remove any existing edgar-related path entries that conflict, then
    # prepend the correct site-packages path.
    try:
        if edgar_site_pkg_dir not in sys.path:
            sys.path.insert(0, edgar_site_pkg_dir)
        else:
            # Move it to the front so it takes priority
            sys.path.remove(edgar_site_pkg_dir)
            sys.path.insert(0, edgar_site_pkg_dir)

        mod = importlib.util.module_from_spec(spec)
        # Register in sys.modules BEFORE exec_module so that submodule
        # imports inside edgar.__init__ (e.g. ``edgar._filings``) can find
        # their parent package correctly.
        sys.modules["edgar"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

    finally:
        sys.path[:] = original_sys_path

    company_cls = getattr(mod, "Company", None)
    if company_cls is None:
        msg = "edgartools module does not export 'Company' class"
        raise CollectorError(msg)

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
        logger.debug(
            "SecEdgarCollector initialized",
            storage_type=type(self._storage).__name__,
        )

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

        For each filing type in ``filing_types``, fetches filings from
        edgartools ``Company.get_filings(form=filing_type)``, extracts
        financials via ``.obj().financials.to_dataframe()``, applies
        ``dimension==False & abstract==False`` filtering, supplements
        missing ``standard_concept`` via ``CF_LABEL_FALLBACK``, maps to
        ``FinancialStatementRecord``, and upserts via storage.

        Applies ``time.sleep(0.1)`` between filing fetches to respect the
        SEC 10 req/sec rate limit.

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

        Examples
        --------
        >>> collector = SecEdgarCollector(storage=mock_storage)
        >>> result = collector.collect_symbol("AAPL")
        >>> result["symbol"]
        'AAPL'
        """
        if filing_types is None:
            filing_types = _DEFAULT_FILING_TYPES

        records_upserted = 0
        errors: list[str] = []

        Company = self._import_company()

        for form_type in filing_types:
            report_type = _FORM_TO_REPORT_TYPE.get(form_type, "other")

            try:
                company = Company(symbol)
                filings = company.get_filings(form=form_type)
            except Exception as exc:
                msg = f"Failed to get {form_type} filings for {symbol}: {exc}"
                logger.warning(msg, symbol=symbol, form=form_type, error=str(exc))
                errors.append(msg)
                continue

            for filing in filings:
                try:
                    obj = filing.obj()
                    financials = obj.financials
                    df: pd.DataFrame = financials.to_dataframe()

                    if df.empty:
                        continue

                    # Apply dimension==False & abstract==False filter
                    working: pd.DataFrame = df.copy()
                    if "dimension" in working.columns:
                        keep = working["dimension"].eq(False)
                        working = working.loc[keep].reset_index(drop=True)
                    if "abstract" in working.columns:
                        keep2 = working["abstract"].eq(False)
                        working = working.loc[keep2].reset_index(drop=True)
                    df = working

                    converted = self._df_to_records(df, symbol, form_type, report_type)
                    if converted:
                        upserted = self._storage.upsert(converted)
                        records_upserted += upserted

                    # Respect SEC 10 req/sec rate limit
                    time.sleep(_SEC_RATE_LIMIT_SLEEP)

                except Exception as exc:
                    msg = f"Failed to process {form_type} filing for {symbol}: {exc}"
                    logger.warning(msg, symbol=symbol, form=form_type, error=str(exc))
                    errors.append(msg)
                    continue

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
]
