import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from logging_config import logging
from akv import AzureKeyVault

akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

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
from routers import speech, upload, langgraph, voice_agent

app.include_router(speech.router)
app.include_router(upload.router)
app.include_router(langgraph.router)
app.include_router(voice_agent.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
