import os

from logging_config import logging

from akv import AzureKeyVault
akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from completion_request import CompletionRequest

from auth_utils import check_role
from llm_agents.langgraph_chatbot import graph
from langchain_core.messages import HumanMessage

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite dev server
    "https://tran-llm-ui.azurewebsites.net",
]

import uuid
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

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

@app.post("/upload")
async def upload(user = Depends(check_role("APIUser"))):
    from vector_store import upload_files
    result = upload_files()
    return result

@app.post("/langgraph/question")
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))):
    result = graph.invoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "end_interview": request.endInterview,
            },
            config
        )
    return result['messages'][-1].content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
