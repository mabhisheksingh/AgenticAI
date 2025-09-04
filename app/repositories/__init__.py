"""Repositories package following Spring MVC conventions.

This package contains:
- Repository interfaces (in main package) 
- Repository implementations (in impl/ subfolder)

Follows Spring MVC pattern where interfaces are in the main package
and implementations are in impl/ subfolder.
"""

# Import and re-export interfaces
from .thread_repository_interface import (
    ThreadRepositoryInterface,
    UserRepositoryInterface,
    ThreadQueryInterface,
)
from .database_interface import DatabaseConnectionProvider

__all__ = [
    "ThreadRepositoryInterface",
    "UserRepositoryInterface",
    "ThreadQueryInterface",
    "DatabaseConnectionProvider",
]