from langchain_core.tools import tool
import datetime

@tool
def get_current_time() -> str:
    """Returns the current time as a string."""
    return datetime.datetime.now().strftime("%H:%M:%S")