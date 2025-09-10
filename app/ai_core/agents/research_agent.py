import logging

from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.prompts.common_prompts import RESEARCH_SYSTEM_PROMPT
from app.ai_core.tools.combined_tools import get_internet_tools
from app.core.di_container import inject
from app.core.enums import LLMProvider

logger = logging.getLogger(__name__)


# ---- General Agent ----
_research_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", RESEARCH_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]
)

research_agent = create_react_agent(
    model=inject(LLMFactoryInterface).create_model(
        llm_provider_type=LLMProvider.LLM_MEDIUM_MODEL,
        with_tools=False,
    ),
    tools=get_internet_tools(),
    prompt=_research_prompt,
    name="research",
)