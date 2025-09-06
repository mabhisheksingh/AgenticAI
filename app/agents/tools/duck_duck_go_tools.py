from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool


@tool
def search_from_internet(query: str) -> str:
    """Search the internet for latest information using DuckDuckGo.
    
    Args:
        query: The search query to look up on the internet
        
    Returns:
        str: Search results from DuckDuckGo
    """
    ddg_tool = DuckDuckGoSearchResults(max_results=5)
    return ddg_tool.run(query)
