import os

from logging_config import logging

from akv import AzureKeyVault
akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from completion_request import CompletionRequest

from auth_utils import check_role
from llm_agents.langgraph_chatbot import graph
from langchain_core.messages import HumanMessage

from storage_account import AzureStorageAccount

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite dev server
    "https://tran-llm-ui.azurewebsites.net",
]

import uuid

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response status: {response.status_code} for {request.method} {request.url}")
    return response

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/upload/vector_store")
async def upload_vector_store(user = Depends(check_role("APIUser"))):
    from vector_store import upload_files
    result = upload_files()
    return result

@app.post("/upload/storage_account")
async def upload_storage_account(
    file: UploadFile = File(...),
    user = Depends(check_role("APIUser"))
):
    container_name = "knowledgestore"
    try:
        data = await file.read()
        blob_prefix = "cv"
        blob_name = f"{blob_prefix}/{file.filename}"
        storage = AzureStorageAccount()
        storage.upload_file(container_name, blob_name, data)

        return {
            "status": "success",
            "container": container_name,
            "blob": blob_name,
            "size_bytes": len(data),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/langgraph/question")
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))):
    # Generate thread_id based on authenticated user's email
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
