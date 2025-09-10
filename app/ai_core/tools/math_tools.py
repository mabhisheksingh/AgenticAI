import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers together.

    This tool takes two numeric inputs (`a` and `b`) and returns their product.
    It works with both integers and floating-point numbers.

    Use this tool whenever the user asks to:
    - Multiply two numbers
    - Calculate a product
    - Perform scaling (e.g., "what is 3.5 times 7?")

    Args:
        a (float): The first number to multiply.
        b (float): The second number to multiply.

    Returns:
        float: The result of a * b.
    """
    logger.info(f"Tool called: multiply(a={a}, b={b})")
    result = a * b
    logger.info(f"Tool multiply result: {result}")
    return result


@tool
def add(a: float, b: float) -> float:
    """
    Add two numbers together.

    This tool takes two numeric inputs (`a` and `b`) and returns their sum.
    It supports both integers and floating-point numbers.

    Use this tool whenever the user asks to:
    - Add two numbers
    - Calculate a total or sum
    - Perform arithmetic like "5 plus 3"

    Args:
        a (float): The first number to add.
        b (float): The second number to add.

    Returns:
        float: The result of a + b.
    """
    logger.info(f"Tool called: add(a={a}, b={b})")
    result = a + b
    logger.info(f"Tool add result: {result}")
    return result


@tool
def divide(a: float, b: float) -> float:
    """
    Divide one number by another.

    This tool takes two numeric inputs (`a` and `b`) and returns the result of dividing `a` by `b`.
    It supports both integers and floating-point numbers.

    Use this tool whenever the user asks to:
    - Divide numbers
    - Find ratios or quotients
    - Solve problems like "10 divided by 2"

    Note:
        - If `b` is zero, the operation will raise an error (division by zero).

    Args:
        a (float): The numerator (number to be divided).
        b (float): The denominator (number to divide by).

    Returns:
        float: The result of a / b.
    """
    logger.info(f"Tool called: divide(a={a}, b={b})")
    result = a / b
    logger.info(f"Tool divide result: {result}")
    return result
