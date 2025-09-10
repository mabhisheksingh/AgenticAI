from datetime import datetime
import logging
import re
from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.prompts.common_prompts import build_conversation_summary_prompt
from app.core.di_container import inject
from app.core.enums import LLMProvider
from app.schemas.custom_state import CustomState

logger = logging.getLogger(__name__)

# Simple cache to reduce repeated LLM calls
_query_cache = {}
_last_cache_cleanup = datetime.now()


def _cleanup_cache():
    """Clean up old cache entries to prevent memory issues."""
    global _last_cache_cleanup
    now = datetime.now()
    
    # Clean up cache every 10 minutes
    if (now - _last_cache_cleanup).total_seconds() > 600:
        # Remove entries older than 15 minutes
        cutoff_time = now.timestamp() - 900
        keys_to_remove = [
            key for key, (_, timestamp) in _query_cache.items()
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
        You are an expert at decomposing complex user queries into atomic sub-questions.
        Given the following user query, split it into a list of minimal, non-overlapping sub-questions, each suitable for a single specialized agent (math, code, research, etc.).
        Return ONLY the list, one per line, no extra commentary.
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
    messages: list[BaseMessage], llm_factory: LLMFactoryInterface
) -> list[BaseMessage]:
    """
    Summarize older conversation history to keep message list short for LLM context.
    Keeps the last 3 messages and summarizes the rest using a summarization LLM.
    """
    if len(messages) <= 6:
        return messages
    
    # Check if we already have a recent summary to avoid redundant summarization
    last_message = messages[-1] if messages else None
    if last_message and isinstance(last_message, AIMessage):
        last_content = getattr(last_message, 'content', '')
        if _content_starts_with(last_content, 'Summary of previous conversation:'):
            # If the last message is already a summary, we might not need to summarize again
            # unless the conversation has grown significantly
            if len(messages) <= 8:  # Allow a bit more before re-summarizing
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