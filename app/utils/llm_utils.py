import logging
import os
import re

from app.utils.loging_utils import LOGGING_FORMAT

logging.basicConfig(
    format=LOGGING_FORMAT
)
logger = logging.getLogger(__name__)


def get_temperature() -> float:
    """Get the LLM temperature setting from environment variables.

    Returns:
        float: Temperature value for LLM responses (0.0-1.0)
               Defaults to 0.7 if not set or invalid

    Environment Variables:
        LLM_TEMPERATURE: Temperature setting for LLM responses (default: "0.7")
    """
    raw = os.getenv("LLM_TEMPERATURE", "0.7")
    try:
        temp = float(raw)
    except (TypeError, ValueError):
        temp = 0.7
    return temp


def normalize_query(q: str) -> str:
    # remove trailing ? . !, strip spaces, and lowercase
    return re.sub(r"[\?\.\!]+$", "", q.strip()).lower()


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
