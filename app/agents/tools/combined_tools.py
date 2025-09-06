from .math_tools import multiply, add, divide
from .utility_tools import get_current_time
from .duck_duck_go_tools import search_from_internet  # Commented out
import logging

logger = logging.getLogger(__name__)
def get_combined_tools():
    logger.info("Getting combined tools")
    combined_tools = []

    #combining math tools
    combined_tools.extend(get_math_tools())

    #combining utility tools
    combined_tools.extend(get_utility_tools())

    # Internet tools temporarily disabled
    combined_tools.extend(get_internet_tools())
    logger.info("Tools combined successfully")
    logger.debug("Combined tools: %s", combined_tools)
    return combined_tools


def get_math_tools():
    return [multiply,add,divide]

def get_utility_tools():
    return [get_current_time]

def get_internet_tools():
    return [search_from_internet]