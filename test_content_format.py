import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from langchain_core.messages import HumanMessage, AIMessage
from app.ai_core.agents.router import _ensure_content_format as router_ensure_content_format
from app.ai_core.agents.nlp_formatting_agent import _ensure_content_format as nlp_ensure_content_format

# Test cases
test_cases = [
    "Simple string content",
    ["List", "of", "strings"],
    [{"type": "text", "text": "Properly formatted content"}],
    [{"text": "Content without type"}],
    ["Mixed", {"type": "text", "text": "content"}, "types"]
]

print("Testing router _ensure_content_format:")
for i, test_case in enumerate(test_cases):
    result = router_ensure_content_format(test_case)
    print(f"Test {i+1}: {test_case} -> {result}")

print("\nTesting nlp_formatting_agent _ensure_content_format:")
for i, test_case in enumerate(test_cases):
    result = nlp_ensure_content_format(test_case)
    print(f"Test {i+1}: {test_case} -> {result}")

# Test with actual message objects
print("\nTesting with HumanMessage:")
human_msg = HumanMessage(content="Test message")
print(f"Before: {human_msg.content}")
human_msg.content = router_ensure_content_format(human_msg.content)
print(f"After: {human_msg.content}")

print("\nTesting with AIMessage:")
ai_msg = AIMessage(content=["Response", "parts"])
print(f"Before: {ai_msg.content}")
ai_msg.content = nlp_ensure_content_format(ai_msg.content)
print(f"After: {ai_msg.content}")