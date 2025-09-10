"""Repository implementations package.

This package contains all repository implementations that implement
the interfaces defined in the parent repositories package.

Follows Spring MVC conventions where implementations are in impl/ subfolder.
"""

# Re-export implementations for easier imports
from .thread_repository_impl import ThreadRepositoryImpl

__all__ = [
    "ThreadRepositoryImpl",
]
