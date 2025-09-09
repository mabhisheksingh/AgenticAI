from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool


@tool
def search_the_web(query: str) -> str:
    """
      Searches the internet for up-to-date, real-time information.

      Use this tool for questions about current events, latest news, weather conditions, sports scores,
      stock prices, or any other query that requires information not available in the model's training data.

      Args:
          query: The specific search query for the internet.

      Returns:
          str: A summary of the search results from the internet.
      """
    ddg_tool = DuckDuckGoSearchResults(max_results=5)
    return ddg_tool.run(query)
