from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


def join_strings(left: str, right: str) -> str:
    """Reducer to join summary strings safely."""
    if not right:
        return left
    if not left:
        return right
    return left + " " + right


class CustomState(TypedDict, total=False):
    # Conversation content
    messages: Annotated[list[BaseMessage], add_messages]
    summary: Annotated[str, join_strings]

    # Routing fields (plan-and-dispatch)
    route: Literal["math", "code", "research", "nlp_formatting"]
    pending_routes: list[str]
    routing_plan: list[tuple[str, str]]  # [(agent, subquery)]
    plan_active: bool
