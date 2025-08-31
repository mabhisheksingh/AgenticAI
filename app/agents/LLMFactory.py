from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.enums import ErrorCode, LLMProvider
from app.core.errors import ApiErrorItem, AppError

_logger = logging.getLogger("api")
load_dotenv()


def _get_temperature() -> float:
    raw = os.getenv("LLM_TEMPERATURE", "0.7")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.7


class LLMFactory:
    @staticmethod
    def create(
        provider: LLMProvider | str,
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> BaseChatModel:
        # Normalize provider to Enum
        if isinstance(provider, str):
            try:
                provider = LLMProvider(provider)
            except ValueError:
                item = ApiErrorItem.model_validate(
                    {
                        "errorcode": ErrorCode.validation_error.value,
                        "errormessage": f"Unknown provider '{provider}'",
                        "errorStatus": 400,
                        "errorField": "provider",
                    }
                )
                raise AppError(
                    message="Unknown provider",
                    code=ErrorCode.validation_error,
                    status_code=400,
                    errors=[item],
                ) from None

        temp = temperature if temperature is not None else _get_temperature()

        if provider is LLMProvider.openai:
            model_name = model or os.getenv("OPENAI_MODEL")
            if not model_name:
                item = ApiErrorItem.model_validate(
                    {
                        "errorcode": ErrorCode.validation_error.value,
                        "errormessage": "OPENAI_MODEL is not set",
                        "errorStatus": 400,
                        "errorField": "model",
                    }
                )
                raise AppError(
                    message="Model not configured for OpenAI",
                    code=ErrorCode.validation_error,
                    status_code=400,
                    errors=[item],
                )
            _logger.debug("Creating ChatOpenAI model=%s temperature=%s", model_name, temp)
            return ChatOpenAI(model=model_name, temperature=temp)

        if provider is LLMProvider.ollama:
            model_name = model or os.getenv("OLLAMA_MODEL_NAME")
            if not model_name:
                item = ApiErrorItem.model_validate(
                    {
                        "errorcode": ErrorCode.validation_error.value,
                        "errormessage": "OLLAMA_MODEL_NAME is not set",
                        "errorStatus": 400,
                        "errorField": "model",
                    }
                )
                raise AppError(
                    message="Model not configured for Ollama",
                    code=ErrorCode.validation_error,
                    status_code=400,
                    errors=[item],
                )
            _logger.debug("Creating ChatOllama model=%s temperature=%s", model_name, temp)
            return ChatOllama(model=model_name, temperature=temp)

        # Should never happen due to normalization, but guard anyway
        item = ApiErrorItem.model_validate(
            {
                "errorcode": ErrorCode.validation_error.value,
                "errormessage": f"Unsupported provider '{provider}'",
                "errorStatus": 400,
                "errorField": "provider",
            }
        )
        raise AppError(
            message="Unsupported provider",
            code=ErrorCode.validation_error,
            status_code=400,
            errors=[item],
        )
