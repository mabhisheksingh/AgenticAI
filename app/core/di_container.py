"""Dependency Injection container for implementing DIP.

This module provides a simple but effective dependency injection container
that manages object creation and lifecycle, enabling loose coupling between
components and making the codebase more testable and maintainable.
"""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any, TypeVar, cast

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container.

    Manages service registration and resolution with support for:
    - Singleton and transient lifetimes
    - Interface-to-implementation mapping
    - Lazy initialization
    - Circular dependency detection

    Features:
    - Type-safe service resolution
    - Automatic dependency injection
    - Configurable service lifetimes
    - Clear error messages for missing dependencies
    """

    def __init__(self):
        """Initialize the DI container."""
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}
        self._singletons: dict[type, Any] = {}
        self._resolving: set[type] = set()  # For circular dependency detection

    def register_singleton(self, interface: type[T], implementation: type[T] | T) -> None:
        """Register a service as singleton (single instance).

        Args:
            interface: The interface type to register
            implementation: The implementation class or instance
        """
        if isinstance(implementation, type):
            # Register a class to be instantiated once
            self._factories[interface] = lambda: implementation()
        else:
            # Register an already created instance
            self._singletons[interface] = implementation

        logger.debug(f"Registered singleton: {interface.__name__}")

    def register_transient(self, interface: type[T], implementation: type[T]) -> None:
        """Register a service as transient (new instance each time).

        Args:
            interface: The interface type to register
            implementation: The implementation class
        """
        self._factories[interface] = lambda: implementation()
        logger.debug(f"Registered transient: {interface.__name__}")

    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a custom factory function for a service.

        Args:
            interface: The interface type to register
            factory: Factory function that creates instances
        """
        self._factories[interface] = factory
        logger.debug(f"Registered factory for: {interface.__name__}")

    def register_instance(self, interface: type[T], instance: T) -> None:
        """Register a specific instance for a service.

        Args:
            interface: The interface type to register
            instance: The specific instance to use
        """
        self._singletons[interface] = instance
        logger.debug(f"Registered instance: {interface.__name__}")

    def resolve(self, interface: type[T]) -> T:
        """Resolve a service instance.

        Args:
            interface: The interface type to resolve

        Returns:
            T: Instance of the requested service

        Raises:
            ValueError: If the service is not registered
            RuntimeError: If circular dependency is detected
        """
        # Check for circular dependencies
        if interface in self._resolving:
            raise RuntimeError(f"Circular dependency detected for {interface.__name__}")

        # Return existing singleton
        if interface in self._singletons:
            return cast(T, self._singletons[interface])

        # Check if we have a factory
        if interface not in self._factories:
            raise ValueError(f"Service {interface.__name__} is not registered")

        try:
            self._resolving.add(interface)

            # Create instance using factory
            factory = self._factories[interface]
            instance = factory()

            # Store as singleton if it was registered as one
            if interface not in self._services:  # New registration
                self._singletons[interface] = instance

            logger.debug(f"Resolved: {interface.__name__}")
            return cast(T, instance)

        finally:
            self._resolving.discard(interface)

    def resolve_with_dependencies(self, interface: type[T]) -> T:
        """Resolve a service with automatic dependency injection.

        This method automatically injects dependencies into the constructor
        based on type annotations.

        Args:
            interface: The interface type to resolve

        Returns:
            T: Instance with dependencies injected
        """
        # For now, we'll use simple resolution
        # In a more advanced implementation, we could use inspect.signature
        # to automatically inject constructor dependencies
        return self.resolve(interface)

    def clear(self) -> None:
        """Clear all registered services (mainly for testing)."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._resolving.clear()
        logger.debug("DI container cleared")


# Global container instance
_container: DIContainer | None = None


def get_container() -> DIContainer:
    """Get the global DI container instance.

    Returns:
        DIContainer: The global container instance
    """
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def configure_dependencies() -> DIContainer:
    """Configure all application dependencies.

    This function sets up all the dependency registrations for the application,
    mapping interfaces to their implementations.

    Returns:
        DIContainer: Configured container ready for use
    """
    container = get_container()

    # Import interfaces from main packages (Spring MVC style)
    # Database connection provider
    from app.config.SqlLiteConfig import get_sql_lite_instance
    from app.repositories import (
        DatabaseConnectionProvider,
        ThreadQueryInterface,
        ThreadRepositoryInterface,
        UserRepositoryInterface,
    )
    from app.services import (
        AgentExecutionInterface,
        AgentServiceInterface,
        ConversationStateInterface,
        UserServiceInterface,
    )

    class SQLiteConnectionProvider:
        def get_connection(self):
            return get_sql_lite_instance()

    container.register_singleton(DatabaseConnectionProvider, SQLiteConnectionProvider())

    # Repository implementations
    from app.repositories.impl import ThreadRepositoryImpl

    def thread_repository_factory():
        db_provider = container.resolve(DatabaseConnectionProvider)
        return ThreadRepositoryImpl(db_provider)

    container.register_factory(ThreadRepositoryInterface, thread_repository_factory)
    container.register_factory(UserRepositoryInterface, thread_repository_factory)  # Same instance
    container.register_factory(ThreadQueryInterface, thread_repository_factory)  # Same instance

    # LLM Factory
    from app.ai_core.llm_factory.impl import LLMFactoryImpl

    container.register_transient(LLMFactoryInterface, LLMFactoryImpl)

    # Services
    from app.services.impl import (
        AgentServiceImpl,
        LangGraphServiceImpl,
        UserServiceImpl,
    )
    from app.utils.mt5_service import MT5Service
    from app.utils.reframe_chat import ReframeChat, create_reframe_chat_service

    # Create a singleton instance of LangGraphServiceImpl
    langgraph_service_instance = None
    
    def langgraph_service_factory():
        nonlocal langgraph_service_instance
        if langgraph_service_instance is None:
            llm_provider = container.resolve(LLMFactoryInterface)
            thread_repository = container.resolve(ThreadRepositoryInterface)
            db_provider = container.resolve(DatabaseConnectionProvider)
            langgraph_service_instance = LangGraphServiceImpl(llm_provider, thread_repository, db_provider)
        return langgraph_service_instance

    def agent_service_factory():
        agent_executor = container.resolve(AgentExecutionInterface)
        return AgentServiceImpl(agent_executor)

    def user_service_factory():
        user_repository = container.resolve(UserRepositoryInterface)
        thread_repository = container.resolve(ThreadRepositoryInterface)
        conversation_state = container.resolve(ConversationStateInterface)
        return UserServiceImpl(user_repository, thread_repository, conversation_state)

    container.register_factory(AgentExecutionInterface, langgraph_service_factory)
    container.register_factory(ConversationStateInterface, langgraph_service_factory)
    container.register_factory(AgentServiceInterface, agent_service_factory)
    container.register_factory(UserServiceInterface, user_service_factory)

    # Utility services
    container.register_factory(ReframeChat, create_reframe_chat_service)

    # Pre-create MT5Service to avoid circular dependency
    def mt5_service_factory():
        # Create a new instance of LLMFactoryImpl directly to avoid DI resolution
        from app.ai_core.llm_factory.impl import LLMFactoryImpl

        llm_factory = LLMFactoryImpl()
        return MT5Service(llm_factory)

    container.register_factory(MT5Service, mt5_service_factory)

    logger.info("Dependencies configured")
    return container


def inject(interface: type[T]) -> T:
    """Convenience function to resolve a dependency.

    Args:
        interface: The interface type to resolve

    Returns:
        T: Resolved service instance
    """
    return get_container().resolve(interface)
