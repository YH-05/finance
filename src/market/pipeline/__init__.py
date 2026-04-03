"""Pipeline package for market data processing.

This package provides the foundational infrastructure for coordinating
multi-phase market data collection pipelines. Public API is defined in
Wave 5.

Submodules
----------
constants
    Database/table name constants and environment variable names.
errors
    Exception hierarchy for pipeline-level error handling.
models
    Frozen dataclass types for pipeline records and phase results.
ticker_normalizer
    Pure function for normalising ticker symbols across data sources.
"""
