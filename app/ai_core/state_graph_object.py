import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.pregel import Pregel

from app.ai_core.agents.code_agent import code_agent_node
from app.ai_core.agents.math_agent import math_agent_node
from app.ai_core.agents.new_router import router
from app.ai_core.agents.research_agent import research_agent_node
from app.ai_core.tools.combined_tools import get_combined_tools
from app.repositories import DatabaseConnectionProvider
from app.schemas.custom_state import CustomState

from app.utils.llm_utils import normalize_query

logger = logging.getLogger(__name__)


# We are not using now inplace of router we are using supervisor_agent
class StateGraphObject:
    def __init__(self, db_provider: DatabaseConnectionProvider):
        self.tools = get_combined_tools()
        self._db_provider = db_provider
        self.checkpointer = self._get_sql_lite_memory()

    def _get_sql_lite_memory(self) -> SqliteSaver:
        sql_lite_instance = self._db_provider.get_connection()
        memory = SqliteSaver(sql_lite_instance)
        return memory

    def prepare_state_graph(self) -> Pregel:
        builder = StateGraph(CustomState)

        # 1. Define all the nodes in the graph
        builder.add_node("router", router)
        builder.add_node("research", research_agent_node)
        builder.add_node("math", math_agent_node)
        builder.add_node("code", code_agent_node)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_node("format_results", self.format_results)

        builder.add_edge(START, "router")
        builder.add_conditional_edges(
            "router",
            # lambda state: [agent for _, agent in state.get("routes", {}).items()],
            lambda state, config=None: self.next_agent_router(state, config),
            {
                "research": "research",
                "math": "math",
                "code": "code",
                "__end__": "format_results",
            },
        )

        # builder.add_edge("code", "format_results")
        # builder.add_edge("research", "format_results")
        # builder.add_edge("math", "format_results")
        # builder.add_edge("format_results", END)

        builder.add_edge("research", "router")
        builder.add_edge("math", "router")
        builder.add_edge("code", "router")
        builder.add_edge("format_results", END)

        # 6. Compile the graph
        graph = builder.compile(checkpointer=self.checkpointer)
        return graph

    def next_agent_router(self, state: CustomState, config=None) -> str:
        """
        Decide which agent to call next, based on remaining subqueries.
        """
        routes = {normalize_query(q): agent for q, agent in state.get("routes", {}).items()}
        done = set(normalize_query(q) for q in state.get("done_queries", []))

        # Find the first unprocessed query
        for query, agent in routes.items():
            if query not in done:
                return agent

        # If all queries are done
        return "__end__"

    def format_results(self, state: CustomState) -> CustomState:
        results = state.get("subquery_results", {})
        logger.info("[FORMAT RESULTS] Processing end %s updated result ")
        state["messages"] = [AIMessage(content=results)]
        state["route"] = "__end__"  # <-- Add this line!
        logger.info("[FORMAT RESULTS] Processing end, result=%s", results)
        return state
