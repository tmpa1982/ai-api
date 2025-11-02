import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from logging_config import logging
from akv import AzureKeyVault

akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

AZURE_SPEECH_KEY = akv.get_secret("azure-speech-key")
if not AZURE_SPEECH_KEY:
    raise ValueError("AZURE_SPEECH_KEY is not set in AKV")
AZURE_SPEECH_REGION = "eastasia"

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite dev server
    "https://tran-llm-ui.azurewebsites.net",
]

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

# Import routers
from routers import speech, upload, langgraph

# Inject config values into routers (simple assignment for now)
speech.AZURE_SPEECH_KEY = AZURE_SPEECH_KEY
speech.AZURE_SPEECH_REGION = AZURE_SPEECH_REGION

app.include_router(speech.router)
app.include_router(upload.router)
app.include_router(langgraph.router)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
