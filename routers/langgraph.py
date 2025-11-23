from fastapi import APIRouter, Depends
from dto.chat_response import ChatResponse
from dto.completion_request import CompletionRequest
from auth_utils import check_role
from llm_agents.chatbot_graph import ChatBotGraph
from langchain.chat_models import init_chat_model
from azure.identity.aio import DefaultAzureCredential
from azure.cosmos.aio import CosmosClient
from services.cosmos_checkpointer import CosmosDBSaver
import uuid

router = APIRouter()

llm = init_chat_model("openai:gpt-4o")

# Initialize Cosmos DB Client and Checkpointer
COSMOS_URL = "https://tranllmcosmos.documents.azure.com:443/"
DATABASE_NAME = "tranllm"
CONTAINER_NAME = "memory"

credential = DefaultAzureCredential()
client = CosmosClient(COSMOS_URL, credential=credential)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

checkpointer = CosmosDBSaver(container)
graph = ChatBotGraph(llm, checkpointer=checkpointer)

@router.post("/langgraph/question")
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))) -> ChatResponse:
    user_email = user.get("preferred_username", "")
    thread_id = f"thread_{user_email}" if user_email else f"thread_{uuid.uuid4()}"
    return graph.invoke(request.message, request.endInterview,thread_id)
