import logging

from langchain_core.language_models import BaseChatModel
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
        builder.add_node("math", math_agent)
        builder.add_node("code", code_agent)
        builder.add_node("research", research_agent)
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
        # The tools_condition function returns either "tools" or END
        builder.add_conditional_edges(
            "research", tools_condition, {"tools": "tools", END: "router"}
        )
        builder.add_edge("tools", "research")

        # Add tool routing for the code agent
        # The tools_condition function returns either "tools" or END
        builder.add_conditional_edges("code", tools_condition, {"tools": "tools", END: "router"})
        builder.add_edge("tools", "code")

        # Add tool routing for the math agent
        # The tools_condition function returns either "tools" or END
        builder.add_conditional_edges("math", tools_condition, {"tools": "tools", END: "router"})
        builder.add_edge("tools", "math")

        # Final formatting is triggered explicitly by the router when plan completes
        builder.add_edge("nlp_formatting", END)

        builder.add_edge(START, "router")
        graph = builder.compile(checkpointer=self.checkpointer)
        return graph
