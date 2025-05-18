from azure.identity import DefaultAzureCredential, get_bearer_token_provider
# from openai import AzureOpenAI
from fastapi import FastAPI
from openai import OpenAI

from completion_request import CompletionRequest
from utils import create_vector_store, upload_file
import os


# agent sdk test
from agents import Agent, function_tool, WebSearchTool, FileSearchTool, set_default_openai_key, Runner, OpenAIChatCompletionsModel, trace
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from dotenv import load_dotenv

load_dotenv()


openai_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)

key_vault_url = "https://tran-akv.vault.azure.net/"

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
# client = AzureOpenAI(
#     api_version="2024-12-01-preview",
#     azure_endpoint="https://tran-openai.openai.azure.com/",
#     azure_ad_token_provider=token_provider,
# )

app = FastAPI()

# Configure the agent with Azure OpenAI
search_agent = Agent(
    name="SearchAgent",
    instructions=(
        "You immediately provide an input to the WebSearchTool to find up-to-date information on the user's query."
    ),
    tools=[WebSearchTool()],
)


vector_store_id = create_vector_store("Knowledge Base")
upload_file("Jia Yu Lee_CV.pdf", vector_store_id["id"])

# --- Agent: Knowledge Agent ---
knowledge_agent = Agent(
    name="KnowledgeAgent",
    instructions=(
        "You answer user questions on my CV with concise, helpful responses using the FileSearchTool."
    ),
    tools=[FileSearchTool(
            max_num_results=3,
            vector_store_ids=[vector_store_id["id"]],
        ),],
)


# --- Tool 1: Fetch account information (dummy) ---
@function_tool
def get_account_info(user_id: str) -> dict:
    """Return dummy account info for a given user."""
    return {
        "user_id": user_id,
        "name": "Bugs Bunny",
        "account_balance": "£72.50",
        "membership_status": "Gold Executive"
    }

# --- Agent: Account Agent ---
account_agent = Agent(
    name="AccountAgent",
    instructions=(
        "You provide account information based on a user ID using the get_account_info tool."
    ),
    tools=[get_account_info],
)

# --- Agent: Triage Agent ---
triage_agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions("""
You are the virtual assistant for Interview Prep. Welcome the user and ask how you can help.
Based on the user's intent, route to:
- KnowledgeAgent that stores my CV
- SearchAgent for anything requiring real-time web search
- AccountAgent for account-related queries
"""),
    handoffs=[account_agent, knowledge_agent, search_agent],
)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.post("/question")
async def ask_question(request: CompletionRequest):

    with trace("Interview Prep Assistant"):
        result = await Runner.run(triage_agent, request.message)
        return result.final_output


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
