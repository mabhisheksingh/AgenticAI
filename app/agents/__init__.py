"""Agents package following Spring MVC conventions.

This package contains:
- Agent interfaces (in main package)
- Agent implementations (in impl/ subfolder)

Follows Spring MVC pattern where interfaces are in the main package
and implementations are in impl/ subfolder.
"""

# Import and re-export interfaces
from .llm_provider_interface import LLMProviderInterface

__all__ = [
    "LLMProviderInterface",
]
