from dataclasses import dataclass
import os
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate

from app.utils.prompt_utils import (
    CODE_SYSTEM_PROMPT,
    MATH_SYSTEM_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
)
from app.ai_core.tools.combined_tools import get_combined_tools, get_internet_tools, get_math_tools
from app.core.enums import LLMProvider
from app.utils.llm_utils import MODEL_PROVIDER_MAP, get_temperature


@dataclass(frozen=True)
class AgentConfig:
    name: str
    description: str
    model: str
    tools: list[Any]
    model_provider: Literal[
        "openai", "anthropic", "deepseek", "google", "mistral", "groq", "ollama", "huggingface"
    ]
    temperature: float
    prompt: ChatPromptTemplate


medium_model = os.getenv(LLMProvider.LLM_MEDIUM_MODEL)
if not medium_model:
    raise ValueError(f"{medium_model} environment variable is not set")

small_model = os.getenv(LLMProvider.LLM_SMALL_MODEL)
if not small_model:
    raise ValueError(f"{small_model} environment variable is not set")

large_model = os.getenv(LLMProvider.LLM_LARGE_MODEL)
if not large_model:
    raise ValueError(f"{large_model} environment variable is not set")

correction_model = os.getenv(LLMProvider.LLM_CORRECTION_MODEL)
if not correction_model:
    raise ValueError(f"{correction_model} environment variable is not set")

# Agents
MATH_AGENT = AgentConfig(
    name="math",
    description="Useful for when you need to answer questions about math.",
    model=medium_model,
    tools=get_math_tools(),
    temperature=get_temperature(),
    prompt=ChatPromptTemplate.from_messages(
        [
            ("system", MATH_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    ),
    model_provider=MODEL_PROVIDER_MAP.get(medium_model),
)

RESEARCH_AGENT = AgentConfig(
    name="research",
    description="Useful for when you need to answer questions about research.",
    model=medium_model,
    tools=get_internet_tools(),
    temperature=get_temperature(),
    prompt=ChatPromptTemplate.from_messages(
        [
            ("system", RESEARCH_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    ),
    model_provider=MODEL_PROVIDER_MAP.get(medium_model),
)

CORRECTION_AGENT = AgentConfig(
    name="correction",
    description="Useful for when you need to answer questions about correction.",
    model=small_model,
    tools=get_internet_tools(),
    temperature=get_temperature(),
    prompt=ChatPromptTemplate.from_messages(
        [
            ("system", CODE_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    ),
    model_provider=MODEL_PROVIDER_MAP.get(small_model),
)

CODE_AGENT = AgentConfig(
    name="code",
    description="Useful for when you need to answer questions about code.",
    model=medium_model,
    tools=get_combined_tools(),
    temperature=get_temperature(),
    prompt=ChatPromptTemplate.from_messages(
        [
            ("system", CODE_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    ),
    model_provider=MODEL_PROVIDER_MAP.get(medium_model),
)
