from datetime import datetime
import logging
import os
import re
from typing import cast

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from app.utils.prompt_utils import (
    build_conversation_summary_prompt,
    build_final_response_prompt,
)
from app.core.di_container import inject
from app.core.enums import LLMProvider
from app.schemas.custom_state import CustomState
from app.utils.llm_utils import MODEL_PROVIDER_MAP, get_temperature

load_dotenv()
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


def _cleanup_cache():
    """Clean up old cache entries to prevent memory issues."""
    global _last_cache_cleanup
    now = datetime.now()

    # Clean up cache every 10 minutes
    if (now - _last_cache_cleanup).total_seconds() > 600:
        # Remove entries older than 15 minutes
        cutoff_time = now.timestamp() - 900
        keys_to_remove = [
            key
            for key, (_, timestamp) in _query_cache.items()
            if timestamp.timestamp() < cutoff_time
        ]
        for key in keys_to_remove:
            del _query_cache[key]
        _last_cache_cleanup = now
        logger.info(f"Cleaned up {len(keys_to_remove)} old cache entries")


def _content_starts_with(content, prefix: str) -> bool:
    """Return True if the given content (str or content-part list) starts with prefix.

    Handles LangChain content being either a plain string or a list of parts
    like [{"type": "text", "text": "..."}].
    """
    if isinstance(content, str):
        return content.startswith(prefix)
    if isinstance(content, list):
        for part in content:
            if isinstance(part, str):
                return part.startswith(prefix)
            if isinstance(part, dict) and part.get("type") == "text":
                text = str(part.get("text", ""))
                return text.startswith(prefix)
        return False
    return False


def extract_query(state: CustomState) -> str:
    messages = state.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            # Handle different content formats
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from content parts
                texts = []
                for part in content:
                    if isinstance(part, str):
                        texts.append(part)
                    elif isinstance(part, dict):
                        if part.get("type") == "text":
                            texts.append(part.get("text", ""))
                        else:
                            texts.append(str(part))
                    else:
                        texts.append(str(part))
                return " ".join(texts)
            else:
                return str(content)
    return ""


def should_use_llm(query: str) -> bool:
    if not query or len(query.strip()) < 3:
        return False
    if len(query.split()) == 1:
        return False
    return True


def llm_split_query(llm: BaseChatModel, query: str) -> list[str]:
    # Clean up cache periodically
    _cleanup_cache()

    # Check cache first
    cache_key = f"split_{query}"
    if cache_key in _query_cache:
        cached_result, timestamp = _query_cache[cache_key]
        # Cache for 5 minutes
        if (datetime.now() - timestamp).total_seconds() < 300:
            logger.info(f"Using cached result for query splitting: {query}")
            return cached_result

    prompt = (
            """
            You are an expert at decomposing complex user queries into atomic, self-contained sub-questions.
            Given the following user query, split it into a list of minimal, non-overlapping sub-questions.
            **Crucially, if a sub-question depends on the context of another (e.g., a name, location, or topic), you must carry that context over.**
    
            Example 1:
            User Query: "Who is the PM of India and what were the results of the latest vice presidential election?"
            Sub-questions:
            - Who is the Prime Minister of India?
            - What were the results of the latest Indian vice presidential election?
    
            Example 2:
            User Query: "What is LangGraph and can you write a python script to implement a basic agent?"
            Sub-questions:
            - What is LangGraph?
            - Write a python script to implement a basic agent using LangGraph.
    
            Return ONLY the list of sub-questions, one per line, with no extra commentary.
            User Query: """
            + query
            + """
        """
    )
    response = llm.invoke(prompt)

    # Handle different response content formats
    content = response.content
    if isinstance(content, list):
        # Extract text from content parts
        texts = []
        for part in content:
            if isinstance(part, str):
                texts.append(part)
            elif isinstance(part, dict):
                if part.get("type") == "text":
                    texts.append(part.get("text", ""))
                else:
                    texts.append(str(part))
            else:
                texts.append(str(part))
        content_text = " ".join(texts)
    else:
        content_text = str(content)

    subqueries = [
        line.strip("- ").strip() for line in content_text.strip().split("\n") if line.strip()
    ]
    logger.info("subquires : %s", subqueries)

    # Cache the result
    _query_cache[cache_key] = (subqueries, datetime.now())
    return subqueries


def pick_agent_for_subquery(subquery: str) -> str:
    # Clean up cache periodically
    _cleanup_cache()

    # Check cache first
    cache_key = f"agent_{subquery}"
    if cache_key in _query_cache:
        cached_result, timestamp = _query_cache[cache_key]
        # Cache for 10 minutes
        if (datetime.now() - timestamp).total_seconds() < 600:
            logger.info(f"Using cached result for agent picking: {subquery}")
            return cached_result

    # Ensure subquery is a string
    if not isinstance(subquery, str):
        subquery = str(subquery)

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
        result = "code"
    elif re.search(r"\d+\s*[*+\-/x÷^%]\s*\d+", subquery):
        result = "math"
    else:
        result = "research"

    # Cache the result
    _query_cache[cache_key] = (result, datetime.now())
    return result


