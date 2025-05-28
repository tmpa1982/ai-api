from agents import Agent, FileSearchTool
from utils import create_vector_store, upload_file
import sys
from pathlib import Path

# Add parent directory to path to allow imports from parent
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from prompts.voice_prompts import voice_system_prompt

vector_store_id = create_vector_store("Knowledge Base")
upload_file("Jia Yu Lee_CV.pdf", vector_store_id["id"])

knowledge_agent = Agent(
    name="KnowledgeAgent",
    instructions = voice_system_prompt + (
        "You answer user questions on my CV with concise, helpful responses using the FileSearchTool."
    ),
    tools=[FileSearchTool(
            max_num_results=3,
            vector_store_ids=[vector_store_id["id"]],
        ),],
)
