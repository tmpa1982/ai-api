from agents import Agent, WebSearchTool
import sys
from pathlib import Path

# Add parent directory to path to allow imports from parent
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from prompts.voice_prompts import voice_system_prompt

search_agent = Agent(
    name="SearchAgent",
    instructions = voice_system_prompt + (
        "You immediately provide an input to the WebSearchTool to find up-to-date information on the user's query."
    ),
    tools=[WebSearchTool()],
)
