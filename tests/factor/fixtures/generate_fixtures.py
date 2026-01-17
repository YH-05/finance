"""Generate fixture data for regression tests.

This script generates expected value data for regression tests.
Run this script to regenerate fixtures when algorithm changes are intentional.

Usage:
    python tests/factor/fixtures/generate_fixtures.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

FIXTURES_DIR = Path(__file__).parent


def generate_normalizer_fixtures() -> None:
    """Generate expected values for Normalizer regression tests."""
    np.random.seed(42)

    # Input data for normalizer tests
    input_data = pd.Series(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        name="test_data",
    )

    # Z-score expected values (robust=True)
    # Median = 5.5, MAD = (|1-5.5|, |2-5.5|, ...) -> median = 2.5
    # Scale = MAD * 1.4826 = 3.7065
    median = input_data.median()  # 5.5
    mad = (input_data - median).abs().median()  # 2.5
    scale = mad * 1.4826  # 3.7065
    zscore_robust_expected = (input_data - median) / scale

    # Z-score expected values (robust=False)
    mean = input_data.mean()  # 5.5
    std = input_data.std()  # ~3.0276...
    zscore_standard_expected = (input_data - mean) / std

    # Percentile rank expected values
    percentile_rank_expected = input_data.rank(pct=True)

    # Quintile rank expected values (using pd.qcut)
    quintile_expected = pd.qcut(input_data, q=5, labels=False).astype(float) + 1

    # Winsorize expected values (limits=(0.1, 0.1))
    lower_q = input_data.quantile(0.1)
    upper_q = input_data.quantile(0.9)
    winsorize_expected = input_data.clip(lower=lower_q, upper=upper_q)

    # Save to parquet
    fixtures = pd.DataFrame(
        {
            "input_data": input_data,
            "zscore_robust_expected": zscore_robust_expected,
            "zscore_standard_expected": zscore_standard_expected,
            "percentile_rank_expected": percentile_rank_expected,
            "quintile_expected": quintile_expected,
            "winsorize_expected": winsorize_expected,
        }
    )
    fixtures.to_parquet(FIXTURES_DIR / "normalizer_expected.parquet")
    print("Generated: normalizer_expected.parquet")


def generate_orthogonalization_fixtures() -> None:
    """Generate expected values for Orthogonalizer regression tests."""
    np.random.seed(42)

    # Generate synthetic data with known relationship
    n_samples = 50

    # Control factor (X)
    control = pd.Series(np.random.randn(n_samples), name="control")

    # Factor to clean (Y = 0.5*X + noise)
    noise = np.random.randn(n_samples) * 0.5
    factor_to_clean = pd.Series(0.5 * control + noise, name="factor_to_clean")

    # Expected residuals after orthogonalization
    # Using OLS: Y = a + b*X + e -> residuals = Y - (a + b*X)
    import statsmodels.api as sm

    X = sm.add_constant(control)
    model = sm.OLS(factor_to_clean, X).fit()
    residuals_expected = pd.Series(model.resid, name="residuals")
    r_squared_expected = model.rsquared

    # Cascade orthogonalization test data
    # Three factors: f1, f2, f3
    # f2 = 0.3*f1 + noise2
    # f3 = 0.2*f1 + 0.4*f2 + noise3
    f1 = pd.Series(np.random.randn(n_samples), name="f1")
    noise2 = np.random.randn(n_samples) * 0.3
    f2 = pd.Series(0.3 * f1 + noise2, name="f2")
    noise3 = np.random.randn(n_samples) * 0.3
    f3 = pd.Series(0.2 * f1 + 0.4 * f2 + noise3, name="f3")

    # Calculate expected orthogonalized values
    # f1_ortho = f1 (unchanged)
    # f2_ortho = residuals of f2 ~ f1
    X_f2 = sm.add_constant(f1)
    model_f2 = sm.OLS(f2, X_f2).fit()
    f2_ortho = pd.Series(model_f2.resid, name="f2_ortho")

    # f3_ortho = residuals of f3 ~ (f1, f2_ortho)
    X_f3 = sm.add_constant(pd.DataFrame({"f1": f1, "f2_ortho": f2_ortho}))
    model_f3 = sm.OLS(f3, X_f3).fit()
    f3_ortho = pd.Series(model_f3.resid, name="f3_ortho")

    # Save single orthogonalization fixture
    single_fixture = pd.DataFrame(
        {
            "control": control,
            "factor_to_clean": factor_to_clean,
            "residuals_expected": residuals_expected,
        }
    )
    single_fixture.to_parquet(FIXTURES_DIR / "orthogonalization_single_expected.parquet")

    # Save cascade orthogonalization fixture
    cascade_fixture = pd.DataFrame(
        {
            "f1": f1,
            "f2": f2,
            "f3": f3,
            "f1_ortho": f1,
            "f2_ortho": f2_ortho,
            "f3_ortho": f3_ortho,
        }
    )
    cascade_fixture.to_parquet(FIXTURES_DIR / "orthogonalization_cascade_expected.parquet")

    # Save metadata
    metadata = pd.DataFrame(
        {
            "r_squared_single": [r_squared_expected],
        }
    )
    metadata.to_parquet(FIXTURES_DIR / "orthogonalization_metadata.parquet")

    print("Generated: orthogonalization_single_expected.parquet")
    print("Generated: orthogonalization_cascade_expected.parquet")
    print("Generated: orthogonalization_metadata.parquet")


def generate_pca_fixtures() -> None:
    """Generate expected values for YieldCurvePCA regression tests."""
    np.random.seed(42)

    # Generate synthetic yield curve data
    n_samples = 100
    n_maturities = 5

    # Create correlated yield changes (simulating Level, Slope, Curvature)
    # Level: all maturities move together
    level = np.random.randn(n_samples) * 0.1

    # Slope: short end vs long end
    slope = np.random.randn(n_samples) * 0.05

    # Curvature: middle vs ends
    curvature = np.random.randn(n_samples) * 0.02

    # Combine to create yield changes
    # Loadings: Level=[1,1,1,1,1], Slope=[-1,-0.5,0,0.5,1], Curvature=[1,-0.5,-1,-0.5,1]
    level_loadings = np.ones(n_maturities)
    slope_loadings = np.linspace(-1, 1, n_maturities)
    curvature_loadings = np.array([1, -0.5, -1, -0.5, 1])

    yield_changes = np.outer(level, level_loadings)
    yield_changes += np.outer(slope, slope_loadings)
    yield_changes += np.outer(curvature, curvature_loadings)
    yield_changes += np.random.randn(n_samples, n_maturities) * 0.01  # noise

    # Create yield levels by cumsum
    yield_levels = np.cumsum(yield_changes, axis=0) + 2.0  # Start at 2%

    # Column names (maturity labels)
    columns = ["1M", "3M", "6M", "1Y", "2Y"]

    # Create DataFrames
    dates = pd.date_range("2020-01-01", periods=n_samples, freq="D")
    yield_df = pd.DataFrame(yield_levels, index=dates, columns=pd.Index(columns))

    # Perform PCA
    from sklearn.decomposition import PCA

    pca = PCA(n_components=3)
    yield_changes_df = yield_df.diff().dropna()
    scores = pca.fit_transform(yield_changes_df)
    components = pca.components_
    explained_variance_ratio = pca.explained_variance_ratio_

    # Apply sign alignment (Level: sum positive, Slope: last positive, Curvature: mid positive)
    if np.sum(components[0]) < 0:
        components[0] = -components[0]
        scores[:, 0] = -scores[:, 0]

    if components[1, -1] < 0:
        components[1] = -components[1]
        scores[:, 1] = -scores[:, 1]

    mid_idx = len(components[2]) // 2
    if components[2, mid_idx] < 0:
        components[2] = -components[2]
        scores[:, 2] = -scores[:, 2]

    # Save fixtures
    yield_df.to_parquet(FIXTURES_DIR / "pca_input_yields.parquet")

    scores_df = pd.DataFrame(
        scores,
        index=yield_changes_df.index,
        columns=pd.Index(["Level", "Slope", "Curvature"]),
    )
    scores_df.to_parquet(FIXTURES_DIR / "pca_scores_expected.parquet")

    components_df = pd.DataFrame(
        components,
        index=pd.Index(["Level", "Slope", "Curvature"]),
        columns=pd.Index(columns),
    )
    components_df.to_parquet(FIXTURES_DIR / "pca_components_expected.parquet")

    variance_df = pd.DataFrame(
        {
            "explained_variance_ratio": explained_variance_ratio,
        },
        index=pd.Index(["Level", "Slope", "Curvature"]),
    )
    variance_df.to_parquet(FIXTURES_DIR / "pca_variance_expected.parquet")

    print("Generated: pca_input_yields.parquet")
    print("Generated: pca_scores_expected.parquet")
    print("Generated: pca_components_expected.parquet")
    print("Generated: pca_variance_expected.parquet")


if __name__ == "__main__":
    print("Generating regression test fixtures...")
    generate_normalizer_fixtures()
    generate_orthogonalization_fixtures()
    generate_pca_fixtures()
    print("Done!")
