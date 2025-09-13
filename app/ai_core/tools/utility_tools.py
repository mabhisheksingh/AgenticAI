import datetime
import logging

from dotenv import load_dotenv
from langchain_core.tools import tool

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
