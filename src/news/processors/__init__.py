"""Processors for AI processing of news articles.

This module provides AI processor implementations for summarization,
classification, tagging, and other AI-powered processing of news articles.
"""

from .agent_base import AgentProcessor, AgentProcessorError, SDKNotInstalledError
from .summarizer import SummarizerProcessor

__all__ = [
    "AgentProcessor",
    "AgentProcessorError",
    "SDKNotInstalledError",
    "SummarizerProcessor",
]
