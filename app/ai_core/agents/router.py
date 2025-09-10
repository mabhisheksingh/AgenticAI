from datetime import datetime
import logging
import re
from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.core.di_container import inject
from app.core.enums import LLMProvider
from app.schemas.custom_state import CustomState

logger = logging.getLogger(__name__)


def extract_query(state: CustomState) -> str:
    messages = state.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content
    return ""


def should_use_llm(query: str) -> bool:
    if not query or len(query.strip()) < 3:
        return False
    if len(query.split()) == 1:
        return False
    return True


def llm_split_query(llm: BaseChatModel, query: str) -> list[str]:
    prompt = (
        """
        You are an expert at decomposing complex user queries into atomic sub-questions.
        Given the following user query, split it into a list of minimal, non-overlapping sub-questions, each suitable for a single specialized agent (math, code, research, etc.).
        Return ONLY the list, one per line, no extra commentary.
        User Query: """
        + query
        + """
        """
    )
    response = llm.invoke(prompt)
    subqueries = [
        line.strip("- ").strip() for line in response.content.strip().split("\n") if line.strip()
    ]
    logger.info("subquires : %s", subqueries)
    return subqueries


def pick_agent_for_subquery(subquery: str) -> str:
    code_keywords = [
        "code",
        "program",
        "function",
        "class",
        "algorithm",
        "java",
        "python",
        "c++",
        "snippet",
        "write code",
        "implement",
        "script",
        "source code",
        "solve using code",
    ]
    if any(kw in subquery.lower() for kw in code_keywords):
        return "code"
    if re.search(r"\d+\s*[*+\-/x÷^%]\s*\d+", subquery):
        return "math"
    return "research"


def summarize_messages(
    messages: list[BaseMessage], llm_factory: LLMFactoryInterface
) -> list[BaseMessage]:
    """
    Summarize older conversation history to keep message list short for LLM context.
    Keeps the last 3 messages and summarizes the rest using a summarization LLM.
    """
    if len(messages) <= 6:
        return messages
    try:
        recent_messages = messages[-3:]
        older_messages_text = "\n".join(
            [f"{type(msg).__name__}: {getattr(msg, 'content', '')}" for msg in messages[:-3]]
        )
        summarization_llm = llm_factory.create_model(
            LLMProvider.LLM_SUMMARIZATION_MODEL, with_tools=False
        )
        summary_prompt = build_conversation_summary_prompt(older_messages_text)
        summary_response = summarization_llm.invoke(summary_prompt)
        summary_content = str(getattr(summary_response, "content", "Previous conversation history"))
        summary_message = AIMessage(content=f"Summary of previous conversation: {summary_content}")
        return [summary_message] + recent_messages
    except Exception as e:
        logger.warning(f"Error summarizing messages, returning recent messages only: {e}")
        return messages[-3:]


# ---- Router ----
def router(state: CustomState) -> CustomState:
    """
    Multi-agent plan-and-dispatch router.
    Splits complex queries into atomic sub-queries, assigns each to the right agent,
    and dispatches them one by one. Final formatting is done after all sub-queries are processed.
    """
    messages = state.get("messages", [])
    query = extract_query(state)
    logger.info(f"Routing query: {query}")

    # If we already have a routing plan, dispatch the next sub-query to its agent
    existing_plan = cast(list[tuple[str, str]], state.get("routing_plan", [])) or []
    if existing_plan:
        next_agent, next_subq = existing_plan[0]
        remaining = existing_plan[1:]
        logger.info(f"Dispatching next task -> agent={next_agent}, subquery={next_subq}")
        # Add subquery as a HumanMessage so agent receives it as context
        new_messages = list(messages) + [HumanMessage(content=next_subq)]
        return cast(
            CustomState,
            {
                **state,
                "messages": new_messages,
                "route": next_agent,
                "routing_plan": remaining,
                "pending_routes": [a for a, _ in remaining],
                "plan_active": True,
            },
        )

    # If plan is exhausted, hand off to the formatting agent for final output
    if state.get("plan_active"):
        logger.info("Routing plan completed. Handing off to nlp_formatting.")
        return cast(
            CustomState,
            {**state, "route": "nlp_formatting", "pending_routes": [], "plan_active": False},
        )

    # If the query is trivial (single task), route directly to the right agent
    if not should_use_llm(query):
        direct_route = pick_agent_for_subquery(query)
        logger.info(f"Trivial query detected. Direct route -> {direct_route}")
        return cast(CustomState, {**state, "route": direct_route, "pending_routes": []})

    # For complex queries, use LLM to split into sub-queries and build a routing plan
    router_llm_factory = inject(LLMFactoryInterface)
    router_llm = router_llm_factory.create_model(LLMProvider.LLM_MEDIUM_MODEL, with_tools=False)
    subqueries = llm_split_query(router_llm, query)
    routing_plan: list[tuple[str, str]] = []
    for subq in subqueries:
        agent = pick_agent_for_subquery(subq)
        routing_plan.append((agent, subq))

    logger.info("Routing plan built: %s", routing_plan)

    # If plan is empty, fallback to research agent
    if not routing_plan:
        return cast(CustomState, {**state, "route": "research", "pending_routes": []})

    # Start dispatching the first sub-query in the plan
    next_agent, next_subq = routing_plan[0]
    remaining = routing_plan[1:]
    new_messages = list(messages) + [HumanMessage(content=next_subq)]
    return cast(
        CustomState,
        {
            **state,
            "messages": new_messages,
            "route": next_agent,
            "routing_plan": remaining,
            "pending_routes": [a for a, _ in remaining],
            "plan_active": True,
        },
    )
