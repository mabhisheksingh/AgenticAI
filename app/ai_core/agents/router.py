from datetime import datetime
import logging
import re
from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.prompts.common_prompts import (
    build_conversation_summary_prompt,
)
from app.core.di_container import inject
from app.core.enums import LLMProvider
from app.schemas.custom_state import CustomState

logger = logging.getLogger(__name__)


# ---- Keyword Config ----
CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "math": {
        "calculate",
        "solve",
        "equation",
        "math",
        "mathematics",
        "algebra",
        "calculus",
        "geometry",
        "trigonometry",
        "statistics",
        "probability",
        "derivative",
        "integral",
        "square root",
        "factorial",
        "multiply",
        "divide",
        "add",
        "subtract",
        "*",
        "=",
        "?",
        "plus",
        "minus",
        "times",
        "divided by",
    },
    "code": {
        "code",
        "program",
        "function",
        "class",
        "method",
        "algorithm",
        "debug",
        "fix",
        "implement",
    },
    "general_time": {"time", "clock", "hour", "minute", "second", "now"},
    "general_web": {
        "weather",
        "news",
        "current",
        "latest",
        "today",
        "stock",
        "price",
        "sports",
        "score",
        "event",
        "happening",
        "trending",
        "future",
        "forecast",
        "prediction",
        "projections",
        "next year",
        "in ",
        "2025",
        "2026",
        "2027",
        "2028",
        "2029",
        "2030",
    },
}

PROGRAMMING_LANGUAGES: set[str] = {
    "java",
    "python",
    "javascript",
    "c++",
    "c#",
    "ruby",
    "php",
    "swift",
    "go",
    "rust",
    "kotlin",
    "scala",
    "perl",
    "matlab",
    "sql",
    "r",
}

CODE_PATTERNS = [
    re.compile(r"\bwrite a \w+", re.IGNORECASE),
    re.compile(r"\bcreate a \w+", re.IGNORECASE),
    re.compile(r"\bdevelop a \w+", re.IGNORECASE),
    re.compile(r"\bbuild a \w+", re.IGNORECASE),
    re.compile(r"\bmake a \w+", re.IGNORECASE),
    re.compile(r"\bcoding \w+", re.IGNORECASE),
    re.compile(r"\bprogramming \w+", re.IGNORECASE),
    re.compile(r"\bcode for", re.IGNORECASE),
    re.compile(r"\bprogram for", re.IGNORECASE),
]

# Enhanced regex pattern to detect math expressions more precisely
MATH_EXPRESSION_PATTERN = re.compile(r"\d+\s*[*+\-/x÷]\s*\d+\s*[=?]*", re.IGNORECASE)
GENERAL_INFO_PATTERNS = [
    re.compile(r"\bwhat\s+is\b", re.IGNORECASE),
    re.compile(r"\bwho\s+is\b", re.IGNORECASE),
    re.compile(r"\btell\s+me\s+about\b", re.IGNORECASE),
]

FUTURE_YEAR_PATTERN = re.compile(r"\b(20[2-9][0-9]|21[0-9][0-9])\b")


def update_state(state: CustomState, route: str) -> CustomState:
    logger.info(f"Router decided route: {route}")
    return cast(
        CustomState,
        {
            "query": state.get("query", ""),
            "route": route,
            "messages": state.get("messages", []),
        },
    )


def contains_keyword(query: str, keywords: set[str]) -> bool:
    return any(kw in query for kw in keywords)


def contains_regex(query: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(query) for p in patterns)


def extract_query(state: CustomState) -> str:
    messages = state.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content
    return state.get("query", "")


def should_use_llm(query: str) -> bool:
    if not query or len(query.strip()) < 3:
        return False
    if len(query.split()) == 1:
        query_lower = query.lower()
        all_keywords = set().union(*CATEGORY_KEYWORDS.values()).union(PROGRAMMING_LANGUAGES)
        if query_lower in all_keywords:
            return False
    return True


def contains_future_year(query: str) -> bool:
    current_year = datetime.now().year
    matches = re.findall(r"\b(20[0-9]{2})\b", query)
    return any(int(year) >= current_year for year in matches)


def should_route_to_web(query: str) -> bool:
    if contains_keyword(query, CATEGORY_KEYWORDS["general_web"]):
        return True
    if contains_regex(query, GENERAL_INFO_PATTERNS):
        return True
    if contains_future_year(query):
        return True
    return False


def summarize_messages(
    messages: list[BaseMessage], llm_factory: LLMFactoryInterface
) -> list[BaseMessage]:
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


def llm_split_query(llm: BaseChatModel, query: str) -> list[str]:
    """
    Use an LLM to break a user query into atomic sub-queries.
    Returns a list of sub-queries.
    """
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


# ---- Router ----
def router(state: CustomState) -> CustomState:
    """Plan-and-dispatch router.

    Behavior:
    - If a routing_plan exists, pop the next (agent, subquery), push the subquery as a HumanMessage,
      set route accordingly, and return updated state with remaining plan.
    - Otherwise, build a routing_plan using the router LLM via llm_split_query, then dispatch the first task.
    - For trivial queries (no LLM needed), route directly using heuristics.
    """
    messages = state.get("messages", [])
    query = extract_query(state)
    logger.info(f"Routing query: {query}")

    # If we already have a plan, dispatch the next task
    existing_plan = cast(list[tuple[str, str]], state.get("routing_plan", [])) or []
    if existing_plan:
        next_agent, next_subq = existing_plan[0]
        remaining = existing_plan[1:]
        logger.info(f"Dispatching next task -> agent={next_agent}, subquery={next_subq}")
        # Push the subquery as a new HumanMessage to become the immediate context for the agent
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

    # If no remaining tasks but we had an active plan, hand off to final formatting
    if state.get("plan_active"):
        logger.info("Routing plan completed. Handing off to nlp_formatting.")
        return cast(
            CustomState,
            {**state, "route": "nlp_formatting", "pending_routes": [], "plan_active": False},
        )

    # No existing plan -> determine if trivial; if so, route directly
    if not should_use_llm(query):
        direct_route = pick_agent_for_subquery(query)
        logger.info(f"Trivial query detected. Direct route -> {direct_route}")
        return cast(CustomState, {**state, "route": direct_route, "pending_routes": []})

    # Build a new routing plan using the router LLM
    router_llm_factory = inject(LLMFactoryInterface)
    router_llm = router_llm_factory.create_model(LLMProvider.LLM_MEDIUM_MODEL, with_tools=False)
    subqueries = llm_split_query(router_llm, query)
    routing_plan: list[tuple[str, str]] = []
    for subq in subqueries:
        agent = pick_agent_for_subquery(subq)
        routing_plan.append((agent, subq))

    logger.info("Routing plan built: %s", routing_plan)

    # If plan is empty (shouldn't happen), fallback to research
    if not routing_plan:
        return cast(CustomState, {**state, "route": "research", "pending_routes": []})

    # Dispatch first task
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
