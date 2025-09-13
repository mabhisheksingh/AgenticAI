import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class CustomState(TypedDict, total=False):
    # Conversation content
    messages: Annotated[list[BaseMessage], add_messages]
    routes: Annotated[dict[str, str], operator.or_]  # subquery -> agent type
    subquery_results: list[str]
    done_queries: list[str]  # Track which queries have been processed

    summary: str
    subqueries: dict[str, str]  # subquery -> agent type
    # Routing fields (plan-and-dispatch)
    route: Literal["math", "code", "research", "__end__"]
    pending_routes: list[str]
    routing_plan: list[tuple[str, str]]  # [(agent, subquery)]
    plan_active: bool
    # New fields for multi-subquery orchestration

    # routes: dict[str, str]
    subquery_plan: list[dict[str, str]]  # [{"query": str, "agent": str}, ...]
    current_subquery_index: int
    current_subquery: str
    has_subqueries: bool
