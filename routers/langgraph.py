from fastapi import APIRouter, Depends
from dto.chat_response import ChatResponse
from dto.completion_request import CompletionRequest
from auth_utils import check_role
from llm_agents.langgraph_chatbot import ChatBotGraph
from langchain.chat_models import init_chat_model
import uuid

router = APIRouter()

llm = init_chat_model("openai:gpt-4o")
graph = ChatBotGraph(llm)

@router.post("/langgraph/question")
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))) -> ChatResponse:
    user_email = user.get("preferred_username", "")
    thread_id = f"thread_{user_email}" if user_email else f"thread_{uuid.uuid4()}"
    return graph.invoke(request.message, request.endInterview,thread_id)
