
from utils.tools import fetch_interviewer_details
from langchain.agents import ToolNode

tool_node = ToolNode(
    tools=[fetch_interviewer_details],
    handle_tool_errors="I encountered an issue. Please try rephrasing your request."
)

if __name__ == "__main__":
    print(tool_node)