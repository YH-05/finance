"""Company configuration modules for the AI investment value chain.

Each submodule defines CompanyConfig instances for a category of companies
in the AI value chain. All configurations are accessible via the
category-specific lists (e.g., AI_LLM_COMPANIES) and the combined
ALL_COMPANIES list.
"""

from .ai_infra import AI_INFRA_COMPANIES
from .ai_llm import AI_LLM_COMPANIES
from .data_center import DATA_CENTER_COMPANIES
from .gpu_chips import GPU_CHIPS_COMPANIES
from .networking import NETWORKING_COMPANIES
from .nuclear_fusion import NUCLEAR_FUSION_COMPANIES
from .physical_ai import PHYSICAL_AI_COMPANIES
from .power_energy import POWER_ENERGY_COMPANIES
from .saas import SAAS_COMPANIES
from .semiconductor import SEMICONDUCTOR_COMPANIES

__all__ = [
    "AI_INFRA_COMPANIES",
    "AI_LLM_COMPANIES",
    "DATA_CENTER_COMPANIES",
    "GPU_CHIPS_COMPANIES",
    "NETWORKING_COMPANIES",
    "NUCLEAR_FUSION_COMPANIES",
    "PHYSICAL_AI_COMPANIES",
    "POWER_ENERGY_COMPANIES",
    "SAAS_COMPANIES",
    "SEMICONDUCTOR_COMPANIES",
]
