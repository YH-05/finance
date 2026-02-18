"""Configuration repository for the CA Strategy pipeline.

Loads and caches universe and benchmark configuration from JSON files.
Extracted from Orchestrator to follow Single Responsibility Principle.
"""

from __future__ import annotations

import json
from functools import cached_property
from typing import TYPE_CHECKING

from dev.ca_strategy.types import BenchmarkWeight, UniverseConfig
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


class ConfigRepository:
    """Load and cache CA Strategy configuration.

    Parameters
    ----------
    config_path : Path
        Directory containing ``universe.json`` and
        ``benchmark_weights.json``.

    Raises
    ------
    FileNotFoundError
        If ``config_path`` does not exist.
    """

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        if not self._config_path.exists():
            msg = f"config_path does not exist: {self._config_path}"
            raise FileNotFoundError(msg)

    @cached_property
    def universe(self) -> UniverseConfig:
        """Load and cache universe configuration."""
        universe_path = self._config_path / "universe.json"
        if not universe_path.exists():
            msg = f"universe.json not found: {universe_path}"
            raise FileNotFoundError(msg)

        universe_data = json.loads(universe_path.read_text(encoding="utf-8"))
        universe = UniverseConfig.model_validate({"tickers": universe_data["tickers"]})
        logger.debug("Universe loaded", universe_size=len(universe.tickers))
        return universe

    @cached_property
    def benchmark(self) -> list[BenchmarkWeight]:
        """Load and cache benchmark weights."""
        benchmark_path = self._config_path / "benchmark_weights.json"
        if not benchmark_path.exists():
            msg = f"benchmark_weights.json not found: {benchmark_path}"
            raise FileNotFoundError(msg)

        benchmark_data = json.loads(benchmark_path.read_text(encoding="utf-8"))
        weights_dict: dict[str, float] = benchmark_data["weights"]
        benchmark = [
            BenchmarkWeight(sector=sector, weight=weight)
            for sector, weight in weights_dict.items()
        ]
        logger.debug("Benchmark loaded", sector_count=len(benchmark))
        return benchmark


__all__ = ["ConfigRepository"]
