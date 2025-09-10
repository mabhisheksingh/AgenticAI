from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


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


def _format_response_content(content: str) -> str:
    """Format the response content to be more readable and structured."""
    # Remove the redundant "Here's your answer:" prefix if it already exists
    if content.startswith("Here's your answer:"):
        content = content[len("Here's your answer:"):].strip()
    
    # Clean up common formatting issues
    content = content.replace("{'type': 'text', 'text': '", "").replace("'}", "")
    content = content.replace("{'type': \"text\", 'text': \"", "").replace("\"}", "")
    
    # Handle numbered lists for better readability
    lines = content.split('\n')
    formatted_lines = []
    for line in lines:
        line = line.strip()
        if line:
            # If line looks like a numbered item, format it nicely
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                formatted_lines.append(f"\n{line}")
            else:
                formatted_lines.append(line)
    
    formatted_content = "\n".join(formatted_lines).strip()
    
    # If the content is already well-formatted, return as is
    if formatted_content.count('\n') > 2:  # Multi-line content
        return formatted_content
    else:
        # For single-line content, just return it without the prefix
        return formatted_content


def nlp_formatting_agent(state: dict) -> dict:
    """
    Formats the final response in a clear, natural language style for the user.
    Assumes the agent's answer is in the last message in state['messages'].
    """
    messages = state.get("messages", [])
    if not messages:
        return state
    
    # Convert all message contents to plain strings for consistency
    formatted_messages = []
    for message in messages:
        if isinstance(message, HumanMessage):
            formatted_messages.append(HumanMessage(content=_normalize_content(message.content)))
        elif isinstance(message, AIMessage):
            formatted_messages.append(AIMessage(content=_normalize_content(message.content)))
        elif isinstance(message, SystemMessage):
            formatted_messages.append(SystemMessage(content=_normalize_content(message.content)))
        else:
            # Fallback for unexpected message types
            content_str = _normalize_content(getattr(message, 'content', str(message)))
            try:
                message.content = content_str
                formatted_messages.append(message)
            except Exception:
                formatted_messages.append(HumanMessage(content=content_str))

    last_message = formatted_messages[-1]
    # If already an AIMessage, just rephrase for clarity
    if isinstance(last_message, AIMessage):
        content = _normalize_content(last_message.content).strip()
        # Format the content for better readability
        formatted_content = _format_response_content(content)
        formatted_messages[-1] = AIMessage(content=formatted_content)
    else:
        # Wrap in AIMessage
        content = _normalize_content(last_message.content if hasattr(last_message, 'content') else str(last_message))
        formatted_content = _format_response_content(content)
        formatted_messages.append(AIMessage(content=formatted_content))
    
    state["messages"] = formatted_messages
    return state