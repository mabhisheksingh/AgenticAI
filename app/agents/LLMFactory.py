from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from app.core.enums import ErrorCode, LLMProvider
from app.core.errors import ApiErrorItem, AppError

logger = logging.getLogger(__name__)
load_dotenv()


def _error_item(errorcode, errormessage, errorStatus=400, errorField="provider"):
    """
    Create a standardized API error item.
    
    Args:
        errorcode (str): Error code identifying the type of error
        errormessage (str): Human-readable error message
        errorStatus (int, optional): HTTP status code. Defaults to 400.
        errorField (str, optional): Field that caused the error. Defaults to "provider".
        
    Returns:
        ApiErrorItem: Validated error item for API responses
    """
    return ApiErrorItem.model_validate(
        {
            "errorcode": errorcode,
            "errormessage": errormessage,
            "errorStatus": errorStatus,
            "errorField": errorField,
        }
    )


def _get_selected_llm_provider() -> LLMProvider:
    """
    Get the selected LLM provider from environment variables.
    
    Returns:
        LLMProvider: The selected LLM provider enum value
        
    Raises:
        RuntimeError: If LLM_PROVIDER environment variable is not set
        AppError: If the provider value is not recognized
        
    Environment Variables:
        LLM_PROVIDER: The LLM provider to use ('ollama' or 'google_genai')
    """
    llm = os.getenv("LLM_PROVIDER")
    if not llm:
        raise RuntimeError("LLM_PROVIDER is not set")
    try:
        return LLMProvider(llm)
    except ValueError:
        item = _error_item(ErrorCode.validation_error.value, f"Unknown provider '{llm}'")
        raise AppError(
            message="Unknown provider",
            code=ErrorCode.validation_error,
            status_code=400,
            errors=[item],
        )


def _get_temperature() -> float:
    """
    Get the LLM temperature setting from environment variables.
    
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


class LLMFactory:
    """
    Factory class for creating LLM (Large Language Model) instances.
    
    This factory supports multiple LLM providers including:
    - Ollama: Local LLM inference
    - Google Gemini: Google's generative AI service
    
    The factory automatically configures models based on environment variables
    and provides standardized error handling for missing configurations.
    """
    
    @staticmethod
    def create(
        provider: LLMProvider | str | None = None,
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> BaseChatModel:
        """
        Create an LLM instance based on the specified or configured provider.
        
        Args:
            provider (LLMProvider | str, optional): LLM provider to use.
                                                   If None, uses LLM_PROVIDER env var.
            model (str, optional): Model name to use. If None, uses provider-specific env var.
            temperature (float, optional): Temperature for response generation.
                                         If None, uses LLM_TEMPERATURE env var.
                                         
        Returns:
            BaseChatModel: Configured LLM instance ready for chat operations
            
        Raises:
            AppError: If required environment variables are missing or invalid
            
        Environment Variables:
            LLM_PROVIDER: Provider to use ('ollama' or 'google_genai')
            LLM_TEMPERATURE: Temperature setting (default: 0.7)
            
            For Google Gemini:
                GOOGLE_API_KEY: API key for Google Gemini
                GEMINI_MODEL_NAME: Model name (e.g., 'gemini-2.5-flash')
                
            For Ollama:
                OLLAMA_MODEL_NAME: Model name (e.g., 'llama3.1:8b')
                
        Examples:
            >>> # Use environment configuration
            >>> llm = LLMFactory.create()
            
            >>> # Specify provider and model
            >>> llm = LLMFactory.create(
            ...     provider="ollama",
            ...     model="llama3.1:8b",
            ...     temperature=0.8
            ... )
        """
        provider = (
            provider
            if isinstance(provider, LLMProvider)
            else (LLMProvider(provider) if provider else _get_selected_llm_provider())
        )
        temp = temperature if temperature is not None else _get_temperature()

        if provider is LLMProvider.google_genai:
            model_name = model or os.getenv("GEMINI_MODEL_NAME")
            api_key = os.getenv("GOOGLE_API_KEY")
            if not model_name or not api_key:
                item = _error_item(
                    ErrorCode.validation_error.value,
                    "GEMINI_MODEL_NAME/GOOGLE_API_KEY is not set",
                    errorField="model",
                )
                raise AppError(
                    message="Model/API key not configured for ChatGoogleGenerativeAI",
                    code=ErrorCode.validation_error,
                    status_code=400,
                    errors=[item],
                )
            logger.debug(
                "Creating ChatGoogleGenerativeAI model=%s temperature=%s (streaming on)",
                model_name,
                temp,
            )
            return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=temp)

        if provider is LLMProvider.ollama:
            model_name = model or os.getenv("OLLAMA_MODEL_NAME")
            if not model_name:
                item = _error_item(
                    ErrorCode.validation_error.value,
                    "OLLAMA_MODEL_NAME is not set",
                    errorField="model",
                )
                raise AppError(
                    message="Model not configured for ChatOllama",
                    code=ErrorCode.validation_error,
                    status_code=400,
                    errors=[item],
                )
            logger.debug(
                "Creating ChatOllama model=%s temperature=%s (streaming on)", model_name, temp
            )
            return ChatOllama(model=model_name, temperature=temp)

        # Should never happen due to normalization, but guard anyway
        item = _error_item(ErrorCode.validation_error.value, f"Unsupported provider '{provider}'")
        raise AppError(
            message="Unsupported provider",
            code=ErrorCode.validation_error,
            status_code=400,
            errors=[item],
        )
