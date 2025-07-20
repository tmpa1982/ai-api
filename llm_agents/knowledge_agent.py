from agents import Agent, FileSearchTool
from vector_store import vector_store

knowledge_agent = Agent(
    name="KnowledgeAgent",
    instructions=(
        "You answer user questions on my CV with concise, helpful responses using the FileSearchTool."
    ),
    tools=[FileSearchTool(
            max_num_results=3,
            vector_store_ids=[vector_store["id"]],
        ),],
)
