import logging

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.pregel import Pregel
from langgraph_supervisor import create_supervisor

from app.ai_core.agents.code_agent import code_agent
from app.ai_core.agents.math_agent import math_agent
from app.ai_core.agents.research_agent import research_agent
from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.prompts.common_prompts import SUPERVISOR_SYSTEM_PROMPT
from app.config.SqlLiteConfig import get_sql_lite_instance
from app.core.di_container import inject
from app.core.enums import LLMProvider

logger = logging.getLogger(__name__)

# Create a model for the supervisor with appropriate settings
_supervisor_model = inject(LLMFactoryInterface).create_model(
    LLMProvider.LLM_LARGE_MODEL, with_tools=False
)

# Create supervisor workflow with clear instructions
_supervisor_workflow = create_supervisor(
    model=_supervisor_model,
    agents=[math_agent, code_agent, research_agent],
    prompt=SUPERVISOR_SYSTEM_PROMPT,
)

# Compile the base graph with synchronous SqliteSaver
graph: Pregel = _supervisor_workflow.compile(
    checkpointer=SqliteSaver(get_sql_lite_instance()), name="Supervisor Agent", debug=True
)