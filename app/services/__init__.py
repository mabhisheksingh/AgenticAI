"""Services package following Spring MVC conventions.

This package contains:
- Service interfaces (in main package)
- Service implementations (in impl/ subfolder)

Follows Spring MVC pattern where interfaces are in the main package
and implementations are in impl/ subfolder.
"""

# Import and re-export interfaces
from .agent_service_interface import (
    AgentServiceInterface,
    AgentExecutionInterface,
    ConversationStateInterface,
)
from .user_service_interface import UserServiceInterface

__all__ = [
    "AgentServiceInterface",
    "AgentExecutionInterface",
    "ConversationStateInterface", 
    "UserServiceInterface",
]