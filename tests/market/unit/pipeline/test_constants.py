"""Unit tests for market.pipeline.constants."""

from typing import Final

import pytest

from market.pipeline import constants


class TestDatabaseNameConstants:
    def test_正常系_NASDAQ_CALENDAR_DB_NAMEが正しい値を持つ(self) -> None:
        assert constants.NASDAQ_CALENDAR_DB_NAME == "nasdaq_calendar"

    def test_正常系_SEC_EDGAR_DB_NAMEが正しい値を持つ(self) -> None:
        assert constants.SEC_EDGAR_DB_NAME == "sec_edgar"

    def test_正常系_YFINANCE_DB_NAMEが正しい値を持つ(self) -> None:
        assert constants.YFINANCE_DB_NAME == "yfinance"


class TestEnvironmentVariableConstants:
    def test_正常系_PIPELINE_NASDAQ_DB_PATH_ENVが正しい値を持つ(self) -> None:
        assert constants.PIPELINE_NASDAQ_DB_PATH_ENV == "PIPELINE_NASDAQ_DB_PATH"

    def test_正常系_PIPELINE_SEC_EDGAR_DB_PATH_ENVが正しい値を持つ(self) -> None:
        assert constants.PIPELINE_SEC_EDGAR_DB_PATH_ENV == "PIPELINE_SEC_EDGAR_DB_PATH"

    def test_正常系_PIPELINE_YFINANCE_DB_PATH_ENVが正しい値を持つ(self) -> None:
        assert constants.PIPELINE_YFINANCE_DB_PATH_ENV == "PIPELINE_YFINANCE_DB_PATH"


class TestTableNameConstants:
    def test_正常系_TABLE_NC_EARNINGS_CALENDARが正しい値を持つ(self) -> None:
        assert constants.TABLE_NC_EARNINGS_CALENDAR == "nc_earnings_calendar"

    def test_正常系_TABLE_NC_COLLECTION_QUEUEが正しい値を持つ(self) -> None:
        assert constants.TABLE_NC_COLLECTION_QUEUE == "nc_collection_queue"

    def test_正常系_TABLE_SE_FINANCIAL_STATEMENTSが正しい値を持つ(self) -> None:
        assert constants.TABLE_SE_FINANCIAL_STATEMENTS == "se_financial_statements"

    def test_正常系_TABLE_YF_DAILY_PRICESが正しい値を持つ(self) -> None:
        assert constants.TABLE_YF_DAILY_PRICES == "yf_daily_prices"


class TestDefaultValueConstants:
    def test_正常系_AV_DEFAULT_DAILY_BUDGETが25である(self) -> None:
        assert constants.AV_DEFAULT_DAILY_BUDGET == 25

    def test_正常系_AV_DEFAULT_DAILY_BUDGETがint型である(self) -> None:
        assert isinstance(constants.AV_DEFAULT_DAILY_BUDGET, int)
