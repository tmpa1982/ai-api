from fastapi import APIRouter, Depends
from completion_request import CompletionRequest
from auth_utils import check_role
from llm_agents.langgraph_chatbot import ChatBotGraph
from langchain.chat_models import init_chat_model
import uuid

router = APIRouter()

llm = init_chat_model("openai:gpt-4o")
graph = ChatBotGraph(llm)

@router.post("/langgraph/question")
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))):
    user_email = user.get("preferred_username", "")
    thread_id = f"thread_{user_email}" if user_email else f"thread_{uuid.uuid4()}"
    result = graph.invoke(request.message, request.endInterview,thread_id)
    return {
        "message": result['messages'][-1].content,
        "evaluator_scorecard": result.get("evaluator_scorecard"),
        "thread_id": thread_id
    }
