"""Agent implementations package.

This package contains all agent implementations that implement
the interfaces defined in the parent agents package.

Follows Spring MVC conventions where implementations are in impl/ subfolder.
"""

# Re-export implementations for easier imports
from .llm_factory_impl import LLMFactoryImpl

__all__ = [
    "LLMFactoryImpl",
]