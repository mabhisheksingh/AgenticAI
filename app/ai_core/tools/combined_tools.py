import logging
import os

from dotenv import load_dotenv

from .duck_duck_go_tools import search_the_web
from .math_tools import add, divide, multiply
from .tavily_tool import tavily_web_search
from .utility_tools import get_current_time

logger = logging.getLogger(__name__)

load_dotenv()


def get_combined_tools():
    logger.info("Getting combined tools")
    combined_tools = []

    # combining math tools
    combined_tools.extend(get_math_tools())

    # combining utility tools
    combined_tools.extend(get_utility_tools())

    # Combining internet tools
    combined_tools.extend(get_internet_tools())
    logger.info("Tools combined successfully")
    logger.debug("Combined tools: %s", combined_tools)
    return combined_tools


def get_math_tools():
    return [multiply, add, divide]


def get_utility_tools():
    return [get_current_time]


def get_internet_tools():
    travily_api_key = os.getenv("TAVILY_API_KEY")
    search_the_web_tool = search_the_web
    if travily_api_key:
        search_the_web_tool = tavily_web_search
    return [search_the_web_tool, get_current_time]
