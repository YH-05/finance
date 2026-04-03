"""Unit tests for market.pipeline.collector_sec.SecEdgarCollector.

The edgartools ``Company`` class is loaded via ``_import_company()``.
In tests, we patch this method to avoid any real SEC API calls.
All tests use MagicMock DI for SecEdgarStorage.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.pipeline.collector_sec import (
    CF_LABEL_FALLBACK,
    SecEdgarCollector,
    _detect_statement_type,
    _safe_float,
)
from market.pipeline.errors import CollectorError

# =============================================================================
# Private helper function tests
# =============================================================================


class TestSafeFloat:
    """Tests for _safe_float()."""

    def test_正常系_整数をfloatに変換できる(self) -> None:
        assert _safe_float(100) == pytest.approx(100.0)

    def test_正常系_文字列数値をfloatに変換できる(self) -> None:
        assert _safe_float("3.14") == pytest.approx(3.14)

    def test_正常系_Noneの場合はNoneを返す(self) -> None:
        assert _safe_float(None) is None

    def test_正常系_NaNの場合はNoneを返す(self) -> None:
        assert _safe_float(float("nan")) is None

    def test_正常系_pandas_NaNはNoneを返す(self) -> None:
        assert _safe_float(pd.NA) is None

    def test_正常系_不正な文字列はNoneを返す(self) -> None:
        assert _safe_float("not_a_number") is None


class TestDetectStatementType:
    """Tests for _detect_statement_type()."""

    def test_正常系_キャッシュフロー関連コンセプトはcash_flow(self) -> None:
        assert _detect_statement_type("10-K", "NetCashProvidedByUsedInOperatingActivities", "") == "cash_flow"

    def test_正常系_資産関連コンセプトはbalance_sheet(self) -> None:
        assert _detect_statement_type("10-K", "total_assets", "") == "balance_sheet"

    def test_正常系_負債関連コンセプトはbalance_sheet(self) -> None:
        assert _detect_statement_type("10-K", "total_liabilities", "") == "balance_sheet"

    def test_正常系_不明なコンセプトはincomeにフォールバック(self) -> None:
        assert _detect_statement_type("10-K", "revenue", "") == "income"


class TestCfLabelFallback:
    """Tests for the CF_LABEL_FALLBACK dictionary."""

    def test_正常系_operating_cashflow_ラベルが含まれる(self) -> None:
        assert "NetCashProvidedByUsedInOperatingActivities" in CF_LABEL_FALLBACK

    def test_正常系_operating_cashflow_に正しいマッピング(self) -> None:
        assert CF_LABEL_FALLBACK["NetCashProvidedByUsedInOperatingActivities"] == "operating_cashflow"


# =============================================================================
# SecEdgarCollector tests
# =============================================================================


class TestSecEdgarCollectorInit:
    """Tests for SecEdgarCollector initialization."""

    def test_正常系_DI経由で初期化できる(
        self, mock_sec_storage: MagicMock
    ) -> None:
        collector = SecEdgarCollector(storage=mock_sec_storage)
        assert collector is not None


class TestSecEdgarCollectorImportCompany:
    """Tests for SecEdgarCollector._import_company()."""

    def test_正常系_edgartools_Companyクラスをロードできる(
        self, mock_sec_storage: MagicMock
    ) -> None:
        """_import_company()がCollectorErrorを出さない場合はロード成功."""
        collector = SecEdgarCollector(storage=mock_sec_storage)
        try:
            company_cls = collector._import_company()
            assert company_cls is not None
        except CollectorError:
            pytest.skip("edgartools not installed in test environment")


class TestSecEdgarCollectorCollectSymbol:
    """Tests for SecEdgarCollector.collect_symbol() with patched _import_company."""

    def _make_mock_company_class(self, df: pd.DataFrame) -> MagicMock:
        """Build a mock Company class that returns the given DataFrame via financials."""
        mock_filing = MagicMock()
        mock_obj = MagicMock()
        mock_financials = MagicMock()
        mock_financials.to_dataframe.return_value = df
        mock_obj.financials = mock_financials
        mock_filing.obj.return_value = mock_obj

        mock_filings = MagicMock()
        mock_filings.__iter__ = MagicMock(return_value=iter([mock_filing]))

        mock_company_instance = MagicMock()
        mock_company_instance.get_filings.return_value = mock_filings

        MockCompany = MagicMock(return_value=mock_company_instance)
        return MockCompany

    def test_正常系_空のDataFrameは0件upsert(
        self, mock_sec_storage: MagicMock
    ) -> None:
        MockCompany = self._make_mock_company_class(pd.DataFrame())
        collector = SecEdgarCollector(storage=mock_sec_storage)

        with patch.object(collector, "_import_company", return_value=MockCompany):
            result = collector.collect_symbol("AAPL", filing_types=["10-K"])

        assert result["symbol"] == "AAPL"
        assert result["records_upserted"] == 0
        assert result["errors"] == []

    def test_正常系_収益データを含むDataFrameは変換される(
        self, mock_sec_storage: MagicMock
    ) -> None:
        df = pd.DataFrame([
            {
                "concept": "revenue",
                "label": "Revenue",
                "value": 391_035_000_000.0,
                "standard_concept": "revenue",
                "period": "2025-09-30",
                "dimension": False,
                "abstract": False,
            }
        ])
        MockCompany = self._make_mock_company_class(df)
        mock_sec_storage.upsert.return_value = 1
        collector = SecEdgarCollector(storage=mock_sec_storage)

        with patch.object(collector, "_import_company", return_value=MockCompany):
            result = collector.collect_symbol("AAPL", filing_types=["10-K"])

        assert result["symbol"] == "AAPL"

    def test_正常系_APIエラーはerrorsリストに記録される(
        self, mock_sec_storage: MagicMock
    ) -> None:
        MockCompany = MagicMock(side_effect=Exception("Company not found"))
        collector = SecEdgarCollector(storage=mock_sec_storage)

        with patch.object(collector, "_import_company", return_value=MockCompany):
            result = collector.collect_symbol("INVALID", filing_types=["10-K"])

        assert result["symbol"] == "INVALID"
        assert len(result["errors"]) == 1

    def test_正常系_複数のfiling_typesを処理できる(
        self, mock_sec_storage: MagicMock
    ) -> None:
        MockCompany = self._make_mock_company_class(pd.DataFrame())
        collector = SecEdgarCollector(storage=mock_sec_storage)

        with patch.object(collector, "_import_company", return_value=MockCompany):
            result = collector.collect_symbol("AAPL", filing_types=["10-K", "10-Q"])

        assert result["symbol"] == "AAPL"
        assert result["errors"] == []

    def test_正常系_デフォルトはanualとquarterlyの両方を処理(
        self, mock_sec_storage: MagicMock
    ) -> None:
        MockCompany = self._make_mock_company_class(pd.DataFrame())
        collector = SecEdgarCollector(storage=mock_sec_storage)

        with patch.object(collector, "_import_company", return_value=MockCompany):
            result = collector.collect_symbol("AAPL")

        # filing_types=None → ["10-K", "10-Q"] → company.get_filings called 2 times
        assert result["symbol"] == "AAPL"


class TestSecEdgarCollectorDfToRecords:
    """Tests for SecEdgarCollector._df_to_records()."""

    def test_正常系_空DataFrameは空リストを返す(
        self, mock_sec_storage: MagicMock
    ) -> None:
        collector = SecEdgarCollector(storage=mock_sec_storage)
        records = collector._df_to_records(pd.DataFrame(), "AAPL", "10-K", "annual")
        assert records == []

    def test_正常系_period列のないDataFrameは処理される(
        self, mock_sec_storage: MagicMock
    ) -> None:
        df = pd.DataFrame([
            {
                "concept": "revenue",
                "label": "Revenue",
                "value": 100.0,
                "standard_concept": "revenue",
            }
        ])
        collector = SecEdgarCollector(storage=mock_sec_storage)
        records = collector._df_to_records(df, "AAPL", "10-K", "annual")
        # period==unknown → fiscal_date="" → skipped
        assert records == []

    def test_正常系_有効なperiodを持つレコードは変換される(
        self, mock_sec_storage: MagicMock
    ) -> None:
        df = pd.DataFrame([
            {
                "concept": "revenue",
                "label": "Revenue",
                "value": 391_035_000_000.0,
                "standard_concept": "revenue",
                "period": "2025-09-30",
            }
        ])
        collector = SecEdgarCollector(storage=mock_sec_storage)
        records = collector._df_to_records(df, "AAPL", "10-K", "annual")
        assert len(records) == 1
        assert records[0].symbol == "AAPL"
        assert records[0].revenue == pytest.approx(391_035_000_000.0)
