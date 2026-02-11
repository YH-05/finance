"""Company configuration modules for the AI investment value chain.

Each submodule defines CompanyConfig instances for a category of companies
in the AI value chain. All configurations are accessible via the
category-specific lists (e.g., AI_LLM_COMPANIES) and the combined
ALL_COMPANIES list.
"""

from .ai_llm import AI_LLM_COMPANIES

__all__ = [
    "AI_LLM_COMPANIES",
]
