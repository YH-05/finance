#!/usr/bin/env python3
"""Performance benchmark script for Phase 3 quality verification.

This script measures the performance of key operations in the refactored
packages to ensure there is no significant performance regression (>10%).

Main benchmark targets:
1. Technical analysis calculations (SMA, EMA, RSI, MACD, Bollinger Bands)
2. Returns calculation (multi-period returns)
3. Data processing (DataFrame normalization)

Usage:
    uv run python scripts/benchmark_performance.py
    uv run python scripts/benchmark_performance.py --iterations 100
    uv run python scripts/benchmark_performance.py --output results.json

References:
    - Issue: #970 [Phase3] 品質確認: パフォーマンス回帰がないか確認
    - Project: docs/project/package-refactoring.md
"""

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

logger = get_logger(__name__, module="scripts.benchmark")


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""

    name: str
    iterations: int
    mean_ms: float
    std_ms: float
    min_ms: float
    max_ms: float
    median_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": round(self.mean_ms, 4),
            "std_ms": round(self.std_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "max_ms": round(self.max_ms, 4),
            "median_ms": round(self.median_ms, 4),
        }


class PerformanceBenchmark:
    """Performance benchmark runner for finance packages."""

    # Baseline values (reference from before refactoring)
    # These values represent acceptable performance thresholds
    BASELINE_MS: dict[str, float] = {
        "technical_sma": 2.0,
        "technical_ema": 2.0,
        "technical_rsi": 5.0,
        "technical_macd": 5.0,
        "technical_bollinger": 5.0,
        "technical_all": 20.0,
        "returns_single": 1.0,
        "returns_multi": 10.0,
        "dataframe_normalize": 1.0,
    }

    # Tolerance threshold (10% as specified in Issue #970)
    TOLERANCE_PERCENT = 10

    def __init__(
        self,
        iterations: int = 50,
        warmup: int = 5,
        data_size: int = 1000,
    ) -> None:
        """Initialize benchmark runner.

        Parameters
        ----------
        iterations : int
            Number of iterations per benchmark
        warmup : int
            Number of warmup iterations before measurement
        data_size : int
            Size of test data (number of rows)
        """
        self.iterations = iterations
        self.warmup = warmup
        self.data_size = data_size
        self.results: list[BenchmarkResult] = []

        logger.info(
            "Initializing benchmark",
            iterations=iterations,
            warmup=warmup,
            data_size=data_size,
        )

    def _generate_price_data(self) -> pd.Series:
        """Generate synthetic price data for benchmarking.

        Returns
        -------
        pd.Series
            Simulated price series
        """
        np.random.seed(42)  # Reproducibility
        returns = np.random.normal(0.0005, 0.02, self.data_size)
        prices = 100 * np.exp(np.cumsum(returns))
        return pd.Series(prices, name="close")

    def _generate_ohlcv_data(self) -> pd.DataFrame:
        """Generate synthetic OHLCV data for benchmarking.

        Returns
        -------
        pd.DataFrame
            Simulated OHLCV DataFrame
        """
        np.random.seed(42)
        base_prices = self._generate_price_data()

        # Generate OHLCV from close prices
        dates = pd.date_range(end=datetime.now(), periods=self.data_size, freq="D")
        df = pd.DataFrame(
            {
                "open": base_prices
                * (1 + np.random.uniform(-0.01, 0.01, self.data_size)),
                "high": base_prices * (1 + np.random.uniform(0, 0.02, self.data_size)),
                "low": base_prices * (1 - np.random.uniform(0, 0.02, self.data_size)),
                "close": base_prices,
                "volume": np.random.randint(1_000_000, 10_000_000, self.data_size),
            },
            index=dates,
        )
        return df

    def _run_benchmark(
        self,
        name: str,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> BenchmarkResult:
        """Run a single benchmark.

        Parameters
        ----------
        name : str
            Benchmark name
        func : callable
            Function to benchmark
        *args : Any
            Arguments to pass to function
        **kwargs : Any
            Keyword arguments to pass to function

        Returns
        -------
        BenchmarkResult
            Benchmark results
        """
        logger.debug("Running benchmark", name=name)

        # Warmup
        for _ in range(self.warmup):
            func(*args, **kwargs)

        # Timed runs
        times_ms: list[float] = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times_ms.append(elapsed)

        result = BenchmarkResult(
            name=name,
            iterations=self.iterations,
            mean_ms=statistics.mean(times_ms),
            std_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0.0,
            min_ms=min(times_ms),
            max_ms=max(times_ms),
            median_ms=statistics.median(times_ms),
        )

        logger.info(
            "Benchmark completed",
            name=name,
            mean_ms=f"{result.mean_ms:.4f}",
            std_ms=f"{result.std_ms:.4f}",
        )

        self.results.append(result)
        return result

    def benchmark_technical_indicators(self) -> list[BenchmarkResult]:
        """Run technical indicator benchmarks.

        Returns
        -------
        list[BenchmarkResult]
            List of benchmark results
        """
        from analyze.technical import TechnicalIndicators

        prices = self._generate_price_data()
        results: list[BenchmarkResult] = []

        # SMA
        results.append(
            self._run_benchmark(
                "technical_sma",
                TechnicalIndicators.calculate_sma,
                prices,
                20,
            )
        )

        # EMA
        results.append(
            self._run_benchmark(
                "technical_ema",
                TechnicalIndicators.calculate_ema,
                prices,
                20,
            )
        )

        # RSI
        results.append(
            self._run_benchmark(
                "technical_rsi",
                TechnicalIndicators.calculate_rsi,
                prices,
                14,
            )
        )

        # MACD
        results.append(
            self._run_benchmark(
                "technical_macd",
                TechnicalIndicators.calculate_macd,
                prices,
            )
        )

        # Bollinger Bands
        results.append(
            self._run_benchmark(
                "technical_bollinger",
                TechnicalIndicators.calculate_bollinger_bands,
                prices,
                20,
            )
        )

        # Calculate All
        results.append(
            self._run_benchmark(
                "technical_all",
                TechnicalIndicators.calculate_all,
                prices,
            )
        )

        return results

    def benchmark_returns_calculation(self) -> list[BenchmarkResult]:
        """Run returns calculation benchmarks.

        Returns
        -------
        list[BenchmarkResult]
            List of benchmark results
        """
        from analyze.technical import TechnicalIndicators

        prices = self._generate_price_data()
        results: list[BenchmarkResult] = []

        # Single period returns
        results.append(
            self._run_benchmark(
                "returns_single",
                TechnicalIndicators.calculate_returns,
                prices,
                1,
            )
        )

        # Multi-period returns (multiple calculations)
        def calculate_multi_returns(prices: pd.Series) -> dict[str, pd.Series]:
            periods = [1, 5, 10, 20, 60, 120, 252]
            return {
                f"return_{p}d": TechnicalIndicators.calculate_returns(prices, p)
                for p in periods
            }

        results.append(
            self._run_benchmark(
                "returns_multi",
                calculate_multi_returns,
                prices,
            )
        )

        return results

    def benchmark_dataframe_processing(self) -> list[BenchmarkResult]:
        """Run DataFrame processing benchmarks.

        Returns
        -------
        list[BenchmarkResult]
            List of benchmark results
        """
        ohlcv = self._generate_ohlcv_data()
        results: list[BenchmarkResult] = []

        # Simulate DataFrame normalization (similar to YFinanceFetcher._normalize_dataframe)
        def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
            """Simulate DataFrame normalization."""
            normalized = df.copy()
            normalized.columns = normalized.columns.str.lower()

            # Standard column selection
            standard_columns = ["open", "high", "low", "close", "volume"]
            result = normalized[standard_columns]
            assert isinstance(result, pd.DataFrame)  # nosec B101

            # Ensure DatetimeIndex
            if not isinstance(result.index, pd.DatetimeIndex):
                result.index = pd.to_datetime(result.index)

            # Sort by date
            result = result.sort_index()

            return result

        results.append(
            self._run_benchmark(
                "dataframe_normalize",
                normalize_dataframe,
                ohlcv,
            )
        )

        return results

    def run_all(self) -> list[BenchmarkResult]:
        """Run all benchmarks.

        Returns
        -------
        list[BenchmarkResult]
            All benchmark results
        """
        logger.info("Starting all benchmarks")

        all_results: list[BenchmarkResult] = []
        all_results.extend(self.benchmark_technical_indicators())
        all_results.extend(self.benchmark_returns_calculation())
        all_results.extend(self.benchmark_dataframe_processing())

        logger.info(
            "All benchmarks completed",
            total_benchmarks=len(all_results),
        )

        return all_results

    def check_regression(self) -> tuple[bool, list[dict[str, Any]]]:
        """Check for performance regression against baselines.

        Returns
        -------
        tuple[bool, list[dict[str, Any]]]
            (passed, details) - True if all benchmarks pass, False otherwise
        """
        details: list[dict[str, Any]] = []
        all_passed = True

        for result in self.results:
            baseline = self.BASELINE_MS.get(result.name)
            if baseline is None:
                logger.warning(
                    "No baseline for benchmark",
                    name=result.name,
                )
                continue

            # Allow up to TOLERANCE_PERCENT% regression
            threshold = baseline * (1 + self.TOLERANCE_PERCENT / 100)
            passed = result.mean_ms <= threshold
            regression_percent = ((result.mean_ms / baseline) - 1) * 100

            detail = {
                "name": result.name,
                "baseline_ms": baseline,
                "actual_ms": round(result.mean_ms, 4),
                "threshold_ms": round(threshold, 4),
                "regression_percent": round(regression_percent, 2),
                "passed": passed,
            }
            details.append(detail)

            if not passed:
                all_passed = False
                logger.error(
                    "Benchmark failed regression check",
                    name=result.name,
                    baseline_ms=baseline,
                    actual_ms=result.mean_ms,
                    regression_percent=f"{regression_percent:.2f}%",
                )
            else:
                logger.info(
                    "Benchmark passed",
                    name=result.name,
                    regression=f"{regression_percent:+.2f}%",
                )

        return all_passed, details

    def generate_report(self) -> dict[str, Any]:
        """Generate a benchmark report.

        Returns
        -------
        dict[str, Any]
            Complete benchmark report
        """
        passed, regression_details = self.check_regression()

        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "iterations": self.iterations,
                "warmup": self.warmup,
                "data_size": self.data_size,
                "tolerance_percent": self.TOLERANCE_PERCENT,
            },
            "summary": {
                "total_benchmarks": len(self.results),
                "passed": passed,
                "status": "PASSED" if passed else "FAILED",
            },
            "results": [r.to_dict() for r in self.results],
            "regression_check": regression_details,
        }

        return report


