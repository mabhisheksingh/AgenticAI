"""LLM factory implementation for creating LLM instances.

This module provides factory implementation for creating Large Language Model instances
following the Factory pattern with support for multiple providers.

Implements LLMFactoryInterface following ISP and DIP principles.
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.tools.combined_tools import get_combined_tools
from app.core.enums import LLMProvider
from app.agents.llm_factory_interface import LLMFactoryInterface

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


class LLMFactoryImpl(LLMFactoryInterface):
    """Factory implementation for creating LLM (Large Language Model) instances.
    
    Implements LLMFactoryInterface following ISP and DIP principles.
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
            with_tools: bool = True
    ) -> BaseChatModel:

        model_name = os.getenv(llm_provider_type.value)
        if not model_name:
            raise ValueError(f"Environment variable {llm_provider_type.value} is not set")
        temp = temperature if temperature is not None else _get_temperature()
        logger.info("Creating model=%s temperature=%s (streaming on)", model_name, temp)
        llm_instance = self.load_llm(model_name, temp, with_tools)
        logger.debug("LLM instance created successfully =%s ", llm_instance)
        logger.info("Returning LLM instance")
        return llm_instance

    def load_llm(self, model_name: str, temperature: float | None = None, with_tools: bool = True):
        logger.info("Loading LLM instance")
        temp = temperature if temperature is not None else _get_temperature()
        timeout = 60
        stop = None
        provider = self.get_provider(model_name)
        tools = get_combined_tools()
        logger.info("Provider and tool are loaded successfully")
        llm:BaseChatModel
        try:
            if provider == "openai":
                # Lazy load OpenAI dependencies only when needed
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError as e:
                    raise ImportError(
                        "OpenAI dependencies not found. Please ensure langchain-openai is installed."
                    ) from e
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY is not set")
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=temp,
                    api_key=SecretStr(api_key),
                    timeout=timeout
                )
            elif provider == "google":
                # Lazy load Google dependencies only when needed
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                except ImportError as e:
                    raise ImportError(
                        "Google Generative AI dependencies not found. Please ensure langchain-google-genai is installed."
                    ) from e
                
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY is not set")
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=SecretStr(api_key),
                    temperature=temp,
                    timeout=timeout
                )
            elif provider == "anthropic":
                # Lazy load Anthropic dependencies only when needed
                try:
                    from langchain_anthropic import ChatAnthropic
                except ImportError as e:
                    raise ImportError(
                        "Anthropic dependencies not found. Please ensure langchain-anthropic is installed."
                    ) from e
                
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY is not set")
                llm = ChatAnthropic(
                    model_name=model_name, 
                    api_key=SecretStr(api_key), 
                    temperature=temp,
                    timeout=60,
                    stop=None
                )
            elif provider == "groq":
                # Lazy load Groq dependencies only when needed
                try:
                    from langchain_groq import ChatGroq
                except ImportError as e:
                    raise ImportError(
                        "Groq dependencies not found. Please ensure langchain-groq is installed."
                    ) from e
                
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY is not set")
                llm =  ChatGroq(
                    model=model_name,
                    api_key=SecretStr(api_key),
                    timeout=timeout
                )
            elif provider == "ollama":
                # Lazy load Ollama dependencies only when needed
                try:
                    from langchain_ollama import ChatOllama
                except ImportError as e:
                    raise ImportError(
                        "Ollama dependencies not found. Please ensure langchain-ollama is installed."
                    ) from e
                
                llm = ChatOllama(
                    model=model_name,
                    stop=stop,
                    temperature=temp
                )
            elif provider == "huggingface":
                # Lazy load Hugging Face dependencies only when needed
                try:
                    from langchain_huggingface import HuggingFacePipeline
                    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
                except ImportError as e:
                    raise ImportError(
                        "Hugging Face dependencies not found. Please install them with: "
                        "pip install -r requirements-huggingface.txt"
                    ) from e
                
                # load tokenizer + model
                model_id = model_name
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

                # create HF pipeline
                pipe = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

                # Use HuggingFacePipeline instead of ChatHuggingFace
                llm = HuggingFacePipeline(
                    pipeline=pipe,
                    model_kwargs={"temperature": temp, "max_length": 512}
                )
            else:
                raise ValueError(f"Unknown provider for model: {model_name}")
        except ValueError as e:
            raise ValueError(f"Error loading model: {e}")
        return llm.bind_tools(tools) if with_tools else llm

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

    # Hugging Face
    "google/mt5-small": "huggingface",
    "prithivida/grammar_error_correcter_v1": "huggingface",
    "vennify/t5-base-grammar-correction": "huggingface",
}