"""LLM provider interfaces.

This module defines interfaces for LLM provider factories following
Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel


class LLMProviderInterface(ABC):
    """Abstract interface for LLM provider factories.
    
    Defines the contract for creating language model instances
    without coupling to specific provider implementations.
    """
    
    @abstractmethod
    def create_model(
        self, 
        provider: str | None = None, 
        *,
        model: str | None = None, 
        temperature: float | None = None
    ) -> BaseChatModel:
        """Create a language model instance."""
        pass