"""Database connection interfaces.

This module defines interfaces for database connection providers following
Dependency Inversion Principle (DIP).
"""

from __future__ import annotations

from typing import Any, Protocol


class DatabaseConnectionProvider(Protocol):
    """Protocol for database connection providers.

    Defines the interface for obtaining database connections without
    coupling to specific database implementations.
    """

    def get_connection(self) -> Any:
        """Get a database connection instance."""
        ...
