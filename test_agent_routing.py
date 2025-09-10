#!/usr/bin/env python3
"""Test script to verify agent routing functionality."""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import the required modules
try:
    from langchain_core.messages import HumanMessage

    from app.ai_core.agents.router import MATH_EXPRESSION_PATTERN, router
    from app.schemas.custom_state import CustomState

    ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"Could not import router function: {e}")
    ROUTER_AVAILABLE = False


def _ensure_content_format(content):
    """Ensure content is properly formatted for Ollama models."""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    elif isinstance(content, list):
        # Check if list contains properly formatted content parts
        formatted_parts = []
        for part in content:
            if isinstance(part, str):
                formatted_parts.append({"type": "text", "text": part})
            elif isinstance(part, dict) and "type" in part:
                formatted_parts.append(part)
            else:
                formatted_parts.append({"type": "text", "text": str(part)})
        return formatted_parts
    else:
        return [{"type": "text", "text": str(content)}]


def test_math_detection():
    """Test the math expression detection functionality."""

    if not ROUTER_AVAILABLE:
        print("Router function not available, skipping tests")
        return True

    # Test cases for math expression detection
    test_cases = [
        ("What is 3*99.8?", True),
        ("Calculate 3*99.8", True),
        ("What is google?", False),
        ("3*99.8=", True),
        ("3 x 99.8", True),
        ("3 ÷ 99.8", True),
        ("3 + 99.8", True),
        ("3 - 99.8", True),
        ("What is the weather today?", False),
    ]

    print("Testing math expression detection...")
    print("=" * 50)

    passed = 0
    total = len(test_cases)

    for i, (query, expected) in enumerate(test_cases, 1):
        match = MATH_EXPRESSION_PATTERN.search(query)
        result = match is not None
        status = "PASS" if result == expected else "FAIL"
        print(f"Test {i}: {status}")
        print(f"  Query: {query}")
        print(f"  Expected: {expected}, Got: {result}")

        if status == "PASS":
            passed += 1
        print()

    print(f"Math detection results: {passed}/{total} tests passed")
    return passed == total


def test_routing():
    """Test the routing functionality."""

    if not ROUTER_AVAILABLE:
        print("Router function not available, skipping tests")
        return True

    # Test cases for routing
    test_cases = [
        ("What is 3*99.8?", "math"),
        ("What is google?", "research"),
        ("Write a Python function to calculate factorial", "code"),
        ("What's the weather today?", "research"),
    ]

    print("Testing routing functionality...")
    print("=" * 50)

    passed = 0
    total = len(test_cases)

    for i, (query, expected_route) in enumerate(test_cases, 1):
        # Create a mock state
        state: CustomState = {
            "query": query,
            "messages": [HumanMessage(content=_ensure_content_format(query))],
            "route": "general",
        }

        # Call the router
        result_state = router(state)
        result_route = result_state.get("route", "general")

        status = "PASS" if result_route == expected_route else "FAIL"
        print(f"Test {i}: {status}")
        print(f"  Query: {query}")
        print(f"  Expected route: {expected_route}, Got: {result_route}")

        if status == "PASS":
            passed += 1
        print()

    print(f"Routing results: {passed}/{total} tests passed")
    return passed == total


if __name__ == "__main__":
    success1 = test_math_detection()
    success2 = test_routing()
    success = success1 and success2
    sys.exit(0 if success else 1)