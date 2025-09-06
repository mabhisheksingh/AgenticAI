"""LLM factory implementation for creating LLM instances.

This module provides factory implementation for creating Large Language Model instances
following the Factory pattern with support for multiple providers.

Implements LLMProviderInterface following ISP and DIP principles.
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq

from app.core.enums import LLMProvider
from app.agents.llm_provider_interface import LLMProviderInterface

logger = logging.getLogger(__name__)
load_dotenv()


def _get_temperature() -> float:
    """Get the LLM temperature setting from environment variables.
    
    Returns:
        float: Temperature value for LLM responses (0.0-1.0)
               Defaults to 0.7 if not set or invalid
               
    Environment Variables:
        LLM_TEMPERATURE: Temperature setting for LLM responses (default: "0.7")
    """
    raw = os.getenv("LLM_TEMPERATURE", "0.7")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.7


class LLMFactoryImpl(LLMProviderInterface):
    """Factory implementation for creating LLM (Large Language Model) instances.
    
    Implements LLMProviderInterface following ISP and DIP principles.
    This factory supports multiple LLM providers including:
    - Ollama: Local LLM inference
    - Google Gemini: Google's generative AI service
    
    The factory automatically configures models based on environment variables
    and provides standardized error handling for missing configurations.
    """

    def create_model(
            self,
            llm_provider_type: LLMProvider,
            temperature: float | None = None,
    ) -> BaseChatModel:

        model_name = os.getenv(llm_provider_type.value)
        if not model_name:
            raise ValueError(f"Environment variable {llm_provider_type.value} is not set")
        temp = temperature if temperature is not None else _get_temperature()
        logger.info("Creating model=%s temperature=%s (streaming on)", model_name, temp)
        llm_instance = self.load_llm(model_name, temp)
        logger.debug("LLM instance created successfully =%s ", llm_instance)
        logger.info("Returning LLM instance")
        return llm_instance

    def load_llm(self, model_name: str, temperature: float | None = None):
        temp = temperature if temperature is not None else _get_temperature()
        timeout = 60
        stop = None
        provider = self.get_provider(model_name)
        try:
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY is not set")
                return ChatOpenAI(
                    model=model_name,
                    temperature=temp,
                    api_key=SecretStr(api_key),
                    timeout=timeout
                )
            elif provider == "google":
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY is not set")
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=SecretStr(api_key),
                    temperature=temp,
                    timeout=timeout
                )
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY is not set")
                return ChatAnthropic(
                    model_name=model_name, 
                    api_key=SecretStr(api_key), 
                    temperature=temp,
                    timeout=60,
                    stop=None
                )
            elif provider == "groq":
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY is not set")
                return ChatGroq(
                    model=model_name,
                    api_key=SecretStr(api_key),
                    timeout=timeout
                )
            elif provider == "ollama":
                return ChatOllama(
                    model=model_name,
                    stop=stop,
                    temperature=temp
                )
            else:
                raise ValueError(f"Unknown provider for model: {model_name}")
        except ValueError as e:
            raise ValueError(f"Error loading model: {e}")

    @staticmethod
    def get_provider(model_name: str) -> str:
        return MODEL_PROVIDER_MAP.get(model_name, "unknown")


# Map of models to their providers for LangChain
MODEL_PROVIDER_MAP = {
    # OpenAI
    "gpt-3.5-turbo": "openai",
    "gpt-4": "openai",
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",

    # Google Gemini
    "gemini-1.5-pro": "google",
    "gemini-1.5-flash": "google",
    "gemini-2.5-flash": "google",

    # Anthropic Claude
    "claude-3-opus": "anthropic",
    "claude-3-sonnet": "anthropic",
    "claude-3-haiku": "anthropic",

    # Mistral
    "mistral-7b": "mistral",
    "mixtral-8x7b": "mistral",

    # Groq (fast inference hosting)
    "llama3-8b-8192": "groq",
    "llama3-70b-8192": "groq",
    "gemma-7b-it": "groq",
    "gemma2-27b-it": "groq",

    # Ollama (local)
    "llama3:70b": "ollama",
    "llama3.1:8b": "ollama",
    "mistral:7b": "ollama",
}
