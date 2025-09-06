from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.pregel import Pregel
from langgraph.prebuilt import ToolNode, tools_condition
import logging
from app.agents.tools.combined_tools import get_combined_tools
from app.repositories import DatabaseConnectionProvider

logger = logging.getLogger(__name__)


class StateGraphObject:
    def __init__(self, llm: BaseChatModel, db_provider: DatabaseConnectionProvider):
        self.llm = llm
        self.tools = get_combined_tools()
        self._db_provider = db_provider
        self.checkpointer = self._get_sql_lite_memory()
        pass

    def _get_sql_lite_memory(self) -> SqliteSaver:
        sql_lite_instance = self._db_provider.get_connection()
        memory = SqliteSaver(sql_lite_instance)
        return memory

    # Node for sync/hybrid approach
    def assistant_node(self, state: MessagesState) -> dict[str, list[BaseMessage]]:
        logger.info("Calling assistant node")
        logger.info("State: %s", state)
        return {"messages": [self.llm.invoke(state["messages"])]}

    def prepare_state_graph(self) -> Pregel:
        builder = StateGraph(MessagesState)
        builder.add_node("assistant", self.assistant_node)
        builder.add_node("tools", ToolNode(self.tools))

        builder.add_conditional_edges(
            "assistant",
            # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
            # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
            tools_condition,
        )

        builder.add_edge(START, "assistant")
        builder.add_edge("assistant", END)
        graph = builder.compile(checkpointer=self.checkpointer)
        return graph