def print_report(report: dict[str, Any]) -> None:
    """Print a formatted benchmark report.

    Parameters
    ----------
    report : dict[str, Any]
        The benchmark report to print
    """
    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARK REPORT")
    print("=" * 70)

    print(f"\nTimestamp: {report['timestamp']}")
    print(f"Data Size: {report['config']['data_size']} rows")
    print(f"Iterations: {report['config']['iterations']}")
    print(f"Tolerance: {report['config']['tolerance_percent']}%")

    print("\n" + "-" * 70)
    print("BENCHMARK RESULTS")
    print("-" * 70)

    print(
        f"\n{'Benchmark':<25} {'Mean (ms)':<12} {'Std (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12}"
    )
    print("-" * 70)

    for result in report["results"]:
        print(
            f"{result['name']:<25} "
            f"{result['mean_ms']:<12.4f} "
            f"{result['std_ms']:<12.4f} "
            f"{result['min_ms']:<12.4f} "
            f"{result['max_ms']:<12.4f}"
        )

    print("\n" + "-" * 70)
    print("REGRESSION CHECK")
    print("-" * 70)

    print(
        f"\n{'Benchmark':<25} {'Baseline':<12} {'Actual':<12} {'Threshold':<12} {'Change':<12} {'Status':<10}"
    )
    print("-" * 70)

    for detail in report["regression_check"]:
        status_str = "PASS" if detail["passed"] else "FAIL"
        change_str = f"{detail['regression_percent']:+.2f}%"
        print(
            f"{detail['name']:<25} "
            f"{detail['baseline_ms']:<12.2f} "
            f"{detail['actual_ms']:<12.4f} "
            f"{detail['threshold_ms']:<12.2f} "
            f"{change_str:<12} "
            f"{status_str:<10}"
        )

    print("\n" + "=" * 70)
    summary = report["summary"]
    status = summary["status"]
    status_emoji = "[PASSED]" if summary["passed"] else "[FAILED]"
    print(f"OVERALL STATUS: {status_emoji} {status}")
    print("=" * 70 + "\n")


def main() -> int:
    """Run performance benchmarks.

    Returns
    -------
    int
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Performance benchmark for Phase 3 quality verification"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of iterations per benchmark (default: 50)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Number of warmup iterations (default: 5)",
    )
    parser.add_argument(
        "--data-size",
        type=int,
        default=1000,
        help="Number of data points (default: 1000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for JSON report (optional)",
    )

    args = parser.parse_args()

    # Initialize and run benchmarks
    benchmark = PerformanceBenchmark(
        iterations=args.iterations,
        warmup=args.warmup,
        data_size=args.data_size,
    )

    benchmark.run_all()

    # Generate and print report
    report = benchmark.generate_report()
    print_report(report)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("Report saved", path=str(output_path))
        print(f"Report saved to: {output_path}")

    # Return exit code based on pass/fail
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
