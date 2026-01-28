"""Processors for AI processing of news articles.

This module provides AI processor implementations for summarization,
classification, tagging, and other AI-powered processing of news articles.
It also provides the Pipeline class for orchestrating Source -> Processor -> Sink
chain execution.
"""

from .agent_base import AgentProcessor, AgentProcessorError, SDKNotInstalledError
from .classifier import ClassifierProcessor
from .pipeline import (
    Pipeline,
    PipelineConfig,
    PipelineError,
    PipelineResult,
    StageError,
)
from .summarizer import SummarizerProcessor

__all__ = [
    "AgentProcessor",
    "AgentProcessorError",
    "ClassifierProcessor",
    "Pipeline",
    "PipelineConfig",
    "PipelineError",
    "PipelineResult",
    "SDKNotInstalledError",
    "StageError",
    "SummarizerProcessor",
]
