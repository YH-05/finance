"""Unit tests for TSAPassengerDataCollector.

This module tests the TSAPassengerDataCollector class including:
- Inheritance from DataCollector base class
- fetch() method with start_date and end_date parameters
- validate() method for data validation
- Web scraping logic with mocked HTTP responses
- Error handling for network issues
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.base_collector import DataCollector
from market.tsa import TSAPassengerDataCollector


class TestTSAPassengerDataCollectorInheritance:
    """Test TSAPassengerDataCollector inheritance."""

    def test_正常系_DataCollectorを継承している(self) -> None:
        collector = TSAPassengerDataCollector()
        assert isinstance(collector, DataCollector)

    def test_正常系_nameプロパティがクラス名を返す(self) -> None:
        collector = TSAPassengerDataCollector()
        assert collector.name == "TSAPassengerDataCollector"


class TestTSAPassengerDataCollectorFetch:
    """Test the fetch method."""

    def test_正常系_fetchメソッドがDataFrameを返す(self) -> None:
        """Mock HTTP response and verify fetch returns DataFrame."""
        html_content = """
        <html>
        <body>
        <table>
            <tbody>
                <tr>
                    <td>01/15/2024</td>
                    <td>2,500,000</td>
                </tr>
                <tr>
                    <td>01/14/2024</td>
                    <td>2,400,000</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = MagicMock()

        with patch("market.tsa.requests.get", return_value=mock_response):
            collector = TSAPassengerDataCollector()
            df = collector.fetch(start_date="2024-01-01", end_date="2024-01-31")

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert "Date" in df.columns
            assert "Numbers" in df.columns

    def test_正常系_fetchがstart_dateとend_dateでフィルタする(self) -> None:
        """Verify date filtering works correctly."""
        html_content = """
        <html>
        <body>
        <table>
            <tbody>
                <tr>
                    <td>01/20/2024</td>
                    <td>2,600,000</td>
                </tr>
                <tr>
                    <td>01/15/2024</td>
                    <td>2,500,000</td>
                </tr>
                <tr>
                    <td>01/10/2024</td>
                    <td>2,400,000</td>
                </tr>
                <tr>
                    <td>01/05/2024</td>
                    <td>2,300,000</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = MagicMock()

        with patch("market.tsa.requests.get", return_value=mock_response):
            collector = TSAPassengerDataCollector()
            df = collector.fetch(start_date="2024-01-10", end_date="2024-01-18")

            assert len(df) == 2
            dates = df["Date"].tolist()
            assert all(
                datetime(2024, 1, 10) <= d <= datetime(2024, 1, 18) for d in dates
            )

    def test_正常系_fetchがyear引数を受け取る(self) -> None:
        """Verify year parameter is passed to URL."""
        html_content = """
        <html>
        <body>
        <table>
            <tbody>
                <tr>
                    <td>06/15/2023</td>
                    <td>2,500,000</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = MagicMock()

        with patch("market.tsa.requests.get", return_value=mock_response) as mock_get:
            collector = TSAPassengerDataCollector()
            collector.fetch(year=2023)

            # Verify the year was appended to URL
            call_args = mock_get.call_args
            assert "2023" in call_args[0][0]

    def test_異常系_ネットワークエラーで例外を送出(self) -> None:
        """Verify network errors are properly raised."""
        import requests

        with patch(
            "market.tsa.requests.get",
            side_effect=requests.exceptions.ConnectionError("Network error"),
        ):
            collector = TSAPassengerDataCollector()
            with pytest.raises(requests.exceptions.ConnectionError):
                collector.fetch()

    def test_異常系_テーブルが見つからない場合(self) -> None:
        """Verify handling when no table is found."""
        html_content = """
        <html>
        <body>
        <div>No table here</div>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = MagicMock()

        with patch("market.tsa.requests.get", return_value=mock_response):
            collector = TSAPassengerDataCollector()
            df = collector.fetch()

            # Should return empty DataFrame when no table found
            assert isinstance(df, pd.DataFrame)
            assert df.empty


class TestTSAPassengerDataCollectorValidate:
    """Test the validate method."""

    def test_正常系_有効なDataFrameでTrueを返す(self) -> None:
        collector = TSAPassengerDataCollector()
        df = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-15", "2024-01-16"]),
                "Numbers": [2500000, 2600000],
            }
        )
        assert collector.validate(df) is True

    def test_異常系_空のDataFrameでFalseを返す(self) -> None:
        collector = TSAPassengerDataCollector()
        df = pd.DataFrame()
        assert collector.validate(df) is False

    def test_異常系_Dateカラムがない場合Falseを返す(self) -> None:
        collector = TSAPassengerDataCollector()
        df = pd.DataFrame({"Numbers": [2500000, 2600000]})
        assert collector.validate(df) is False

    def test_異常系_Numbersカラムがない場合Falseを返す(self) -> None:
        collector = TSAPassengerDataCollector()
        df = pd.DataFrame({"Date": pd.to_datetime(["2024-01-15", "2024-01-16"])})
        assert collector.validate(df) is False

    def test_異常系_Numbersに負の値がある場合Falseを返す(self) -> None:
        collector = TSAPassengerDataCollector()
        df = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-15", "2024-01-16"]),
                "Numbers": [2500000, -100],
            }
        )
        assert collector.validate(df) is False


class TestTSAPassengerDataCollectorCollect:
    """Test the collect method (inherited from DataCollector)."""

    def test_正常系_collectがfetchとvalidateを実行(self) -> None:
        """Verify collect() calls both fetch() and validate()."""
        html_content = """
        <html>
        <body>
        <table>
            <tbody>
                <tr>
                    <td>01/15/2024</td>
                    <td>2,500,000</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = MagicMock()

        with patch("market.tsa.requests.get", return_value=mock_response):
            collector = TSAPassengerDataCollector()
            df = collector.collect()

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1


class TestTSAPassengerDataCollectorDocstrings:
    """Test that all public methods have proper docstrings."""

    def test_正常系_クラスにDocstringがある(self) -> None:
        assert TSAPassengerDataCollector.__doc__ is not None
        assert "TSA" in TSAPassengerDataCollector.__doc__

    def test_正常系_fetchメソッドにDocstringがある(self) -> None:
        assert TSAPassengerDataCollector.fetch.__doc__ is not None

    def test_正常系_validateメソッドにDocstringがある(self) -> None:
        assert TSAPassengerDataCollector.validate.__doc__ is not None


class TestTSAPassengerDataCollectorLogging:
    """Test logging functionality."""

    def test_正常系_fetchでログが出力される(self) -> None:
        """Verify structlog logger is used."""
        html_content = """
        <html>
        <body>
        <table>
            <tbody>
                <tr>
                    <td>01/15/2024</td>
                    <td>2,500,000</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = MagicMock()

        with (
            patch("market.tsa.requests.get", return_value=mock_response),
            patch("market.tsa.logger") as mock_logger,
        ):
            collector = TSAPassengerDataCollector()
            collector.fetch()

            # Verify logger was called
            assert mock_logger.debug.called or mock_logger.info.called


class TestTSAPassengerDataCollectorExports:
    """Test module exports."""

    def test_正常系_TSAPassengerDataCollectorがエクスポートされている(self) -> None:
        from market.tsa import __all__

        assert "TSAPassengerDataCollector" in __all__
