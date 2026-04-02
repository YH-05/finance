"""Unit tests for market.nse.collectors._base module.

NseCollectorMixin の動作を検証するテストスイート。
セッション DI パターンの共通 Mixin テスト。

Test TODO List:
- [x] NseCollectorMixin: session なしで初期化
- [x] NseCollectorMixin: session 注入で初期化
- [x] _get_session(): 注入なし時に新規セッション生成（should_close=True）
- [x] _get_session(): 注入あり時に既存セッション返却（should_close=False）
- [x] collectors/__init__.py: 4 コレクターが re-export されている
"""

from unittest.mock import MagicMock, patch

import pytest

from market.nse.collectors._base import NseCollectorMixin
from market.nse.session import NseSession


# =============================================================================
# Concrete subclass for testing the Mixin
# =============================================================================


class _ConcreteCollector(NseCollectorMixin):
    """Concrete subclass for testing NseCollectorMixin."""

    pass


# =============================================================================
# Tests: NseCollectorMixin initialization
# =============================================================================


class TestNseCollectorMixinInit:
    def test_正常系_sessionなしで初期化(self) -> None:
        collector = _ConcreteCollector()
        assert collector._session_instance is None

    def test_正常系_session注入で初期化(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = _ConcreteCollector(session=mock_session)
        assert collector._session_instance is mock_session


# =============================================================================
# Tests: _get_session()
# =============================================================================


class TestGetSession:
    def test_正常系_注入なし時に新規セッション生成_should_close_True(self) -> None:
        collector = _ConcreteCollector()
        with patch("market.nse.collectors._base.NseSession") as mock_cls:
            mock_instance = MagicMock(spec=NseSession)
            mock_cls.return_value = mock_instance
            session, should_close = collector._get_session()
        assert should_close is True
        assert session is mock_instance
        mock_cls.assert_called_once()

    def test_正常系_注入あり時に既存セッション返却_should_close_False(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = _ConcreteCollector(session=mock_session)
        session, should_close = collector._get_session()
        assert should_close is False
        assert session is mock_session


# =============================================================================
# Tests: collectors/__init__.py exports
# =============================================================================


class TestCollectorsInit:
    def test_正常系_QuoteCollectorがre_export(self) -> None:
        from market.nse.collectors import QuoteCollector

        assert QuoteCollector is not None

    def test_正常系_IndicesCollectorがre_export(self) -> None:
        from market.nse.collectors import IndicesCollector

        assert IndicesCollector is not None

    def test_正常系_CorporateCollectorがre_export(self) -> None:
        from market.nse.collectors import CorporateCollector

        assert CorporateCollector is not None

    def test_正常系_StockListCollectorがre_export(self) -> None:
        from market.nse.collectors import StockListCollector

        assert StockListCollector is not None

    def test_正常系_all完全性(self) -> None:
        import market.nse.collectors as collectors_module

        assert "QuoteCollector" in collectors_module.__all__
        assert "IndicesCollector" in collectors_module.__all__
        assert "CorporateCollector" in collectors_module.__all__
        assert "StockListCollector" in collectors_module.__all__
