from __future__ import annotations

from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from app.core.enums import LLMProvider
from app.schemas.custom_state import CustomState
from app.utils.llm_utils import MODEL_PROVIDER_MAP, get_temperature
from app.utils.loging_utils import LOGGING_FORMAT

load_dotenv()
logging.basicConfig(
    format=LOGGING_FORMAT
)
logger = logging.getLogger(__name__)

# Simple cache to reduce repeated LLM calls
_query_cache = {}
_last_cache_cleanup = datetime.now()


def _get_llm():
    model_type = LLMProvider.LLM_MEDIUM_MODEL
    research_model = os.getenv(model_type)
    if not research_model:
        raise ValueError(f"{model_type} environment variable is not set")

    router_llm = init_chat_model(
        model=research_model,
        model_provider=MODEL_PROVIDER_MAP.get(research_model),
        temperature=get_temperature(),
    )
    return router_llm


class RouterState(BaseModel):
    routes: dict[str, str] = Field(
        ..., description="Mapping of user subqueries to their assigned agent"
    )


def llm_split_query(
    latest_query: list[BaseMessage] | str, history_summary: str = None
) -> RouterState | dict | BaseModel:
    """
    Splits the latest user query into sub-questions and assigns them to agents,
    using both the latest query and a summary of the past history.
    """

    # Normalize latest_query into plain text
    try:
        if isinstance(latest_query, list) and latest_query:
            # Expecting a list of BaseMessage
            last = latest_query[-1]
            latest_query = getattr(last, "content", str(last))
        elif isinstance(latest_query, str):
            # Already plain text
            pass
        else:
            latest_query = str(latest_query)
    except Exception:
        latest_query = str(latest_query)
    prompt = f"""
        You are an expert at decomposing complex user queries into atomic sub-questions.
        Consider the past conversation summary for context (carry over relevant context):
        {history_summary}

        Decompose the following user query into sub-questions. Be faithful to the user's wording; do not invent unrelated sub-questions. If the user asks for a calculation or includes a mathematical expression (e.g., 6 * 1 - 1), include a math sub-question and set its agent to "math".

        Return only a JSON object where:
        - keys are the sub-questions in natural language
        - values are one of: "research", "code", "math"

        Examples:
        {{
            "Who is the Prime Minister of India?": "research",
            "Write a Python script to implement a basic agent using LangGraph.": "code",
            "What is the result of 6 * 1 - 1?": "math"
        }}

        User Query: {latest_query}
        """

    # Prepare conversation messages
    messages: list[BaseMessage] = [HumanMessage(content=prompt)]
    llm = _get_llm()
    router_llm = llm.with_structured_output(RouterState)

    router_llm_response = router_llm.invoke(messages)
    if not router_llm_response.routes:
        return RouterState(routes={})
    return router_llm_response


# ---- Router ----
def router(state: CustomState) -> CustomState:
    """
    Multi-agent plan-and-dispatch router.
    Splits complex queries into atomic sub-queries, assigns each to the right agent,
    and dispatches them one by one. Final formatting is done after all sub-queries are processed.
    """
    logger.info("Router: processing start")
    messages = state.get("messages", [])
    logger.info("Messages : %s", messages)
    summary = state.get("summary", "")
    logger.info("Summary : %s", summary)
    routes = state["routes"]
    logger.info("Routes : %s", routes)
    if routes:
        return state

    subqueries = llm_split_query(messages, summary)
    logger.info("Subqueries: %s", subqueries)

    routes = subqueries.routes if hasattr(subqueries, "routes") else {}
    state["routes"] = routes
    logger.info("UPDATED state : %s", state)

    return state


