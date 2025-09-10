import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.pregel import Pregel

from app.ai_core.agents.code_agent import code_agent
from app.ai_core.agents.math_agent import math_agent
from app.ai_core.agents.nlp_formatting_agent import nlp_formatting_agent
from app.ai_core.agents.research_agent import research_agent
from app.ai_core.agents.router import router
from app.ai_core.tools.combined_tools import get_combined_tools
from app.repositories import DatabaseConnectionProvider
from app.schemas.custom_state import CustomState

logger = logging.getLogger(__name__)


def route_based_on_state(state: CustomState) -> str:
    """Determine the next node based on the route field in the state."""
    route = state.get("route", "research")
    logger.info(f"Routing based on state: {route}")
    return route


# Fix for Ollama model content format issue - ensure messages are properly formatted
def _ensure_message_content_format(state: CustomState) -> CustomState:
    """Ensure all messages in the state have properly formatted content for Ollama."""
    messages = state.get("messages", [])
    for msg in messages:
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            msg.content = [{"type": "text", "text": msg.content}]
        elif hasattr(msg, 'content') and isinstance(msg.content, list):
            # Check if any items in the list are strings that need to be converted
            for i, item in enumerate(msg.content):
                if isinstance(item, str):
                    msg.content[i] = {"type": "text", "text": item}
    state["messages"] = messages
    return state


# We are not using now inplace of router we are using supervisor_agent
class StateGraphObject:
    def __init__(self, llm: BaseChatModel, db_provider: DatabaseConnectionProvider):
        self.llm = llm
        self.tools = get_combined_tools()
        self._db_provider = db_provider
        self.checkpointer = self._get_sql_lite_memory()

    def _get_sql_lite_memory(self) -> SqliteSaver:
        sql_lite_instance = self._db_provider.get_connection()
        memory = SqliteSaver(sql_lite_instance)
        return memory

    def prepare_state_graph(self) -> Pregel:
        builder = StateGraph(CustomState)

        # ---- Sanitization wrappers to avoid empty messages in state ----
        def _content_to_text(content) -> str:
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict) and item.get("type") == "text":
                        parts.append(str(item.get("text", "")))
                    else:
                        parts.append(str(item))
                return " ".join([p for p in parts if p])
            return str(content)

        def _sanitize_state_update(update: CustomState) -> CustomState:
            try:
                msgs = list(update.get("messages", []))
            except Exception:
                return update
            sanitized = []
            for m in msgs:
                try:
                    has_tools = hasattr(m, "tool_calls") and bool(getattr(m, "tool_calls", []))
                    text = _content_to_text(getattr(m, "content", "")).strip()
                    if text or has_tools:
                        # Normalize list content to plain text for consistency downstream
                        if not text and has_tools:
                            # keep as-is to preserve tool call metadata
                            sanitized.append(m)
                        else:
                            try:
                                m.content = text
                            except Exception:
                                # If message is immutable, keep original
                                pass
                            sanitized.append(m)
                except Exception:
                    sanitized.append(m)
            update["messages"] = sanitized
            return update

        def code_node(state: CustomState) -> CustomState:
            out = code_agent.invoke(state)
            return _sanitize_state_update(out)

        def math_node(state: CustomState) -> CustomState:
            out = math_agent.invoke(state)
            return _sanitize_state_update(out)

        def research_node(state: CustomState) -> CustomState:
            out = research_agent.invoke(state)
            return _sanitize_state_update(out)

        # Register wrapped nodes
        builder.add_node("math", math_node)
        builder.add_node("code", code_node)
        builder.add_node("research", research_node)
        builder.add_node("router", router)
        builder.add_node("tools", ToolNode(self.tools))  # Add tools node
        builder.add_node("nlp_formatting", nlp_formatting_agent)

        # Add conditional routing - use a function that extracts the route from state
        builder.add_conditional_edges(
            "router",
            route_based_on_state,
            {
                "math": "math",
                "code": "code",
                "research": "research",
                "nlp_formatting": "nlp_formatting",
            },
        )

        # Add tool routing for the research agent
        # After tools are used, route back to the originating agent to continue processing
        builder.add_conditional_edges(
            "research", tools_condition, {"tools": "tools", END: "router"}
        )
        # The tools_condition function returns either "tools" or END
        builder.add_conditional_edges("math", tools_condition, {"tools": "tools", END: "router"})
        # The tools_condition function returns either "tools" or END
        builder.add_conditional_edges("code", tools_condition, {"tools": "tools", END: "router"})

        builder.add_edge("tools", "code")
        builder.add_edge("tools", "research")
        builder.add_edge("tools", "math")

        # Final formatting is triggered explicitly by the router when plan completes
        builder.add_edge("nlp_formatting", END)

        builder.add_edge(START, "router")
        graph = builder.compile(checkpointer=self.checkpointer)
        return graph