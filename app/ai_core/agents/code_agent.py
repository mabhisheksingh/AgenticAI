import logging

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.schemas.custom_state import CustomState
from app.utils.agent_utils import CODE_AGENT
from app.utils.loging_utils import LOGGING_FORMAT

load_dotenv()
logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)

# ---- Code Agent ----

_code_llm = init_chat_model(
    model=CODE_AGENT.model,
    model_provider=CODE_AGENT.model_provider,
    temperature=CODE_AGENT.temperature,
)
_code_agent = create_react_agent(
    model=_code_llm,
    tools=CODE_AGENT.tools,
    prompt=CODE_AGENT.prompt,
    name=CODE_AGENT.name,
)


def code_agent_node(state: CustomState) -> CustomState:
    logger.info("[CODE AGENT] Processing start")
    routes = state["routes"]
    remaining = [
        (query,agent)
        for query, agent in routes.items()
        if query not in state.get("done_queries", []) and agent == CODE_AGENT.name
    ]
    if not remaining:
        return state
    query, _ = remaining[0]
    llm_response = _code_agent.invoke({"messages": HumanMessage(content=query)})
    logger.info(f"[CODE AGENT] llm response {llm_response}")
    result_text: str = llm_response["messages"][-1].content

    logger.info(f"[CODE AGENT] result_text: {result_text}")
    state["subquery_results"] = [result_text]

    results = list(state.get("subquery_results", []))
    results.append(result_text)
    done = list(state.get("done_queries", []))
    done.append(query)
    logger.info("[CODE AGENT] Processing end")
    return {
        **state,
        "subquery_results": results,
        "done_queries": done,
    }
