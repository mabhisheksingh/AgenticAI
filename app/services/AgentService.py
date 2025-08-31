import logging
from typing import Any
import uuid
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph

from app.agents.LLMFactory import LLMFactory
from app.config.SqlLiteConfig import get_sql_lite_instance
from app.core.enums import LLMProvider
from app.core.errors import NotFoundError
from app.repositories.ThreadRepository import ThreadRepository
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
    def create_and_update_chat(
        cls, user_id: str, thread_id: UUID | None, message: str
    ) -> dict[str, Any]:
        logger.info("Creating and updating chat")
        llm = LLMFactory.create(LLMProvider.ollama)

        # response = llm.invoke(message)
        logger.info("Invoking llm")
        lg = LangGraphService(llm)
        response = lg.execute(message, thread_id, user_id)
        # logger.info("Response: %s", response)
        return response

    @classmethod
    def list_threads_by_session(cls, user_id: str) -> list[dict[str, Any]]:
        return ThreadRepository.get_session_by_id(user_id)

    @classmethod
    def delete_thread_by_session_and_id(cls, user_id: str, thread_id: str) -> int:
        return ThreadRepository.delete_by_session_and_thread(user_id, thread_id)


class LangGraphService:
    def __init__(self, llm):
        self.llm = llm
        # Compile the graph once per service instance and reuse
        builder = self._get_langgraph()
        self.graph = builder.compile(checkpointer=LangGraphService._get_sql_lite_memory())

    @staticmethod
    def _get_session_and_thread_config(thread_id: UUID | str, session_id: str) -> Any:
        config = {"configurable": {"thread_id": str(thread_id), "session_id": str(session_id)}}
        logger.info("Config: %s", config)
        return config

    # get sql lite checkpointer
    @staticmethod
    def _get_sql_lite_memory() -> SqliteSaver:
        sql_lite_instance = get_sql_lite_instance()
        memory = SqliteSaver(sql_lite_instance)
        return memory

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
        messages = []
        is_new_thread = thread_id is None
        if is_new_thread:
            thread_id = uuid.uuid4()
            # Persist mapping between session (user) and thread
            try:
                ThreadRepository.save(session_id=user_id, thread_id=str(thread_id))
            except Exception:
                # Do not break the flow if persistence fails; proceed without blocking chat
                logger.exception("Failed to persist session-thread mapping")
            messages.append(
                AIMessage(
                    content="Hey! You are a helpful assistant expert in Crime and Law",
                    name="assistant",
                )
            )
        else:
            row = ThreadRepository.get_by_session_and_thread(user_id, str(thread_id))
            if not row:
                raise NotFoundError("Thread not found or invalid thread id for this user")

        messages.append(HumanMessage(content=message))
        output = self.graph.invoke(
            {"messages": messages},
            config=LangGraphService._get_session_and_thread_config(thread_id, user_id),
        )
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
            # Fallbacks
            elif hasattr(output_messages, "content"):
                answer = to_plain_text(output_messages.content)  # type: ignore[attr-defined]
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
                "response": to_plain_text(str(output_messages)),
            }
