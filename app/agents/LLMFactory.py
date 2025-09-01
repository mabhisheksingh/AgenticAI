from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.enums import ErrorCode, LLMProvider
from app.core.errors import ApiErrorItem, AppError

logger = logging.getLogger(__name__)
load_dotenv()


def _error_item(errorcode, errormessage, errorStatus=400, errorField="provider"):
    return ApiErrorItem.model_validate({
        "errorcode": errorcode,
        "errormessage": errormessage,
        "errorStatus": errorStatus,
        "errorField": errorField,
    })


def _get_selected_llm_provider() -> LLMProvider:
    llm = os.getenv("LLM_PROVIDER")
    if not llm:
        raise RuntimeError("LLM_PROVIDER is not set")
    try:
        return LLMProvider(llm)
    except ValueError:
        item = _error_item(
            ErrorCode.validation_error.value,
            f"Unknown provider '{llm}'"
        )
        raise AppError(
            message="Unknown provider",
            code=ErrorCode.validation_error,
            status_code=400,
            errors=[item],
        )


def _get_temperature() -> float:
    raw = os.getenv("LLM_TEMPERATURE", "0.7")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.7


class LLMFactory:
    @staticmethod
    def create(
        provider: LLMProvider | str = None,
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> BaseChatModel:
        provider = provider if isinstance(provider, LLMProvider) else (
            LLMProvider(provider) if provider else _get_selected_llm_provider()
        )
        temp = temperature if temperature is not None else _get_temperature()

        if provider is LLMProvider.google_genai:
            model_name = model or os.getenv("GEMINI_MODEL_NAME")
            api_key = os.getenv("GOOGLE_API_KEY")
            if not model_name or not api_key:
                item = _error_item(
                    ErrorCode.validation_error.value,
                    "GEMINI_MODEL_NAME/GOOGLE_API_KEY is not set",
                    errorField="model"
                )
                raise AppError(
                    message="Model/API key not configured for ChatGoogleGenerativeAI",
                    code=ErrorCode.validation_error,
                    status_code=400,
                    errors=[item],
                )
            logger.debug("Creating ChatGoogleGenerativeAI model=%s temperature=%s", model_name, temp)
            return ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=temp)

        if provider is LLMProvider.ollama:
            model_name = model or os.getenv("OLLAMA_MODEL_NAME")
            if not model_name:
                item = _error_item(
                    ErrorCode.validation_error.value,
                    "OLLAMA_MODEL_NAME is not set",
                    errorField="model"
                )
                raise AppError(
                    message="Model not configured for ChatOllama",
                    code=ErrorCode.validation_error,
                    status_code=400,
                    errors=[item],
                )
            logger.debug("Creating ChatOllama model=%s temperature=%s", model_name, temp)
            return ChatOllama(model=model_name, temperature=temp)

        # Should never happen due to normalization, but guard anyway
        item = _error_item(
            ErrorCode.validation_error.value,
            f"Unsupported provider '{provider}'"
        )
        raise AppError(
            message="Unsupported provider",
            code=ErrorCode.validation_error,
            status_code=400,
            errors=[item],
        )
