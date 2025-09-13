import logging

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.schemas.custom_state import CustomState
from app.utils.agent_utils import RESEARCH_AGENT

load_dotenv()
logger = logging.getLogger(__name__)

# ---- research Agent ----
_research_llm = init_chat_model(
    model=RESEARCH_AGENT.model,
    model_provider=RESEARCH_AGENT.model_provider,
    temperature=RESEARCH_AGENT.temperature,
)
research_agent = create_react_agent(
    model=_research_llm,
    tools=RESEARCH_AGENT.tools,
    prompt=RESEARCH_AGENT.prompt,
    name=RESEARCH_AGENT.name,
)


def research_agent_node(state: CustomState) -> CustomState:
    """Wrapper node that injects summary only for research agent invocation.

    - Prepends a temporary SystemMessage with the conversation summary (if present).
    - Invokes the research_agent with this ephemeral context.
    - Appends only the agent's AIMessage to the state's messages.
    """
    # Get All remaining queries
    logger.info("[RESEARCH AGENT] Processing start")
    remaining = [
        (q, a) for q, a in state["routes"].items() if q not in state.get("done_queries", [])
    ]
    if not remaining:
        return state  # nothing left

    query, agent = remaining[0]
    if agent != "research":
        return state  # not our job

    # Invoke research agent
    llm_response = research_agent.invoke({"messages": HumanMessage(content=query)})
    logger.info("[RESEARCH AGENT] Processing end updated result ")
    # Normalize output
    result_text: str = llm_response["messages"][-1].content
    # Update state
    results = list(state.get("subquery_results", []))
    results.append(result_text)
    done = list(state.get("done_queries", []))
    done.append(query)
    return {
        **state,
        "subquery_results": results,
        "done_queries": done,
    }
