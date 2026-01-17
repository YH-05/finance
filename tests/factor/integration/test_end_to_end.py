"""End-to-end integration tests for factor package.

This module tests complete workflows that combine macro factors
and ROIC factors, simulating real-world usage patterns.
"""

import numpy as np
import pandas as pd
import pytest

from factor.core.normalizer import Normalizer
from factor.core.orthogonalization import Orthogonalizer
from factor.core.pca import YieldCurvePCA
from factor.factors.macro.flight_to_quality import HY_SPREAD_SERIES, IG_SPREAD_SERIES
from factor.factors.macro.inflation import INFLATION_SERIES
from factor.factors.macro.macro_builder import MacroFactorBuilder
from factor.factors.quality.roic import ROICFactor
from factor.factors.quality.roic_label import ROICTransitionLabeler


class TestEndToEndWorkflows:
    """End-to-end tests combining multiple factor components."""

    @pytest.fixture
    def realistic_market_data(self) -> dict[str, pd.DataFrame | pd.Series]:
        """Create realistic market data for end-to-end testing."""
        np.random.seed(42)
        n_samples = 200  # Approximately 1 year of daily data
        dates = pd.date_range("2020-01-01", periods=n_samples, freq="D")

        # Treasury yields with realistic dynamics
        base_yields = {
            "DGS1MO": 0.50,
            "DGS3MO": 0.70,
            "DGS6MO": 0.90,
            "DGS1": 1.20,
            "DGS2": 1.50,
            "DGS3": 1.80,
            "DGS5": 2.20,
            "DGS7": 2.50,
            "DGS10": 2.80,
            "DGS20": 3.20,
            "DGS30": 3.50,
        }

        yields_data = {}
        for series_id, base_yield in base_yields.items():
            # Autoregressive process for realistic yield dynamics
            changes = np.zeros(n_samples)
            for i in range(1, n_samples):
                changes[i] = 0.8 * changes[i - 1] + np.random.randn() * 0.02
            yields_data[series_id] = base_yield + np.cumsum(changes)

        yields_df = pd.DataFrame(yields_data, index=dates)

        # Credit spreads
        hy_spread = 4.5 + np.cumsum(np.random.randn(n_samples) * 0.05)
        ig_spread = 1.0 + np.cumsum(np.random.randn(n_samples) * 0.02)
        spreads_df = pd.DataFrame(
            {
                HY_SPREAD_SERIES: hy_spread,
                IG_SPREAD_SERIES: ig_spread,
            },
            index=dates,
        )

        # Inflation expectations
        inflation = 2.2 + np.cumsum(np.random.randn(n_samples) * 0.01)
        inflation_df = pd.DataFrame(
            {
                INFLATION_SERIES: inflation,
            },
            index=dates,
        )

        # Market returns
        market_return = pd.Series(
            np.random.randn(n_samples) * 0.01,
            index=dates,
            name="market_return",
        )

        # Risk-free rate
        risk_free = pd.Series(
            yields_df["DGS1MO"].to_numpy() / 100 / 252,  # Daily rate
            index=dates,
            name="risk_free",
        )

        return {
            "yields": yields_df,
            "spreads": spreads_df,
            "inflation": inflation_df,
            "market_return": market_return,
            "risk_free": risk_free,
        }

    @pytest.fixture
    def realistic_roic_data(self) -> pd.DataFrame:
        """Create realistic ROIC data for end-to-end testing."""
        np.random.seed(42)

        n_stocks = 50
        n_quarters = 12  # 3 years of quarterly data
        tickers = [f"STOCK{i:03d}" for i in range(1, n_stocks + 1)]
        dates = pd.date_range("2020-01-01", periods=n_quarters, freq="QE")

        data = []

        # Assign each stock a base ROIC and persistence factor
        base_roics = np.random.uniform(0.05, 0.25, n_stocks)
        persistences = np.random.uniform(0.7, 0.95, n_stocks)

        for i, ticker in enumerate(tickers):
            current_roic = base_roics[i]
            for date in dates:
                noise = np.random.randn() * 0.02
                current_roic = (
                    persistences[i] * current_roic
                    + (1 - persistences[i]) * base_roics[i]
                    + noise
                )
                current_roic = max(0.01, min(0.40, current_roic))  # Bound ROIC

                data.append(
                    {
                        "date": date,
                        "ticker": ticker,
                        "ROIC": current_roic,
                    }
                )

        return pd.DataFrame(data)

    def test_正常系_マクロファクターとROICファクターの両方を使用した完全なワークフロー(
        self,
        realistic_market_data: dict[str, pd.DataFrame | pd.Series],
        realistic_roic_data: pd.DataFrame,
    ) -> None:
        """マクロファクターとROICファクターを組み合わせた完全なワークフローが正常に動作することを確認。"""
        # Step 1: Build macro factors
        macro_builder = MacroFactorBuilder(pca_components=3, min_samples=20)
        macro_factors = macro_builder.build_all_factors(realistic_market_data)

        # Verify macro factors
        assert len(macro_factors.columns) == 6
        assert macro_factors.notna().any().all()

        # Step 2: Calculate ROIC ranks
        roic_factor = ROICFactor(min_samples=10)
        roic_ranked = roic_factor.calculate_ranks(
            realistic_roic_data,
            roic_column="ROIC",
            date_column="date",
        )

        # Verify ROIC ranks
        assert "ROIC_Rank" in roic_ranked.columns

        # Step 3: Add shifted ROIC values
        roic_shifted = roic_factor.add_shifted_values(
            roic_ranked,
            roic_column="ROIC_Rank",
            ticker_column="ticker",
            date_column="date",
            past_periods=[1, 2, 4],
            future_periods=[1, 2, 4],
            freq_suffix="Q",
        )

        # Verify shifted columns
        assert "ROIC_Rank_1QAgo" in roic_shifted.columns
        assert "ROIC_Rank_4QForward" in roic_shifted.columns

        # Step 4: Label ROIC transitions
        labeler = ROICTransitionLabeler()
        roic_labeled = labeler.label_dataframe(
            roic_shifted,
            rank_columns=["ROIC_Rank", "ROIC_Rank_1QForward", "ROIC_Rank_4QForward"],
            label_column="ROIC_Label",
        )

        # Verify labels
        assert "ROIC_Label" in roic_labeled.columns

        # Step 5: Analyze distribution of labels
        label_counts = roic_labeled["ROIC_Label"].value_counts(dropna=True)
        assert len(label_counts) > 0

        # Overall verification
        assert len(macro_factors) > 0
        assert len(roic_labeled) == len(realistic_roic_data)

    def test_正常系_実際のデータフォーマットに近いテスト(
        self,
        realistic_market_data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """実際のデータフォーマットと処理パターンをシミュレートしたテスト。"""
        # Simulate typical data preprocessing steps
        yields = realistic_market_data["yields"]
        spreads = realistic_market_data["spreads"]
        inflation = realistic_market_data["inflation"]

        # Step 1: Handle missing data (forward fill)
        yields_clean = yields.ffill().dropna()
        spreads_clean = spreads.ffill().dropna()
        inflation_clean = inflation.ffill().dropna()

        # Step 2: Align all data to common dates
        common_dates = yields_clean.index.intersection(spreads_clean.index)
        common_dates = common_dates.intersection(inflation_clean.index)

        yields_aligned = yields_clean.loc[common_dates]
        spreads_aligned = spreads_clean.loc[common_dates]
        inflation_aligned = inflation_clean.loc[common_dates]

        # Step 3: Create market factor data
        market_return = pd.Series(
            np.random.randn(len(common_dates)) * 0.01,
            index=common_dates,
        )
        risk_free = pd.Series(
            yields_aligned["DGS1MO"].values / 100 / 252,
            index=common_dates,
        )

        # Step 4: Build macro factors
        aligned_data = {
            "yields": yields_aligned,
            "spreads": spreads_aligned,
            "inflation": inflation_aligned,
            "market_return": market_return,
            "risk_free": risk_free,
        }

        builder = MacroFactorBuilder(min_samples=20)
        factors = builder.build_all_factors(aligned_data)

        # Verify output format
        assert isinstance(factors, pd.DataFrame)
        assert isinstance(factors.index, pd.DatetimeIndex)
        assert len(factors.columns) == 6

        # All factors should be numeric
        for col in factors.columns:
            dtype = factors[col].dtype
            assert np.issubdtype(dtype, np.floating)  # type: ignore[arg-type]

    def test_正常系_正規化直交化PCAの統合ワークフロー(
        self,
        realistic_market_data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """Normalizer, Orthogonalizer, PCA を統合したワークフローのテスト。"""
        yields = realistic_market_data["yields"]

        # Step 1: PCA on yield curve
        pca = YieldCurvePCA(n_components=3)
        yields_df = yields if isinstance(yields, pd.DataFrame) else pd.DataFrame(yields)
        pca_result = pca.fit_transform(yields_df, use_changes=True, align_signs=True)

        # Verify PCA output
        assert pca_result.scores.shape[1] == 3
        assert len(pca_result.column_names) == 3
        # Note: With random data, explained variance may be lower
        # For real yield curve data, it would typically be > 0.9
        assert pca_result.explained_variance_ratio.sum() > 0.3

        # Step 2: Normalize PCA scores
        normalizer = Normalizer(min_samples=10)
        normalized_scores = normalizer.zscore(pca_result.scores, robust=True)

        # Verify normalization
        for col in normalized_scores.columns:
            col_data = normalized_scores[col].dropna()
            if len(col_data) > 0:
                # Should be roughly centered (median close to 0 for robust zscore)
                assert abs(col_data.median()) < 0.5

        # Step 3: Orthogonalize factors sequentially
        orthogonalizer = Orthogonalizer(min_samples=20)

        # Orthogonalize Slope against Level
        slope_series = pd.Series(normalized_scores["Slope"])
        level_series = pd.Series(normalized_scores["Level"])
        ortho_result = orthogonalizer.orthogonalize(
            slope_series,
            level_series,
        )

        # Verify orthogonalization
        assert ortho_result.r_squared >= 0
        assert ortho_result.r_squared <= 1

        # Step 4: Cascade orthogonalization
        factors_dict: dict[str, pd.Series] = {
            "Level": pd.Series(normalized_scores["Level"]),
            "Slope": pd.Series(normalized_scores["Slope"]),
            "Curvature": pd.Series(normalized_scores["Curvature"]),
        }

        cascade_result = orthogonalizer.orthogonalize_cascade(
            factors_dict,
            order=["Level", "Slope", "Curvature"],
        )

        # Verify cascade result
        assert len(cascade_result) == 3
        assert "Level" in cascade_result
        assert cascade_result["Level"].r_squared == 0.0  # First factor unchanged

    def test_正常系_グループ別正規化とROIC分析の統合(
        self,
        realistic_roic_data: pd.DataFrame,
    ) -> None:
        """グループ別正規化とROIC分析を統合したワークフローのテスト。"""
        # Step 1: Add sector information
        np.random.seed(42)
        sectors = ["Tech", "Finance", "Healthcare", "Consumer", "Industrial"]
        realistic_roic_data = realistic_roic_data.copy()
        realistic_roic_data["sector"] = [
            sectors[hash(t) % len(sectors)] for t in realistic_roic_data["ticker"]
        ]

        # Step 2: Calculate ROIC ranks
        roic_factor = ROICFactor(min_samples=5)
        ranked_data = roic_factor.calculate_ranks(
            realistic_roic_data,
            roic_column="ROIC",
            date_column="date",
        )

        # Step 3: Sector-neutral normalization of ROIC
        normalizer = Normalizer(min_samples=3)
        normalized_data = normalizer.normalize_by_group(
            ranked_data,
            value_column="ROIC",
            group_columns=["date", "sector"],
            method="zscore",
            robust=True,
        )

        # Verify normalization column exists
        assert "ROIC_zscore" in normalized_data.columns

        # Step 4: Calculate percentile ranks within sectors
        percentile_data = normalizer.normalize_by_group(
            ranked_data,
            value_column="ROIC",
            group_columns=["date", "sector"],
            method="percentile_rank",
        )

        assert "ROIC_percentile_rank" in percentile_data.columns

        # Step 5: Add shifted values and label
        shifted_data = roic_factor.add_shifted_values(
            ranked_data,
            roic_column="ROIC_Rank",
            ticker_column="ticker",
            date_column="date",
            future_periods=[1, 2],
            freq_suffix="Q",
        )

        labeler = ROICTransitionLabeler()
        labeled_data = labeler.label_dataframe(
            shifted_data,
            rank_columns=["ROIC_Rank", "ROIC_Rank_1QForward", "ROIC_Rank_2QForward"],
        )

        # Step 6: Analyze by sector
        sector_label_dist = labeled_data.groupby("sector")["ROIC_Label"].value_counts(
            normalize=True
        )

        # Verify we have sector-level analysis
        assert len(sector_label_dist) > 0


class TestEndToEndDataQuality:
    """Data quality tests for end-to-end workflows."""

    def test_エッジケース_欠損値が多いデータでの処理(self) -> None:
        """欠損値が多いデータでも処理が継続することを確認。"""
        np.random.seed(42)
        n_samples = 100
        dates = pd.date_range("2020-01-01", periods=n_samples, freq="D")

        # Create data with many NaN values
        yields_data = {}
        base_yields = {
            "DGS1MO": 0.5,
            "DGS3MO": 0.7,
            "DGS1": 1.0,
            "DGS2": 1.5,
            "DGS10": 2.5,
        }

        for series_id, base_yield in base_yields.items():
            values = base_yield + np.cumsum(np.random.randn(n_samples) * 0.01)
            # Add 20% NaN values
            nan_indices = np.random.choice(
                n_samples, size=int(n_samples * 0.2), replace=False
            )
            values[nan_indices] = np.nan
            yields_data[series_id] = values

        yields_df = pd.DataFrame(yields_data, index=dates)

        # PCA should handle missing data gracefully
        pca = YieldCurvePCA(n_components=3)

        # Should work after handling NaN
        clean_yields = yields_df.ffill().dropna()

        if len(clean_yields) >= 3:
            result = pca.fit_transform(clean_yields, use_changes=True)
            assert result.scores is not None
            assert len(result.scores) > 0

    def test_エッジケース_極端な値を含むデータでの処理(self) -> None:
        """極端な外れ値を含むデータでも処理が継続することを確認。"""
        np.random.seed(42)

        # Create data with outliers
        normal_data = pd.Series(np.random.randn(100))
        # Add extreme outliers
        normal_data.iloc[10] = 100  # Extreme positive
        normal_data.iloc[50] = -100  # Extreme negative

        normalizer = Normalizer(min_samples=5)

        # Robust zscore should handle outliers
        robust_zscore = normalizer.zscore(normal_data, robust=True)

        # Outliers should have large absolute values but not infinite
        assert np.isfinite(robust_zscore).all()

        # Winsorization should clip outliers
        winsorized = normalizer.winsorize(normal_data, limits=(0.05, 0.05))

        # Should be bounded
        assert winsorized.max() < 100
        assert winsorized.min() > -100

    def test_エッジケース_小規模データセットでの処理(self) -> None:
        """小規模データセットでも処理が動作することを確認。"""
        # Minimum viable data for ROIC pipeline
        _small_data = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=4, freq="QE"),
                "ticker": ["A", "B", "A", "B"],
                "ROIC": [0.10, 0.20, 0.15, 0.25],
            }
        )

        # Make data large enough for processing
        expanded_data = pd.DataFrame(
            {
                "date": ["2020-01-01"] * 10,
                "ticker": [f"T{i}" for i in range(10)],
                "ROIC": np.linspace(0.05, 0.30, 10),
            }
        )

        roic_factor = ROICFactor(min_samples=5)
        result = roic_factor.calculate_ranks(
            expanded_data,
            roic_column="ROIC",
            date_column="date",
        )

        assert "ROIC_Rank" in result.columns
        assert bool(result["ROIC_Rank"].notna().any())

    def test_正常系_日付型の互換性確認(self) -> None:
        """異なる日付型でも処理が正常に動作することを確認。"""
        dates_types = [
            pd.date_range("2020-01-01", periods=10, freq="QE"),  # DatetimeIndex
            pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-04-01",
                    "2020-07-01",
                    "2020-10-01",
                    "2021-01-01",
                    "2021-04-01",
                    "2021-07-01",
                    "2021-10-01",
                    "2022-01-01",
                    "2022-04-01",
                ]
            ),  # DatetimeIndex from strings
        ]

        for dates in dates_types:
            data = pd.DataFrame(
                {
                    "date": dates,
                    "ticker": [f"T{i % 5}" for i in range(len(dates))],
                    "ROIC": np.linspace(0.05, 0.30, len(dates)),
                }
            )

            roic_factor = ROICFactor(min_samples=2)
            result = roic_factor.calculate_ranks(
                data,
                roic_column="ROIC",
                date_column="date",
            )

            assert "ROIC_Rank" in result.columns
