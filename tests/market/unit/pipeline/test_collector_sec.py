"""Unit tests for market.pipeline.collector_sec.SecEdgarCollector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from market.pipeline.collector_sec import CF_LABEL_FALLBACK, SecEdgarCollector

# ---------------------------------------------------------------------------
# CF_LABEL_FALLBACK
# ---------------------------------------------------------------------------


class TestCFLabelFallback:
    def test_正常系_dictである(self) -> None:
        assert isinstance(CF_LABEL_FALLBACK, dict)

    def test_正常系_空でない(self) -> None:
        assert len(CF_LABEL_FALLBACK) > 0

    def test_正常系_すべてのキーと値がstrである(self) -> None:
        for k, v in CF_LABEL_FALLBACK.items():
            assert isinstance(k, str), f"key {k!r} should be str"
            assert isinstance(v, str), f"value {v!r} should be str"


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestSecEdgarCollectorInit:
    def test_正常系_DIでstorageを注入できる(self) -> None:
        mock_storage = MagicMock()
        collector = SecEdgarCollector(storage=mock_storage)
        assert collector is not None

    def test_正常系_デフォルト引数で初期化できる(self) -> None:
        with patch("market.pipeline.collector_sec.SecEdgarStorage") as mock_cls:
            mock_cls.return_value = MagicMock()
            collector = SecEdgarCollector()
        assert collector is not None


# ---------------------------------------------------------------------------
# _import_company
# ---------------------------------------------------------------------------


class TestImportCompany:
    def test_正常系_edgartoolsのCompanyクラスを返す(self) -> None:
        collector = SecEdgarCollector(storage=MagicMock())
        company_cls = collector._import_company()
        # Must be a type/class (callable)
        assert callable(company_cls)

    def test_正常系_src_edgarではない(self) -> None:
        """Returned class must NOT be from src/edgar (namespace conflict avoidance)."""
        collector = SecEdgarCollector(storage=MagicMock())
        company_cls = collector._import_company()
        # The module should be from site-packages edgar.entity.core, not src/edgar
        module_path = getattr(company_cls, "__module__", "")
        # Must come from edgar package (site-packages), not our pipeline module
        assert "market.pipeline" not in str(module_path)
        # Class name should be "Company"
        assert company_cls.__name__ == "Company"

    def test_正常系_キャッシュされる(self) -> None:
        """Multiple calls return the same class object (lru_cache)."""
        collector = SecEdgarCollector(storage=MagicMock())
        cls1 = collector._import_company()
        cls2 = collector._import_company()
        assert cls1 is cls2


# ---------------------------------------------------------------------------
# collect_symbol
# ---------------------------------------------------------------------------


class TestCollectSymbol:
    def _make_filing_mock(
        self,
        statement_type: str,
        period: str = "2025-09-30",
        report_type: str = "annual",
    ) -> MagicMock:
        """Build a minimal filing mock that returns a financials DataFrame."""
        import pandas as pd

        # Build a minimal DataFrame row matching what edgartools returns
        df = pd.DataFrame(
            {
                "concept": ["us-gaap/Revenues"],
                "label": ["Revenue"],
                "value": [100_000_000.0],
                "dimension": [False],
                "abstract": [False],
                "standard_concept": ["revenue"],
                "period": [period],
            }
        )

        financials_mock = MagicMock()
        financials_mock.to_dataframe.return_value = df

        filing_mock = MagicMock()
        obj_mock = MagicMock()
        obj_mock.financials = financials_mock
        filing_mock.obj.return_value = obj_mock

        return filing_mock

    def test_正常系_ストレージのupsertが呼ばれる(self) -> None:
        mock_storage = MagicMock()
        mock_storage.upsert.return_value = 1

        company_mock = MagicMock()
        filing_10k = self._make_filing_mock("income", "2025-09-30")
        company_mock.get_filings.return_value.__iter__ = lambda s: iter([filing_10k])

        collector = SecEdgarCollector(storage=mock_storage)

        with patch.object(
            collector, "_import_company", return_value=lambda sym: company_mock
        ):
            collector.collect_symbol("AAPL", filing_types=["10-K"])

        mock_storage.upsert.assert_called()

    def test_正常系_デフォルト_filing_typesは10Kと10Qを含む(self) -> None:
        mock_storage = MagicMock()
        collector = SecEdgarCollector(storage=mock_storage)

        company_mock = MagicMock()
        company_mock.get_filings.return_value.__iter__ = lambda s: iter([])

        with patch.object(
            collector, "_import_company", return_value=lambda sym: company_mock
        ):
            collector.collect_symbol("AAPL")

        # get_filings should be called for both 10-K and 10-Q
        assert company_mock.get_filings.call_count == 2
        call_args_list = company_mock.get_filings.call_args_list
        form_types_called = {
            call[1].get("form") or call[0][0] for call in call_args_list
        }
        assert "10-K" in form_types_called
        assert "10-Q" in form_types_called

    def test_異常系_シンボルが空でも例外を適切に処理する(self) -> None:
        mock_storage = MagicMock()
        collector = SecEdgarCollector(storage=mock_storage)

        company_mock = MagicMock()
        company_mock.get_filings.side_effect = Exception("Symbol not found")

        with patch.object(
            collector, "_import_company", return_value=lambda sym: company_mock
        ):
            # Should not raise; errors should be caught
            result = collector.collect_symbol("INVALID_SYMBOL_XYZ")

        # upsert should not have been called
        mock_storage.upsert.assert_not_called()
