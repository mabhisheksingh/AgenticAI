import logging

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.schemas.custom_state import CustomState
from app.utils.agent_utils import MATH_AGENT

load_dotenv()
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
)
logger = logging.getLogger(__name__)

_code_llm = init_chat_model(
    model=MATH_AGENT.model,
    model_provider=MATH_AGENT.model_provider,
    temperature=MATH_AGENT.temperature,
)
_math_agent = create_react_agent(
    model=_code_llm,
    tools=MATH_AGENT.tools,
    prompt=MATH_AGENT.prompt,
    name=MATH_AGENT.name,
)


def math_agent_node(state: CustomState) -> CustomState:
    logger.info("[MATH AGENT] Processing start")
    routes = state["routes"]
    remaining = [
        (query, agent)
        for query, agent in routes.items()
        if query not in state.get("done_queries", []) and agent == MATH_AGENT.name
    ]
    if not remaining:
        return state
    query, _ = remaining[0]
    llm_response = _math_agent.invoke({"messages": HumanMessage(content=query)})
    logger.info(f"[MATH AGENT] llm response: {llm_response}")
    result_text: str = llm_response["messages"][-1].content
    logger.info(f"[MATH AGENT] result_text: {result_text}")

    results = list(state.get("subquery_results", []))
    results.append(result_text)
    done = list(state.get("done_queries", []))
    done.append(query)

    logger.info("[MATH AGENT] Processing end")

    return {
        **state,
        "subquery_results": results,
        "done_queries": done,
    }