def should_skip_llm_split(query: str, state: CustomState) -> bool:
    """Determine if we should skip LLM-based query splitting."""
    # If this is a follow-up to an active plan, don't re-split
    if state.get("plan_active", False):
        return True

    # If we have pending routes, this is part of an ongoing plan
    if state.get("pending_routes", []):
        return True

    # If query is simple (single task), don't split
    if not should_use_llm(query):
        return True

    return False


def summarize_messages(
        messages: list[BaseMessage],
) -> tuple[list[BaseMessage], str]:
    """
    Summarize older conversation history to keep message list short for LLM context.
    Returns (trimmed_messages, summary_text). The summary_text is intended to be
    injected only where needed (e.g., research agent), NOT into the messages list.
    """
    if len(messages) <= 6:
        return messages, ""

    try:
        recent_messages = messages[-3:]
        older_messages_text = "\n".join(
            [f"{type(msg).__name__}: {getattr(msg, 'content', '')}" for msg in messages[:-3]]
        )
        summarization_llm = _get_llm()
        summary_prompt = build_conversation_summary_prompt(older_messages_text)
        summary_response = summarization_llm.invoke(summary_prompt)
        summary_content = str(getattr(summary_response, "content", ""))
        return recent_messages, summary_content
    except Exception as e:
        logger.warning(f"Error summarizing messages, returning recent messages only: {e}")
        return messages[-3:], ""


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

    # Fast-path: handle greetings / introductions quickly without tools or extra LLM calls
    ql = (query or "").strip().lower()
    if ql and (re.match(r"^(hi|hello|hey)\b", ql) or re.search(r"\b(i am|i'm)\b", ql)):
        # Try to extract a name if the user introduced themselves
        name_match = re.search(
            r"\b(?:i am|i'm)\s+([A-Za-z][A-Za-z\s\.'-]{0,40})\b", query, flags=re.IGNORECASE
        )
        if name_match:
            name = name_match.group(1).strip().split()[0]
            reply = f"Nice to meet you, {name}! How can I help you today?"
        else:
            reply = "Hi! How can I help you today?"

        quick_msg = AIMessage(content=reply, tool_calls=[], response_metadata={})
        # Some downstream components expect a metadata attribute
        try:
            quick_msg.metadata = {}
        except Exception:
            pass

        final_messages = list(messages) + [quick_msg]
        return cast(
            CustomState,
            {
                **state,
                "messages": final_messages,
                "route": "__end__",
                "plan_active": False,
                "pending_routes": [],
                "routing_plan": [],
            },
        )

    # If a routing plan was just completed, generate the final response directly.
    if state.get("plan_active") and not state.get("routing_plan"):
        logger.info("Routing plan completed. Generating final response.")

        # 1. Get the LLM and prompt for final response synthesis.
        llm = _get_llm()
        prompt = build_final_response_prompt()
        response_chain = prompt | llm

        # 2. Sanitize the history to only include the user query and tool results.
        history = state.get("messages", [])
        user_query = next((msg for msg in history if isinstance(msg, HumanMessage)), None)
        tool_results = [msg for msg in history if isinstance(msg, ToolMessage)]
        clean_input = {"messages": [user_query] + tool_results}

        # 3. Invoke the chain to get the final answer.
        raw_response = response_chain.invoke(clean_input)

        # 4. Sanitize the final response and add the required metadata attribute for the streaming service.
        final_response = AIMessage(
            content=str(raw_response.content), tool_calls=[], response_metadata={}
        )
        final_response.tool_calls = []
        final_response.metadata = {}

        # 5. Update the state with the final message and signal the end.
        final_messages = list(messages) + [final_response]
        new_state = cast(
            CustomState,
            {
                **state,
                "messages": final_messages,
                "route": "__end__",
                "plan_active": False,
            },
        )
        if "tool_calls" in new_state:
            del new_state["tool_calls"]
        return new_state

    # Check if we should skip LLM-based splitting to reduce load
    if should_skip_llm_split(query, state):
        # If we already have a routing plan, dispatch the next sub-query to its agent
        existing_plan = cast(list[tuple[str, str]], state.get("routing_plan", [])) or []
        if existing_plan:
            next_agent, next_subq = existing_plan[0]
            remaining = existing_plan[1:]
            logger.info(f"Dispatching next task -> agent={next_agent}, subquery={next_subq}")
            # Add subquery as a HumanMessage so agent receives it as context
            new_messages = list(messages) + [HumanMessage(content=str(next_subq))]
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
            logger.info("Routing plan completed.")
            return cast(
                CustomState,
                {**state, "route": "__end__", "pending_routes": [], "plan_active": False},
            )

        # If the query is trivial (single task), route directly to the right agent
        if not should_use_llm(query):
            direct_route = pick_agent_for_subquery(query)
            logger.info(f"Trivial query detected. Direct route -> {direct_route}")
            return cast(CustomState, {**state, "route": direct_route, "pending_routes": []})

    # For complex queries, use LLM to split into sub-queries and build a routing plan
    router_llm = _get_llm()
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
    new_messages = list(messages) + [HumanMessage(content=str(next_subq))]
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
