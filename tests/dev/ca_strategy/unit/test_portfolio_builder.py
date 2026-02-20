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

    def test_エッジケース_aggregate_scoreが全て0の場合均等配分される(self) -> None:
        """全銘柄の aggregate_score=0 のとき均等配分分岐が正しく動作することを確認。"""
        builder = PortfolioBuilder(target_size=2)
        benchmark = [BenchmarkWeight(sector="Information Technology", weight=1.0)]
        ranked = [
            RankedStock(
                ticker="AAPL",
                aggregate_score=0.0,
                gics_sector="Information Technology",
                sector_rank=1,
                claim_count=0,
                structural_weight=0.0,
            ),
            RankedStock(
                ticker="MSFT",
                aggregate_score=0.0,
                gics_sector="Information Technology",
                sector_rank=2,
                claim_count=0,
                structural_weight=0.0,
            ),
        ]

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        assert len(result.holdings) == 2
        total_weight = sum(h.weight for h in result.holdings)
        assert total_weight == pytest.approx(1.0, abs=1e-9)
        # Both holdings should have equal weight when all scores are 0
        weights = [h.weight for h in result.holdings]
        assert weights[0] == pytest.approx(weights[1], abs=1e-9)


# ===========================================================================
# TestEqualWeightPortfolio
# ===========================================================================
class TestEqualWeightPortfolio:
    """build_equal_weight() メソッドのテスト。

    閾値ベースの等ウェイトポートフォリオ構築機能を検証する。
    - threshold を超える銘柄が均等ウェイトで選択される
    - 全ウェイト合計が 1.0 になる
    - SectorAllocation が選択銘柄の実績ベースで計算される
    - 空結果・境界値ケースを正しくハンドリングする
    """

    # -----------------------------------------------------------------------
    # Helper
    # -----------------------------------------------------------------------
    def _make_ranked(
        self,
        stocks: list[tuple[str, float, str]] | None = None,
    ) -> list[RankedStock]:
        """Create a list of RankedStock entries.

        Parameters
        ----------
        stocks : list of (ticker, aggregate_score, gics_sector)
        """
        if stocks is None:
            stocks = [
                ("AAPL", 0.9, "Information Technology"),
                ("MSFT", 0.8, "Information Technology"),
                ("JPM", 0.7, "Financials"),
                ("GS", 0.6, "Financials"),
                ("JNJ", 0.4, "Health Care"),
            ]
        return [
            RankedStock(
                ticker=ticker,
                aggregate_score=score,
                gics_sector=sector,
                sector_rank=1,
                claim_count=3,
                structural_weight=0.5,
            )
            for ticker, score, sector in stocks
        ]

    # -----------------------------------------------------------------------
    # 正常系: 基本動作
    # -----------------------------------------------------------------------
    def test_正常系_閾値0_5で複数銘柄が選択されPortfolioResultが返る(self) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked()

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        assert isinstance(result, PortfolioResult)
        # AAPL(0.9), MSFT(0.8), JPM(0.7), GS(0.6) pass threshold 0.5
        assert len(result.holdings) == 4

    def test_正常系_選択銘柄に均等ウェイトが設定される(self) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked()

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        # 4 stocks pass threshold; each should get 1/4 = 0.25
        expected_weight = 1.0 / 4
        for h in result.holdings:
            assert h.weight == pytest.approx(expected_weight, abs=1e-9)

    def test_正常系_全ウェイト合計が1_0になる(self) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked()

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        total_weight = sum(h.weight for h in result.holdings)
        assert total_weight == pytest.approx(1.0, abs=1e-9)

    def test_正常系_holdingsがPortfolioHolding型で返される(self) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked()

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        for h in result.holdings:
            assert isinstance(h, PortfolioHolding)

    def test_正常系_SectorAllocationが選択銘柄の実績ベースで計算される(self) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked()

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        # Verify sector_allocations are computed from selected holdings
        assert isinstance(result.sector_allocations, list)
        assert len(result.sector_allocations) > 0
        for sa in result.sector_allocations:
            assert isinstance(sa, SectorAllocation)

        # Total actual_weight across sectors should sum to 1.0
        total_actual = sum(sa.actual_weight for sa in result.sector_allocations)
        assert total_actual == pytest.approx(1.0, abs=1e-9)

    def test_正常系_SectorAllocationのstock_countが正しい(self) -> None:
        """IT: AAPL+MSFT=2株, Financials: JPM+GS=2株 が通過する（閾値0.5）。"""
        builder = PortfolioBuilder()
        ranked = self._make_ranked()

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        sector_counts = {sa.sector: sa.stock_count for sa in result.sector_allocations}
        assert sector_counts.get("Information Technology") == 2
        assert sector_counts.get("Financials") == 2

    def test_正常系_as_of_dateが結果に含まれる(self) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked()

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        assert result.as_of_date == date(2015, 9, 30)

    # -----------------------------------------------------------------------
    # 正常系: 単一銘柄
    # -----------------------------------------------------------------------
    def test_正常系_1銘柄が通過するとウェイトが1_0になる(self) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked(stocks=[("AAPL", 0.9, "Information Technology")])

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        assert len(result.holdings) == 1
        assert result.holdings[0].weight == pytest.approx(1.0, abs=1e-9)

    # -----------------------------------------------------------------------
    # エッジケース: 空結果
    # -----------------------------------------------------------------------
    def test_エッジケース_閾値が全銘柄スコアを超える場合に空のPortfolioResultが返る(
        self,
    ) -> None:
        builder = PortfolioBuilder()
        ranked = self._make_ranked()  # max score = 0.9

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.95,  # No stock exceeds this
            as_of_date=date(2015, 9, 30),
        )

        assert isinstance(result, PortfolioResult)
        assert result.holdings == []
        assert result.sector_allocations == []

    def test_エッジケース_空のランキングデータで空PortfolioResultが返る(self) -> None:
        builder = PortfolioBuilder()

        result = builder.build_equal_weight(
            ranked=[],
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        assert isinstance(result, PortfolioResult)
        assert result.holdings == []
        assert result.sector_allocations == []

    # -----------------------------------------------------------------------
    # エッジケース: 境界値（> threshold、= は除外）
    # -----------------------------------------------------------------------
    def test_エッジケース_閾値ちょうどのスコアは除外される(self) -> None:
        """aggregate_score == threshold の銘柄は除外される（> ではなく = は不可）。"""
        builder = PortfolioBuilder()
        ranked = self._make_ranked(
            stocks=[
                ("AAPL", 0.7, "Information Technology"),  # > 0.5, included
                ("MSFT", 0.5, "Information Technology"),  # == 0.5, excluded
                ("JPM", 0.3, "Financials"),  # < 0.5, excluded
            ]
        )

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        tickers = {h.ticker for h in result.holdings}
        assert "AAPL" in tickers
        assert "MSFT" not in tickers
        assert "JPM" not in tickers

    def test_エッジケース_閾値より僅かに上のスコアは含まれる(self) -> None:
        """aggregate_score が threshold より僅かに大きい銘柄は選択される。"""
        builder = PortfolioBuilder()
        ranked = self._make_ranked(
            stocks=[
                ("AAPL", 0.5001, "Information Technology"),  # Just above 0.5
                ("MSFT", 0.5, "Information Technology"),  # Exactly 0.5, excluded
            ]
        )

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=0.5,
            as_of_date=date(2015, 9, 30),
        )

        tickers = {h.ticker for h in result.holdings}
        assert "AAPL" in tickers
        assert "MSFT" not in tickers
        assert len(result.holdings) == 1

    # -----------------------------------------------------------------------
    # パラメトライズ: 複数閾値でのウェイト合計検証
    # -----------------------------------------------------------------------
    @pytest.mark.parametrize("threshold", [0.3, 0.5, 0.7])
    def test_パラメトライズ_複数閾値でウェイト合計が1_0になる(
        self, threshold: float
    ) -> None:
        """閾値 0.3, 0.5, 0.7 の各ケースで全ウェイト合計が 1.0 であることを検証。"""
        builder = PortfolioBuilder()
        ranked = self._make_ranked(
            stocks=[
                ("AAPL", 0.9, "Information Technology"),
                ("MSFT", 0.8, "Information Technology"),
                ("JPM", 0.6, "Financials"),
                ("GS", 0.5, "Financials"),
                ("JNJ", 0.4, "Health Care"),
                ("PFE", 0.2, "Health Care"),
            ]
        )

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=threshold,
            as_of_date=date(2015, 9, 30),
        )

        if result.holdings:
            total_weight = sum(h.weight for h in result.holdings)
            assert total_weight == pytest.approx(1.0, abs=1e-9), (
                f"threshold={threshold}: total_weight={total_weight}"
            )

    @pytest.mark.parametrize("threshold", [0.3, 0.5, 0.7])
    def test_パラメトライズ_複数閾値でholdingsにPortfolioHolding型が使われる(
        self, threshold: float
    ) -> None:
        """各閾値で holdings の型が正しいことを確認。"""
        builder = PortfolioBuilder()
        ranked = self._make_ranked(
            stocks=[
                ("AAPL", 0.9, "Information Technology"),
                ("MSFT", 0.8, "Information Technology"),
                ("JPM", 0.6, "Financials"),
                ("GS", 0.5, "Financials"),
                ("JNJ", 0.4, "Health Care"),
            ]
        )

        result = builder.build_equal_weight(
            ranked=ranked,
            threshold=threshold,
            as_of_date=date(2015, 9, 30),
        )

        for h in result.holdings:
            assert isinstance(h, PortfolioHolding)

    # -----------------------------------------------------------------------
    # 回帰確認: 既存 build() メソッドへの影響なし
    # -----------------------------------------------------------------------
    def test_回帰_build_equal_weight追加後もbuildメソッドが正常動作する(self) -> None:
        """build_equal_weight の追加が既存 build() メソッドに影響しないことを確認。"""
        builder = PortfolioBuilder(target_size=6)
        benchmark = [
            BenchmarkWeight(sector="Information Technology", weight=0.40),
            BenchmarkWeight(sector="Financials", weight=0.30),
            BenchmarkWeight(sector="Health Care", weight=0.30),
        ]
        ranked = _make_ranked_data()

        result = builder.build(
            ranked=ranked,
            benchmark=benchmark,
            as_of_date=date(2015, 9, 30),
        )

        assert isinstance(result, PortfolioResult)
        assert len(result.holdings) > 0
        total_weight = sum(h.weight for h in result.holdings)
        assert total_weight == pytest.approx(1.0, abs=1e-9)
