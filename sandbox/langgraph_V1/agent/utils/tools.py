from langchain_core.tools import tool

# mock RAG tools
@tool
def fetch_interviewer_details(interviewee_name: str, query: str) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        interviewee_name: Name of the interviewee
    """
    return f"Adam has 3 years of experience in data analysis working at a investment back in Budapest Hungary. She also completed a coding bootcamp a year ago"