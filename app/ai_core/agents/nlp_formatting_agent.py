from typing import Any

from langchain_core.messages import AIMessage


def _normalize_content(content: Any) -> str:
    """Convert LLM content to a clean string.

    Handles cases where content is a string, a list of strings/parts, or other structures.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # Handle common LangChain content dicts
                if "text" in item:
                    parts.append(str(item.get("text", "")))
                elif "content" in item:
                    parts.append(str(item.get("content", "")))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "\n".join([p for p in parts if p])
    # Fallback for other types
    return str(content)


def nlp_formatting_agent(state: dict) -> dict:
    """
    Formats the final response in a clear, natural language style for the user.
    Assumes the agent's answer is in the last message in state['messages'].
    """
    messages = state.get("messages", [])
    if not messages:
        return state
    last_message = messages[-1]
    # If already an AIMessage, just rephrase for clarity
    if isinstance(last_message, AIMessage):
        content = _normalize_content(last_message.content).strip()
        # Simple NLP formatting (could be replaced by LLM call for advanced formatting)
        formatted_content = f"Here's your answer: {content}"
        messages[-1] = AIMessage(content=formatted_content)
    else:
        # Wrap in AIMessage
        formatted_content = f"Here's your answer: {last_message!s}"
        messages.append(AIMessage(content=formatted_content))
    state["messages"] = messages
    return state
