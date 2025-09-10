import logging

from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.prompts.common_prompts import CODE_SYSTEM_PROMPT
from app.ai_core.tools.combined_tools import get_combined_tools
from app.core.di_container import inject
from app.core.enums import LLMProvider

logger = logging.getLogger(__name__)


# ---- Code Agent ----

_code_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CODE_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]
)

code_agent = create_react_agent(
    model=inject(LLMFactoryInterface).create_model(
        llm_provider_type=LLMProvider.LLM_LARGE_MODEL,
        with_tools=False,
    ),
    tools=get_combined_tools(),
    prompt=_code_prompt,
    name="code",
)