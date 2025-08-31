import uuid
from typing import Any
from uuid import UUID
import logging

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from app.agents.LLMFactory import LLMFactory
from app.core.enums import LLMProvider
from app.utils.text import to_plain_text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class AgentService:


    def __init__(self):
        pass

    @classmethod
    def create_and_update_chat(cls, user_id: str, thread_id: UUID | None, message: str) -> dict[str, Any]:
        logger.info("Creating and updating chat")
        llm = LLMFactory.create(LLMProvider.ollama)

        # response = llm.invoke(message)
        logger.info("Invoking llm")
        lg = LangGraphService(llm)
        response = lg.execute(message, thread_id, user_id)
        # logger.info("Response: %s", response)
        return response


class LangGraphService:
    def __init__(self, llm):
        self.llm = llm
        pass

    # Node
    def _chat_model_node(self, state: MessagesState):
        # Ensure we append the generated AIMessage to the messages list
        return {"messages": [self.llm.invoke(state["messages"])]}

    def _get_langgraph(self) -> StateGraph:
        builder = StateGraph(MessagesState)
        builder.add_node("chat_model", self._chat_model_node)
        builder.add_edge(START, "chat_model")
        builder.add_edge("chat_model", END)
        return builder

    def execute(self, message: str, thread_id: UUID | None, user_id: str) -> dict[str, Any]:
        builder = self._get_langgraph()
        graph = builder.compile()
        messages = []
        is_new_thread = thread_id is None
        if is_new_thread:
            thread_id = uuid.uuid4()
            messages.append(AIMessage("Hey! Your are helpful assistant expert on Crime and Law", name="assistant"))

        messages.append(HumanMessage(content=message))
        output = graph.invoke({"messages": messages})
        output_messages = output["messages"]
        # Extract only the model's final text output
        try:
            last_ai = None
            for m in reversed(output_messages):
                if isinstance(m, AIMessage):
                    last_ai = m
                    break
            if last_ai is not None:
                answer = to_plain_text(last_ai.content)
            else:
                # Fallbacks
                if hasattr(output_messages, "content"):
                    answer = to_plain_text(getattr(output_messages, "content"))  # type: ignore[attr-defined]
                else:
                    answer = to_plain_text(str(output_messages))
            return {
                "threadId": thread_id,
                "userId": user_id,
                "message": message,
                "response": answer,
            }
        except Exception:
            return {
                "threadId": thread_id,
                "userId": user_id,
                "message": message,
                "response": to_plain_text(str(output_messages))
            }
