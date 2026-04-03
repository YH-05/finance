"""Pipeline package for market data processing.

This package provides the foundational infrastructure for coordinating
multi-phase market data collection pipelines.

Public API (Wave 5)
-------------------
- ``EarningsPipeline`` -- 4-phase earnings data collection orchestrator
- ``PhaseResult`` -- Per-phase execution summary (frozen dataclass)
- ``PipelineResult`` -- Full pipeline run summary (frozen dataclass)
- ``PipelineError`` -- Base exception for all pipeline errors
- ``CollectionQueue`` -- SQLite-backed task queue for NASDAQ earnings data

Submodules
----------
constants
    Database/table name constants and environment variable names.
errors
    Exception hierarchy for pipeline-level error handling.
models
    Frozen dataclass types for pipeline records and phase results.
pipeline
    ``EarningsPipeline`` orchestrator.
cli
    argparse-based CLI (``main()``).
queue
    ``CollectionQueue`` SQLite queue.
ticker_normalizer
    Pure function for normalising ticker symbols across data sources.
"""

from market.pipeline.errors import PipelineError
from market.pipeline.models import PhaseResult, PipelineResult
from market.pipeline.pipeline import EarningsPipeline
from market.pipeline.queue import CollectionQueue

__all__ = [
    "CollectionQueue",
    "EarningsPipeline",
    "PhaseResult",
    "PipelineError",
    "PipelineResult",
]
