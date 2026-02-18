"""Tests for ca_strategy portfolio_builder module.

PortfolioBuilder constructs a portfolio from ranked stock scores and
benchmark sector weights.

Key behaviors:
- Sector allocation matches benchmark weights
- Within each sector, top-N stocks by score are selected
- Intra-sector weights are score-proportional (normalized)
- All portfolio weights sum to 1.0
"""

from __future__ import annotations

from datetime import date

import pytest

from dev.ca_strategy.portfolio_builder import PortfolioBuilder, RankedStock
from dev.ca_strategy.types import (
    BenchmarkWeight,
    PortfolioHolding,
    PortfolioResult,
    SectorAllocation,
    StockScore,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_stock_score(
    ticker: str = "AAPL",
    aggregate_score: float = 0.8,
    sector: str = "Information Technology",
    claim_count: int = 3,
) -> RankedStock:
    """Create a ranked stock entry dict (as from neutralizer output)."""
    return RankedStock(
        ticker=ticker,
        aggregate_score=aggregate_score,
        gics_sector=sector,
        sector_rank=1,
        claim_count=claim_count,
        structural_weight=0.5,
    )


def _make_benchmark_weights() -> list[BenchmarkWeight]:
    """Create minimal benchmark weights for testing."""
    return [
        BenchmarkWeight(sector="Information Technology", weight=0.40),
        BenchmarkWeight(sector="Financials", weight=0.30),
        BenchmarkWeight(sector="Health Care", weight=0.30),
    ]


def _make_ranked_data(
    sectors: dict[str, list[tuple[str, float]]] | None = None,
) -> list[RankedStock]:
    """Create ranked stock data with sector info.

    Parameters
    ----------
    sectors : dict mapping sector name to list of (ticker, score) tuples
    """
    if sectors is None:
        sectors = {
            "Information Technology": [
                ("AAPL", 0.9),
                ("MSFT", 0.8),
                ("GOOGL", 0.7),
                ("INTC", 0.6),
            ],
            "Financials": [
                ("JPM", 0.85),
                ("GS", 0.75),
                ("MS", 0.65),
            ],
            "Health Care": [
                ("JNJ", 0.88),
                ("PFE", 0.78),
                ("MRK", 0.68),
            ],
        }
    ranked: list[RankedStock] = []
    for sector, stocks in sectors.items():
        for rank, (ticker, score) in enumerate(stocks, 1):
            ranked.append(
                RankedStock(
                    ticker=ticker,
                    aggregate_score=score,
                    gics_sector=sector,
                    sector_rank=rank,
                    claim_count=3,
                    structural_weight=0.5,
                )
            )
    return ranked


# ===========================================================================
# PortfolioBuilder
# ===========================================================================
class TestPortfolioBuilder:
    """PortfolioBuilder class tests."""

    # -----------------------------------------------------------------------
    # Instantiation
    # -----------------------------------------------------------------------
    def test_正常系_デフォルトパラメータで作成できる(self) -> None:
        builder = PortfolioBuilder()
        assert builder is not None

    def test_正常系_カスタムtarget_sizeで作成できる(self) -> None:
        builder = PortfolioBuilder(target_size=50)
        assert builder is not None

    # -----------------------------------------------------------------------
    # build – basic portfolio construction
    # -----------------------------------------------------------------------
    def test_正常系_ポートフォリオを構築できる(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        assert isinstance(result, PortfolioResult)
        assert len(result.holdings) > 0
        assert len(result.sector_allocations) > 0

    def test_正常系_holdingsがPortfolioHolding型で返される(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        for h in result.holdings:
            assert isinstance(h, PortfolioHolding)

    def test_正常系_sector_allocationsがSectorAllocation型で返される(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        for sa in result.sector_allocations:
            assert isinstance(sa, SectorAllocation)

    # -----------------------------------------------------------------------
    # build – weight normalization
    # -----------------------------------------------------------------------
    def test_正常系_全ウェイト合計が1_0になる(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        total_weight = sum(h.weight for h in result.holdings)
        assert total_weight == pytest.approx(1.0, abs=1e-9)

    # -----------------------------------------------------------------------
    # build – sector allocation
    # -----------------------------------------------------------------------
    def test_正常系_セクター配分がベンチマークウェイトに一致する(self) -> None:
        builder = PortfolioBuilder(target_size=10)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        sector_weights: dict[str, float] = {}
        for h in result.holdings:
            sector_weights[h.sector] = sector_weights.get(h.sector, 0.0) + h.weight

        # Each sector's actual weight should approximate the benchmark
        benchmark_map = {bw.sector: bw.weight for bw in benchmark}
        for sector, actual in sector_weights.items():
            expected = benchmark_map.get(sector, 0.0)
            assert actual == pytest.approx(expected, abs=0.05), (
                f"Sector {sector}: actual={actual:.4f}, expected={expected:.4f}"
            )

    # -----------------------------------------------------------------------
    # build – stock selection within sectors
    # -----------------------------------------------------------------------
    def test_正常系_各セクターからスコア上位N銘柄が選択される(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        # IT: 40% of 6 = ~2.4 -> 2 stocks
        # Fin: 30% of 6 = ~1.8 -> 2 stocks
        # HC: 30% of 6 = ~1.8 -> 2 stocks
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        tickers = {h.ticker for h in result.holdings}
        # Top IT stocks should be selected (AAPL, MSFT are top-2)
        # At minimum, AAPL should be included as the highest scorer in IT
        assert "AAPL" in tickers

    def test_正常系_セクター内ウェイトがスコア比例配分される(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        # Within each sector, higher-score stocks should have higher weights
        sector_holdings: dict[str, list[PortfolioHolding]] = {}
        for h in result.holdings:
            sector_holdings.setdefault(h.sector, []).append(h)

        for sector, holdings in sector_holdings.items():
            if len(holdings) >= 2:
                sorted_by_score = sorted(holdings, key=lambda x: x.score, reverse=True)
                sorted_by_weight = sorted(
                    holdings, key=lambda x: x.weight, reverse=True
                )
                # The ordering by score and weight should match
                assert [h.ticker for h in sorted_by_score] == [
                    h.ticker for h in sorted_by_weight
                ], f"Sector {sector}: score order does not match weight order"

    # -----------------------------------------------------------------------
    # build – edge cases
    # -----------------------------------------------------------------------
    def test_エッジケース_空のランキングデータで空ポートフォリオを返す(self) -> None:
        builder = PortfolioBuilder(target_size=30)
        benchmark = _make_benchmark_weights()

        result = builder.build(
            ranked=[],
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        assert isinstance(result, PortfolioResult)
        assert result.holdings == []
        assert result.sector_allocations == []

    def test_エッジケース_セクターの銘柄数が不足しても動作する(self) -> None:
        builder = PortfolioBuilder(target_size=30)
        benchmark = _make_benchmark_weights()
        # Only 1 stock per sector
        ranked = _make_ranked_data(
            sectors={
                "Information Technology": [("AAPL", 0.9)],
                "Financials": [("JPM", 0.85)],
                "Health Care": [("JNJ", 0.88)],
            }
        )

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        assert len(result.holdings) == 3
        total_weight = sum(h.weight for h in result.holdings)
        assert total_weight == pytest.approx(1.0, abs=1e-9)

    def test_エッジケース_ベンチマークに含まれないセクターの銘柄は除外される(
        self,
    ) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = [
            BenchmarkWeight(sector="Information Technology", weight=0.60),
            BenchmarkWeight(sector="Financials", weight=0.40),
        ]
        ranked = _make_ranked_data(
            sectors={
                "Information Technology": [("AAPL", 0.9), ("MSFT", 0.8)],
                "Financials": [("JPM", 0.85)],
                "Health Care": [("JNJ", 0.88)],  # Not in benchmark
            }
        )

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        tickers = {h.ticker for h in result.holdings}
        assert "JNJ" not in tickers

    def test_正常系_as_of_dateが結果に含まれる(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        assert result.as_of_date == date(2015, 9, 30)

    def test_正常系_holdingsのweight_scoreが0_0から1_0の範囲内(self) -> None:
        builder = PortfolioBuilder(target_size=6)
        benchmark = _make_benchmark_weights()
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        for h in result.holdings:
            assert 0.0 <= h.weight <= 1.0, f"{h.ticker}: weight={h.weight}"
            assert 0.0 <= h.score <= 1.0, f"{h.ticker}: score={h.score}"
