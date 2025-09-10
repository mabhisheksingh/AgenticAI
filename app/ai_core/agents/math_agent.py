import logging

from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.prompts.common_prompts import MATH_SYSTEM_PROMPT
from app.ai_core.tools.combined_tools import get_math_tools
from app.core.di_container import inject
from app.core.enums import LLMProvider

logger = logging.getLogger(__name__)

_math_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", MATH_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]
)

math_agent = create_react_agent(
    model=inject(LLMFactoryInterface).create_model(
        llm_provider_type=LLMProvider.LLM_MEDIUM_MODEL,
        temperature=0.3,  # Lower temperature for more deterministic responses
        with_tools=False,
    ),
    tools=get_math_tools(),
    prompt=_math_prompt,
    name="math",
)
