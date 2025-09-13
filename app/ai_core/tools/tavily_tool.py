import logging

logger = logging.getLogger(__name__)
from langchain_core.tools import tool
from langchain_tavily import TavilySearch


@tool
def tavily_web_search(query: str) -> str:
    """
    Searches the internet for up-to-date, real-time information.

    Use this tool for questions about current events, latest news, weather conditions, sports scores,
    stock prices, or any other query that requires information not available in the model's training data.

    Args:
        query: The specific search query for the internet.

    Returns:
        str: A summary of the search results from the internet.
    """
    logger.info(f"Tool called: search_the_web (tavily_search_tool) with query={query}")
    tavily_tool = TavilySearch(max_results=5)
    result = tavily_tool.invoke(query)
    logger.info(f"Tool tavily_web_search (tavily_tool) result: {result}")
    return result
