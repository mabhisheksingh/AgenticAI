import logging

from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.prompts.common_prompts import CODE_SYSTEM_PROMPT
from app.ai_core.tools.combined_tools import get_combined_tools
from app.core.di_container import inject
from app.core.enums import LLMProvider

logger = logging.getLogger(__name__)


# ---- Code Agent ----

_code_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CODE_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]
)

code_agent = create_react_agent(
    model=inject(LLMFactoryInterface).create_model(
        llm_provider_type=LLMProvider.LLM_LARGE_MODEL,
        with_tools=False,
    ),
    tools=get_combined_tools(),
    prompt=_code_prompt,
    name="code",
)

# def code_agent(state: CustomState) -> CustomState:
#     try:
#         # Extract the last human message as the query
#         query = ""
#         for message in reversed(state["messages"]):
#             if isinstance(message, HumanMessage):
#                 query = message.content
#                 break
#
#         if not query:
#             # Fallback to the query field if no human message found
#             query = state.get("query", "")
#
#         logger.info(f"Code agent processing query: {query}")
#
#         code_llm_factory = inject(LLMFactoryInterface)
#         code_llm = code_llm_factory.create_model(LLMProvider.LLM_LARGE_MODEL)
#
#         # Try with tools first, similar to the general agent
#         tools = get_combined_tools()
#         code_llm_with_tools = code_llm.bind_tools(tools)
#
#         # Create a proper message history for the LLM
#         messages = [HumanMessage(content=f"Write code for: {query}")]
#
#         try:
#             response = code_llm_with_tools.invoke(messages)
#         except Exception as e:
#             logger.warning(f"Code agent failed with tools, trying without tools: {e}")
#             # Fallback to invoking without tools
#             response = code_llm.invoke(f"Write code for: {query}")
#
#         # Properly extract content from the response
#         content = ""
#         if hasattr(response, "content"):
#             content = response.content
#             if isinstance(content, list):
#                 # If content is a list, join it into a string
#                 content = " ".join(str(item) for item in content)
#             elif not isinstance(content, str):
#                 # If content is not a string, convert it to string
#                 content = str(content)
#         else:
#             # If no content attribute, convert the entire response to string
#             content = str(response)
#
#         # Ensure we have content to return
#         if not content or not content.strip():
#             content = "I've processed your code request, but I don't have a specific response to provide."
#
#         logger.info(f"Code agent response: {content}")
#
#         # Create a new AIMessage with the response
#         ai_message = AIMessage(content=content)
#
#         # Return updated state with the new message and answer
#         # DO NOT include the query, route, or summary fields to avoid concurrent update errors
#         updated_messages = list(state["messages"]) + [ai_message]
#         result = {
#             "messages": updated_messages,
#             "answer": content,  # Add the answer field for streaming
#         }
#         logger.info(f"Code agent returning result: {result}")
#         return result
#     except Exception as e:
#         logger.error(f"Error in code agent: {e}", exc_info=True)
#         # Return a fallback response
#         error_message = "Sorry, I encountered an error while processing your code request."
#         ai_message = AIMessage(content=error_message)
#         updated_messages = list(state["messages"]) + [ai_message]
#         return {
#             "messages": updated_messages,
#             "answer": error_message,
#         }
