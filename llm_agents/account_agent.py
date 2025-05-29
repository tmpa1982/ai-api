from agents import Agent, function_tool
import sys
from pathlib import Path

# Add parent directory to path to allow imports from parent
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from prompts.voice_prompts import voice_system_prompt


@function_tool
def get_account_info(user_id: str) -> dict:
    """Return dummy account info for a given user."""
    return {
        "user_id": user_id,
        "name": "Bugs Bunny",
        "account_balance": "£72.50",
        "membership_status": "Gold Executive"
    }

account_agent = Agent(
    name="AccountAgent",
    instructions = voice_system_prompt +(
        "You provide account information based on a user ID using the get_account_info tool."
    ),
    tools=[get_account_info],
)
