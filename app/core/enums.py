"""Core enumerations for the AgenticAI application.

This module defines various enumerations used throughout the application
for API versioning, routing tags, environments, agent types, error codes,
and LLM provider specifications.
"""
from enum import Enum


class APIVersion(str, Enum):
    """API version enumeration for versioning endpoints.
    
    Used to maintain backward compatibility and controlled API evolution.
    All API routes are prefixed with the version (e.g., /v1/*, /v2/*).
    """
    v1 = "v1"
    v2 = "v2"


class RouterTag(str, Enum):
    """Router tags for organizing API endpoints in OpenAPI documentation.
    
    These tags group related endpoints together in the Swagger/OpenAPI UI
    for better organization and discoverability.
    """
    user = "user"
    agent = "agent"


class Environment(str, Enum):
    """Application environment enumeration.
    
    Defines the possible runtime environments for configuration
    and behavior customization.
    """
    dev = "dev"
    prod = "prod"
    test = "test"


class AgentType(str, Enum):
    """AI agent type enumeration for different agent behaviors.
    
    Defines the various types of AI agents that can be instantiated
    within the LangGraph orchestration system.
    """
    conversational = "conversational"
    retriever = "retriever"
    planner = "planner"


class ErrorCode(str, Enum):
    """Standardized error codes for consistent error handling.
    
    Used throughout the application to provide consistent error
    identification and handling across all API endpoints.
    """
    not_found = "NOT_FOUND"
    validation_error = "VALIDATION_ERROR"
    internal_error = "INTERNAL_ERROR"


class LLMProvider(str, Enum):
    # === Medium models
    LLM_MEDIUM_MODEL = "LLM_MEDIUM_MODEL"
    # === Large models
    LLM_LARGE_MODEL = "LLM_LARGE_MODEL"
    # === Small / Fast models
    LLM_SMALL_MODEL = "LLM_SMALL_MODEL"
    # === TINY models
    LLM_TINY_MODEL = "LLM_TINY_MODEL"

    # === Task Specific ===
    LLM_CORRECTION_MODEL ="LLM_CORRECTION_MODEL"
    LLM_TRANSLATION_MODEL ="LLM_TRANSLATION_MODEL"
    LLM_REASONING_MODEL ="LLM_LARGE_MODEL"
    LLM_SUMMARIZATION_MODEL ="LLM_SMALL_MODEL"
