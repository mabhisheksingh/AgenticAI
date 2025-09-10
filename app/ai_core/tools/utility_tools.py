import datetime
import logging
import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

load_dotenv()
logger = logging.getLogger(__name__)


@tool
def get_current_time() -> str:
    """
    Get the current system time in 24-hour format (HH:MM:SS).

    Use this tool if the user asks:
    - "What time is it now?"
    - "Tell me the current/local/system time"
    - "Give me the exact time right now"
    - or any variation of asking for the **present moment's time**.

    Returns:
        str: The current system time as a formatted string (HH:MM:SS).
    """
    logger.info("Tool called: get_current_time")
    result = datetime.now().strftime("%H:%M:%S")
    logger.info(f"Tool get_current_time result: {result}")
    return result


@tool
def search_the_web() -> Any:
    """
    Searches the internet for up-to-date, real-time information.

    Use this tool for questions about current events, latest news, weather conditions, sports scores,
    stock prices, or any other query that requires information not available in the model's training data.

    Args:
        query: The specific search query for the internet.

    Returns:
        str: A summary of the search results from the internet.
    """
    logger.info("Tool called: search_the_web (utility_tools)")
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not found in environment variables")
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    tavily_client = TavilySearch(max_results=5, topic="general")
    logger.info("Tool search_the_web (utility_tools) returning tavily_client instance")
    return tavily_client
