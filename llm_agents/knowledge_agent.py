from agents import Agent, FileSearchTool
from utils import create_vector_store, upload_file

vector_store = create_vector_store("Knowledge Base")
upload_file("Jia Yu Lee_CV.pdf", vector_store["id"])

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
