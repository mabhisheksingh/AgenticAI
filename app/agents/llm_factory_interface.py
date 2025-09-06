"""LLM provider interfaces.

This module defines interfaces for LLM provider factories following
Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.enums import LLMProvider


class LLMFactoryInterface(ABC):
    """Abstract interface for LLM provider factories.
    
    Defines the contract for creating language model instances
    without coupling to specific provider implementations.
    """

    @abstractmethod
    def create_model(
            self,
            llm_provider_type: LLMProvider,
            temperature: float | None = None,
            with_tools: bool = True
    ) -> BaseChatModel:
        """Create a language model instance."""
        pass
