import logging
from typing import Annotated

logger = logging.getLogger(__name__)

from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_tavily import TavilySearch

tavily_tool = TavilySearch(max_results=5)

# Warning: This executes code locally, which can be unsafe when not sandboxed

repl = PythonREPL()


@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    logger.info(f"Tool called: python_repl_tool with code={code}")
    try:
        result = repl.run(code)
    except BaseException as e:
        logger.error(f"python_repl_tool failed: {e!r}")
        return f"Failed to execute. Error: {e!r}"
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    logger.info(f"python_repl_tool result: {result_str}")
    return result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
