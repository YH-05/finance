"""Pytest fixtures for visualization tests.

This module provides fixtures for testing chart generation functionality
including sample portfolios, ticker info, and drift results.
"""

import pytest

from strategy.portfolio import Portfolio
from strategy.rebalance.types import DriftResult
from strategy.types import TickerInfo


# =============================================================================
# Portfolio Fixtures
# =============================================================================


@pytest.fixture
def simple_portfolio() -> Portfolio:
    """シンプルな 60/40 ポートフォリオを作成.

    Returns
    -------
    Portfolio
        VOO 60%, BND 40% の基本ポートフォリオ
    """
    return Portfolio(
        holdings=[("VOO", 0.6), ("BND", 0.4)],
        name="60/40 Portfolio",
    )


@pytest.fixture
def multi_asset_portfolio() -> Portfolio:
    """複数資産クラスのポートフォリオを作成.

    Returns
    -------
    Portfolio
        4銘柄のポートフォリオ
    """
    return Portfolio(
        holdings=[
            ("VOO", 0.40),
            ("BND", 0.30),
            ("VNQ", 0.15),
            ("GLD", 0.15),
        ],
        name="Multi-Asset Portfolio",
    )


@pytest.fixture
def single_holding_portfolio() -> Portfolio:
    """単一銘柄のポートフォリオを作成.

    Returns
    -------
    Portfolio
        VOO 100% の単一銘柄ポートフォリオ
    """
    return Portfolio(
        holdings=[("VOO", 1.0)],
        name="Single Asset",
    )


# =============================================================================
# TickerInfo Fixtures
# =============================================================================


@pytest.fixture
def sample_ticker_info() -> dict[str, TickerInfo]:
    """テスト用のティッカー情報を作成.

    Returns
    -------
    dict[str, TickerInfo]
        ティッカーをキーとするTickerInfo辞書
    """
    return {
        "VOO": TickerInfo(
            ticker="VOO",
            name="Vanguard S&P 500 ETF",
            sector="Broad Market",
            asset_class="equity",
        ),
        "BND": TickerInfo(
            ticker="BND",
            name="Vanguard Total Bond Market ETF",
            sector="Fixed Income",
            asset_class="bond",
        ),
        "VNQ": TickerInfo(
            ticker="VNQ",
            name="Vanguard Real Estate ETF",
            sector="Real Estate",
            asset_class="real_estate",
        ),
        "GLD": TickerInfo(
            ticker="GLD",
            name="SPDR Gold Shares",
            sector="Commodities",
            asset_class="commodity",
        ),
    }


# =============================================================================
# DriftResult Fixtures
# =============================================================================


@pytest.fixture
def sample_drift_results() -> list[DriftResult]:
    """テスト用のドリフト結果を作成.

    Returns
    -------
    list[DriftResult]
        2銘柄のドリフト結果（リバランス必要・不要の両方を含む）
    """
    return [
        DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        ),
        DriftResult(
            ticker="BND",
            target_weight=0.40,
            current_weight=0.35,
            drift=-0.05,
            drift_percent=-12.5,
            requires_rebalance=True,
        ),
    ]


@pytest.fixture
def no_drift_results() -> list[DriftResult]:
    """ドリフトなしの結果を作成.

    Returns
    -------
    list[DriftResult]
        ドリフトがゼロの結果
    """
    return [
        DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.60,
            drift=0.0,
            drift_percent=0.0,
            requires_rebalance=False,
        ),
        DriftResult(
            ticker="BND",
            target_weight=0.40,
            current_weight=0.40,
            drift=0.0,
            drift_percent=0.0,
            requires_rebalance=False,
        ),
    ]


@pytest.fixture
def multi_asset_drift_results() -> list[DriftResult]:
    """複数資産のドリフト結果を作成.

    Returns
    -------
    list[DriftResult]
        4銘柄のドリフト結果
    """
    return [
        DriftResult(
            ticker="VOO",
            target_weight=0.40,
            current_weight=0.45,
            drift=0.05,
            drift_percent=12.5,
            requires_rebalance=True,
        ),
        DriftResult(
            ticker="BND",
            target_weight=0.30,
            current_weight=0.28,
            drift=-0.02,
            drift_percent=-6.67,
            requires_rebalance=False,
        ),
        DriftResult(
            ticker="VNQ",
            target_weight=0.15,
            current_weight=0.12,
            drift=-0.03,
            drift_percent=-20.0,
            requires_rebalance=True,
        ),
        DriftResult(
            ticker="GLD",
            target_weight=0.15,
            current_weight=0.15,
            drift=0.0,
            drift_percent=0.0,
            requires_rebalance=False,
        ),
    ]
