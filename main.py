import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from completion_request import CompletionRequest

from agents import Runner, trace

from triage_agent import triage_agent
from akv import AzureKeyVault

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://tran-openai.openai.azure.com/",
    azure_ad_token_provider=token_provider,
)

akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/models")
async def list_models():
    return client.models.list().data

@app.post("/question")
async def ask_question(request: CompletionRequest):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that talks in piraty style.",
            },
            {
                "role": "user",
                "content": request.message,
            }
        ],
        model="gpt-4o-mini"
    )

    return response.choices[0].message.content

@app.post("/openai/question")
async def ask_question(request: CompletionRequest):
    with trace("Interview Prep Assistant"):
        result = await Runner.run(triage_agent, request.message)
        return result.final_output

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
