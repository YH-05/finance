"""Tests for ca_strategy neutralizer module.

SectorNeutralizer wraps the existing Normalizer to apply
sector-neutral Z-score normalization and ranking to stock scores.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dev.ca_strategy.neutralizer import SectorNeutralizer
from dev.ca_strategy.types import UniverseConfig, UniverseTicker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_universe(
    tickers_sectors: list[tuple[str, str]],
) -> UniverseConfig:
    """Create a UniverseConfig from (ticker, sector) pairs."""
    return UniverseConfig(
        tickers=[UniverseTicker(ticker=t, gics_sector=s) for t, s in tickers_sectors]
    )


def _make_scores_df(
    data: list[dict],
) -> pd.DataFrame:
    """Create a scores DataFrame with required columns."""
    return pd.DataFrame(data)


# ===========================================================================
# SectorNeutralizer
# ===========================================================================
class TestSectorNeutralizer:
    """SectorNeutralizer class tests."""

    # -----------------------------------------------------------------------
    # Instantiation
    # -----------------------------------------------------------------------
    def test_正常系_デフォルト設定で作成できる(self) -> None:
        neutralizer = SectorNeutralizer()
        assert neutralizer is not None

    def test_正常系_カスタムmin_samplesで作成できる(self) -> None:
        neutralizer = SectorNeutralizer(min_samples=3)
        assert neutralizer is not None

    # -----------------------------------------------------------------------
    # neutralize – basic
    # -----------------------------------------------------------------------
    def test_正常系_セクター内Zスコアが計算される(self) -> None:
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
                ("MSFT", "Information Technology"),
                ("GOOGL", "Information Technology"),
                ("AMZN", "Information Technology"),
                ("META", "Information Technology"),
            ]
        )
        scores_df = _make_scores_df(
            [
                {"ticker": "AAPL", "aggregate_score": 0.9, "as_of_date": "2024-01-01"},
                {"ticker": "MSFT", "aggregate_score": 0.7, "as_of_date": "2024-01-01"},
                {"ticker": "GOOGL", "aggregate_score": 0.5, "as_of_date": "2024-01-01"},
                {"ticker": "AMZN", "aggregate_score": 0.3, "as_of_date": "2024-01-01"},
                {"ticker": "META", "aggregate_score": 0.6, "as_of_date": "2024-01-01"},
            ]
        )

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        assert "sector_zscore" in result.columns
        assert "sector_rank" in result.columns
        assert "gics_sector" in result.columns

    def test_正常系_複数セクターで独立にZスコアが計算される(self) -> None:
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
                ("MSFT", "Information Technology"),
                ("GOOGL", "Information Technology"),
                ("AMZN", "Information Technology"),
                ("META", "Information Technology"),
                ("JPM", "Financials"),
                ("BAC", "Financials"),
                ("GS", "Financials"),
                ("MS", "Financials"),
                ("C", "Financials"),
            ]
        )
        scores_df = _make_scores_df(
            [
                {"ticker": "AAPL", "aggregate_score": 0.9, "as_of_date": "2024-01-01"},
                {"ticker": "MSFT", "aggregate_score": 0.7, "as_of_date": "2024-01-01"},
                {"ticker": "GOOGL", "aggregate_score": 0.5, "as_of_date": "2024-01-01"},
                {"ticker": "AMZN", "aggregate_score": 0.3, "as_of_date": "2024-01-01"},
                {"ticker": "META", "aggregate_score": 0.6, "as_of_date": "2024-01-01"},
                {"ticker": "JPM", "aggregate_score": 0.85, "as_of_date": "2024-01-01"},
                {"ticker": "BAC", "aggregate_score": 0.65, "as_of_date": "2024-01-01"},
                {"ticker": "GS", "aggregate_score": 0.75, "as_of_date": "2024-01-01"},
                {"ticker": "MS", "aggregate_score": 0.55, "as_of_date": "2024-01-01"},
                {"ticker": "C", "aggregate_score": 0.45, "as_of_date": "2024-01-01"},
            ]
        )

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        # Each sector should have independent Z-scores
        tech_rows = result[result["gics_sector"] == "Information Technology"]
        fin_rows = result[result["gics_sector"] == "Financials"]

        assert len(tech_rows) == 5
        assert len(fin_rows) == 5
        # Z-scores are sector-relative, not cross-sector
        assert bool(tech_rows["sector_zscore"].notna().all())
        assert bool(fin_rows["sector_zscore"].notna().all())

    # -----------------------------------------------------------------------
    # neutralize – sector_rank
    # -----------------------------------------------------------------------
    def test_正常系_sector_rankがスコア順で付与される(self) -> None:
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
                ("MSFT", "Information Technology"),
                ("GOOGL", "Information Technology"),
                ("AMZN", "Information Technology"),
                ("META", "Information Technology"),
            ]
        )
        scores_df = _make_scores_df(
            [
                {"ticker": "AAPL", "aggregate_score": 0.9, "as_of_date": "2024-01-01"},
                {"ticker": "MSFT", "aggregate_score": 0.7, "as_of_date": "2024-01-01"},
                {"ticker": "GOOGL", "aggregate_score": 0.5, "as_of_date": "2024-01-01"},
                {"ticker": "AMZN", "aggregate_score": 0.3, "as_of_date": "2024-01-01"},
                {"ticker": "META", "aggregate_score": 0.6, "as_of_date": "2024-01-01"},
            ]
        )

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        # AAPL (0.9) should have rank 1, AMZN (0.3) should have the lowest rank
        aapl_row = result[result["ticker"] == "AAPL"]
        amzn_row = result[result["ticker"] == "AMZN"]
        assert aapl_row["sector_rank"].values[0] == 1
        assert amzn_row["sector_rank"].values[0] == 5

    # -----------------------------------------------------------------------
    # neutralize – universe mapping
    # -----------------------------------------------------------------------
    def test_正常系_ユニバースからセクター情報がマッピングされる(self) -> None:
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
                ("MSFT", "Information Technology"),
                ("GOOGL", "Information Technology"),
                ("AMZN", "Information Technology"),
                ("META", "Information Technology"),
            ]
        )
        scores_df = _make_scores_df(
            [
                {"ticker": "AAPL", "aggregate_score": 0.9, "as_of_date": "2024-01-01"},
                {"ticker": "MSFT", "aggregate_score": 0.7, "as_of_date": "2024-01-01"},
                {"ticker": "GOOGL", "aggregate_score": 0.5, "as_of_date": "2024-01-01"},
                {"ticker": "AMZN", "aggregate_score": 0.3, "as_of_date": "2024-01-01"},
                {"ticker": "META", "aggregate_score": 0.6, "as_of_date": "2024-01-01"},
            ]
        )

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        assert (
            result[result["ticker"] == "AAPL"]["gics_sector"].values[0]
            == "Information Technology"
        )

    def test_正常系_ユニバースにない銘柄は除外される(self) -> None:
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
                ("MSFT", "Information Technology"),
                ("GOOGL", "Information Technology"),
                ("AMZN", "Information Technology"),
                ("META", "Information Technology"),
            ]
        )
        scores_df = _make_scores_df(
            [
                {"ticker": "AAPL", "aggregate_score": 0.9, "as_of_date": "2024-01-01"},
                {"ticker": "MSFT", "aggregate_score": 0.7, "as_of_date": "2024-01-01"},
                {"ticker": "GOOGL", "aggregate_score": 0.5, "as_of_date": "2024-01-01"},
                {"ticker": "AMZN", "aggregate_score": 0.3, "as_of_date": "2024-01-01"},
                {"ticker": "META", "aggregate_score": 0.6, "as_of_date": "2024-01-01"},
                {
                    "ticker": "UNKNOWN",
                    "aggregate_score": 0.5,
                    "as_of_date": "2024-01-01",
                },
            ]
        )

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        assert "UNKNOWN" not in result["ticker"].values

    # -----------------------------------------------------------------------
    # neutralize – robust Z-score
    # -----------------------------------------------------------------------
    def test_正常系_robust_Zscoreが使用される(self) -> None:
        """Robust Z-score uses median and MAD instead of mean and std."""
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
                ("MSFT", "Information Technology"),
                ("GOOGL", "Information Technology"),
                ("AMZN", "Information Technology"),
                ("META", "Information Technology"),
                ("NVDA", "Information Technology"),
            ]
        )
        # Include an outlier (NVDA with 0.99)
        scores_df = _make_scores_df(
            [
                {"ticker": "AAPL", "aggregate_score": 0.5, "as_of_date": "2024-01-01"},
                {"ticker": "MSFT", "aggregate_score": 0.51, "as_of_date": "2024-01-01"},
                {
                    "ticker": "GOOGL",
                    "aggregate_score": 0.52,
                    "as_of_date": "2024-01-01",
                },
                {"ticker": "AMZN", "aggregate_score": 0.49, "as_of_date": "2024-01-01"},
                {"ticker": "META", "aggregate_score": 0.48, "as_of_date": "2024-01-01"},
                {"ticker": "NVDA", "aggregate_score": 0.99, "as_of_date": "2024-01-01"},
            ]
        )

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        # With robust Z-score, the outlier NVDA should have a high Z-score
        nvda_zscore = result[result["ticker"] == "NVDA"]["sector_zscore"].values[0]
        assert nvda_zscore > 1.0  # Should be significantly positive

    # -----------------------------------------------------------------------
    # neutralize – return type
    # -----------------------------------------------------------------------
    def test_正常系_DataFrameが返却される(self) -> None:
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
                ("MSFT", "Information Technology"),
                ("GOOGL", "Information Technology"),
                ("AMZN", "Information Technology"),
                ("META", "Information Technology"),
            ]
        )
        scores_df = _make_scores_df(
            [
                {"ticker": "AAPL", "aggregate_score": 0.9, "as_of_date": "2024-01-01"},
                {"ticker": "MSFT", "aggregate_score": 0.7, "as_of_date": "2024-01-01"},
                {"ticker": "GOOGL", "aggregate_score": 0.5, "as_of_date": "2024-01-01"},
                {"ticker": "AMZN", "aggregate_score": 0.3, "as_of_date": "2024-01-01"},
                {"ticker": "META", "aggregate_score": 0.6, "as_of_date": "2024-01-01"},
            ]
        )

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        assert isinstance(result, pd.DataFrame)
        # Original columns should be preserved
        assert "ticker" in result.columns
        assert "aggregate_score" in result.columns
        assert "as_of_date" in result.columns

    # -----------------------------------------------------------------------
    # Edge cases
    # -----------------------------------------------------------------------
    def test_エッジケース_空のDataFrameで空の結果を返す(self) -> None:
        universe = _make_universe(
            [
                ("AAPL", "Information Technology"),
            ]
        )
        scores_df = _make_scores_df([])

        neutralizer = SectorNeutralizer(min_samples=3)
        result = neutralizer.neutralize(scores_df, universe)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
