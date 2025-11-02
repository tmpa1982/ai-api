from fastapi import APIRouter, Depends
from completion_request import CompletionRequest
from auth_utils import check_role
from llm_agents.langgraph_chatbot import graph
from langchain_core.messages import HumanMessage
import uuid

router = APIRouter()

@router.post("/langgraph/question")
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))):
    user_email = user.get("preferred_username", "")
    thread_id = f"thread_{user_email}" if user_email else f"thread_{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(
        {
            "messages": [HumanMessage(content=request.message)],
            "end_interview": request.endInterview,
        },
        config
    )
    return {
        "message": result['messages'][-1].content,
        "evaluator_scorecard": result.get("evaluator_scorecard"),
        "thread_id": thread_id
    }
