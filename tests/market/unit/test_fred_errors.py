"""Unit tests for FRED error classes.

FRED エラークラスのテストスイート。
FREDCacheNotFoundError の動作を検証する。
"""

import pytest

from market.errors import FREDCacheNotFoundError, FREDFetchError


class TestFREDCacheNotFoundError:
    """FREDCacheNotFoundError クラスのテスト。"""

    def test_正常系_単一シリーズIDでエラー作成(self) -> None:
        """単一のシリーズIDでエラーを作成できること。"""
        error = FREDCacheNotFoundError(series_ids=["GDP"])

        assert error.series_ids == ["GDP"]
        assert "GDP" in str(error)
        assert "sync_series" in str(error)
        assert 'sync_series("GDP")' in str(error)

    def test_正常系_複数シリーズIDでエラー作成(self) -> None:
        """複数のシリーズIDでエラーを作成できること。"""
        series_ids = ["GDP", "CPIAUCSL", "UNRATE"]
        error = FREDCacheNotFoundError(series_ids=series_ids)

        assert error.series_ids == series_ids
        assert "GDP" in str(error)
        assert "CPIAUCSL" in str(error)
        assert "UNRATE" in str(error)

    def test_正常系_FREDFetchErrorを継承(self) -> None:
        """FREDFetchError を継承していること。"""
        error = FREDCacheNotFoundError(series_ids=["GDP"])

        assert isinstance(error, FREDFetchError)

    def test_正常系_エラーメッセージに復旧方法を含む(self) -> None:
        """エラーメッセージに復旧方法が含まれること。"""
        error = FREDCacheNotFoundError(series_ids=["DGS10"])
        message = str(error)

        assert "FRED series not found in cache" in message
        assert "DGS10" in message
        assert "HistoricalCache().sync_series" in message

    def test_正常系_raiseで例外として使用可能(self) -> None:
        """raise で例外として使用できること。"""
        with pytest.raises(FREDCacheNotFoundError) as exc_info:
            raise FREDCacheNotFoundError(series_ids=["FEDFUNDS"])

        assert exc_info.value.series_ids == ["FEDFUNDS"]

    def test_正常系_FREDFetchErrorでキャッチ可能(self) -> None:
        """FREDFetchError でキャッチできること。"""
        with pytest.raises(FREDFetchError):
            raise FREDCacheNotFoundError(series_ids=["M2SL"])

    def test_エッジケース_空リストでもエラー作成可能(self) -> None:
        """空のリストでもエラーを作成できること（ただし推奨されない）。"""
        error = FREDCacheNotFoundError(series_ids=[])

        assert error.series_ids == []
        assert "FRED series not found in cache" in str(error)
