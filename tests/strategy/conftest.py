"""Pytest configuration and fixtures for strategy."""

import logging
import os
import tempfile
from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import pytest

if TYPE_CHECKING:
    from strategy.risk.metrics import RiskMetricsResult


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """Create sample data for testing."""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables for each test."""
    test_env_vars = [var for var in os.environ if var.startswith("TEST_")]
    for var in test_env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture logs for testing with proper level."""
    caplog.set_level(logging.DEBUG)
    return caplog


# =============================================================================
# Risk Calculation Fixtures
# =============================================================================


@pytest.fixture
def sample_returns() -> pd.Series:
    """テスト用の日次リターンデータを生成.

    Returns
    -------
    pd.Series
        正負混合のリターンデータ（100日分）

    Notes
    -----
    シード値を固定して再現性を確保している。
    """
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.015, 100)  # 平均0.05%, 標準偏差1.5%
    return pd.Series(
        returns,
        index=pd.date_range("2023-01-01", periods=100, freq="B"),
        name="daily_returns",
    )


@pytest.fixture
def positive_returns() -> pd.Series:
    """全て正のリターンデータを生成.

    Returns
    -------
    pd.Series
        全て正のリターンデータ（50日分）
    """
    np.random.seed(123)
    returns = np.abs(np.random.normal(0.005, 0.01, 50))  # 全て正
    return pd.Series(
        returns,
        index=pd.date_range("2023-01-01", periods=50, freq="B"),
        name="positive_returns",
    )


@pytest.fixture
def negative_returns() -> pd.Series:
    """全て負のリターンデータを生成.

    Returns
    -------
    pd.Series
        全て負のリターンデータ（50日分）
    """
    np.random.seed(456)
    returns = -np.abs(np.random.normal(0.005, 0.01, 50))  # 全て負
    return pd.Series(
        returns,
        index=pd.date_range("2023-01-01", periods=50, freq="B"),
        name="negative_returns",
    )


@pytest.fixture
def valid_metrics_data() -> dict[str, Any]:
    """有効な RiskMetricsResult データを生成.

    Returns
    -------
    dict[str, Any]
        RiskMetricsResult の全フィールドを含む辞書
    """
    return {
        "volatility": 0.15,
        "sharpe_ratio": 1.2,
        "sortino_ratio": 1.5,
        "max_drawdown": -0.10,
        "var_95": -0.02,
        "var_99": -0.03,
        "beta": 1.1,
        "treynor_ratio": 0.08,
        "information_ratio": 0.5,
        "annualized_return": 0.08,
        "cumulative_return": 0.25,
        "calculated_at": datetime(2023, 12, 31, 15, 30, 0),
        "period_start": date(2023, 1, 1),
        "period_end": date(2023, 12, 31),
    }


@pytest.fixture
def sample_metrics_result(valid_metrics_data: dict[str, Any]) -> "RiskMetricsResult":
    """テスト用の RiskMetricsResult インスタンスを生成.

    Parameters
    ----------
    valid_metrics_data : dict[str, Any]
        有効なメトリクスデータ

    Returns
    -------
    RiskMetricsResult
        テスト用のメトリクス結果
    """
    from strategy.risk.metrics import RiskMetricsResult

    return RiskMetricsResult(**valid_metrics_data)


@pytest.fixture
def benchmark_returns() -> pd.Series:
    """ベンチマーク用の日次リターンデータを生成.

    Returns
    -------
    pd.Series
        ベンチマークのリターンデータ（100日分）

    Notes
    -----
    sample_returns と同じ期間で、相関のあるデータを生成。
    """
    np.random.seed(100)
    returns = np.random.normal(0.0003, 0.012, 100)  # 平均0.03%, 標準偏差1.2%
    return pd.Series(
        returns,
        index=pd.date_range("2023-01-01", periods=100, freq="B"),
        name="benchmark_returns",
    )
