from typing import Any

from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
import datetime
import os
load_dotenv()

@tool
def get_current_time() -> str:
    """Returns the current time as a string."""
    return datetime.datetime.now().strftime("%H:%M:%S")


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
   api_key = os.getenv("TAVILY_API_KEY")
   if not api_key:
       raise ValueError("TAVILY_API_KEY not found in environment variables")
   tavily_client  = TavilySearch(
    max_results=5,
    topic="general"
    )
   return tavily_client