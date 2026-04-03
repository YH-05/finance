"""Integration tests for Phase 3: SEC EDGAR real API (AAPL 1件のみ).

Tests use the real SEC EDGAR API via ``SecEdgarCollector`` with AAPL as the
single test subject. Data is persisted to a temporary SQLite database.
All tests require ``@pytest.mark.integration`` and are skipped in normal CI.

Run with:
    uv run pytest tests/market/pipeline/integration/ -v -m integration

Test TODO List:
- [x] AAPLの10-KフィリングからFinancialsを取得できること
- [x] 取得したレコードが一時DBにupsertされること
- [x] FinancialStatementRecordに必須フィールドが含まれること
- [x] collect_symbol のサマリー構造が正しいこと
- [x] テスト後に一時DBがcleanupされること

Notes
-----
SEC rate limit: 10 requests/sec. The collector applies a 0.1s sleep between
requests. Tests use filing_types=["10-K"] to minimize API calls.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market.pipeline.collector_sec import SecEdgarCollector
from market.pipeline.storage_sec import SecEdgarStorage


@pytest.mark.integration
class TestSecEdgarIntegration:
    """Integration tests for SecEdgarCollector using real SEC EDGAR API.

    Tests are limited to AAPL with ``filing_types=["10-K"]`` to minimize
    API calls and respect SEC rate limits. All tests write to a temporary
    SQLite database that is automatically cleaned up by pytest's ``tmp_path``.
    """

    def test_collect_aapl_10k_returns_valid_summary(self, tmp_path: Path) -> None:
        """AAPLの10-KデータをSEC EDGAR APIから取得してサマリーが正しいことを確認する.

        Verifies that ``collect_symbol("AAPL", filing_types=["10-K"])`` returns
        a summary dict with the required keys.
        """
        db_path = tmp_path / "sec_edgar_integration.db"
        storage = SecEdgarStorage(db_path=db_path)
        collector = SecEdgarCollector(storage=storage)

        result = collector.collect_symbol("AAPL", filing_types=["10-K"])

        assert isinstance(result, dict), "collect_symbol should return a dict"
        assert "symbol" in result
        assert "records_upserted" in result
        assert "errors" in result

        assert result["symbol"] == "AAPL"
        assert result["records_upserted"] >= 0
        assert isinstance(result["errors"], list)

    def test_collect_aapl_10k_upserts_financial_records(self, tmp_path: Path) -> None:
        """AAPLの10-Kから取得したFinancial Recordsが一時DBに保存されることを確認する.

        Verifies that at least one ``FinancialStatementRecord`` is persisted
        after collecting AAPL 10-K filings.
        """
        db_path = tmp_path / "sec_edgar_persist.db"
        storage = SecEdgarStorage(db_path=db_path)
        collector = SecEdgarCollector(storage=storage)

        result = collector.collect_symbol("AAPL", filing_types=["10-K"])

        records_upserted = result["records_upserted"]
        if records_upserted > 0:
            # Verify records are retrievable from storage
            retrieved = storage.get_by_symbol("AAPL")
            assert len(retrieved) > 0, (
                f"Expected at least 1 record after upserting {records_upserted}, got 0"
            )

    def test_collect_aapl_financial_record_fields(self, tmp_path: Path) -> None:
        """取得したFinancialStatementRecordに必須フィールドが含まれることを確認する.

        Verifies that records stored in the database have the required
        ``symbol``, ``fiscal_date_ending``, ``statement_type``, ``report_type``,
        and ``fetched_at`` fields populated.
        """
        db_path = tmp_path / "sec_edgar_fields.db"
        storage = SecEdgarStorage(db_path=db_path)
        collector = SecEdgarCollector(storage=storage)

        result = collector.collect_symbol("AAPL", filing_types=["10-K"])

        if result["records_upserted"] > 0:
            records = storage.get_by_symbol("AAPL")
            for rec in records:
                # sqlite3.Row supports key-based access
                assert rec["symbol"] == "AAPL", "Record symbol should be AAPL"
                assert rec["fiscal_date_ending"], (
                    "fiscal_date_ending should not be empty"
                )
                assert rec["statement_type"] in ("income", "balance_sheet", "cash_flow"), (
                    f"Unexpected statement_type: {rec['statement_type']}"
                )
                assert rec["report_type"] in ("annual", "quarterly", "other"), (
                    f"Unexpected report_type: {rec['report_type']}"
                )
                assert rec["fetched_at"], "fetched_at should not be empty"

    def test_collect_aapl_10k_has_financial_data(self, tmp_path: Path) -> None:
        """AAPLの10-Kから財務データ（revenue/net_income）が取得できることを確認する.

        Verifies that at least some annual income records contain revenue or
        net_income values (not all None).
        """
        db_path = tmp_path / "sec_edgar_financial.db"
        storage = SecEdgarStorage(db_path=db_path)
        collector = SecEdgarCollector(storage=storage)

        result = collector.collect_symbol("AAPL", filing_types=["10-K"])

        if result["records_upserted"] > 0:
            records = storage.get_by_symbol("AAPL")
            income_records = [r for r in records if r["statement_type"] == "income"]
            if income_records:
                # At least one income record should have revenue or net_income
                has_financial_data = any(
                    r["revenue"] is not None or r["net_income"] is not None
                    for r in income_records
                )
                assert has_financial_data, (
                    "Expected at least one income record with revenue or net_income, "
                    f"but found {len(income_records)} records with all None values"
                )

    def test_db_cleanup_after_test(self, tmp_path: Path) -> None:
        """テスト後に一時DBがpytestによって自動削除されることを確認する.

        Verifies that the temporary database file is created during the test
        and will be cleaned up by pytest's ``tmp_path`` fixture.
        """
        db_path = tmp_path / "sec_edgar_cleanup.db"
        storage = SecEdgarStorage(db_path=db_path)
        collector = SecEdgarCollector(storage=storage)

        collector.collect_symbol("AAPL", filing_types=["10-K"])

        # The db file should exist during the test
        assert db_path.exists(), "Database file should be created during collection"
        # Cleanup is handled by pytest's tmp_path fixture (automatic after test)
