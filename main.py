import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from completion_request import CompletionRequest
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

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
security = HTTPBearer()

TENANT_ID = "aa76d384-6e66-4f99-acef-1264b8cef053"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
JWKS_URL = f"{AUTHORITY}/discovery/v2.0/keys"
AUDIENCE = "6495a485-f811-440c-8e96-39d45f00aeab" # Application ID in Enterprise Applications
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

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

# Cache for public keys
jwks = None

async def get_public_keys():
    global jwks
    if jwks is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL)
            resp.raise_for_status()
            jwks = resp.json()
    return jwks

async def verify_token(auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    keys = await get_public_keys()
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]
        key = next((k for k in keys["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found.")
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def check_role(required_role: str):
    async def role_checker(payload: dict = Depends(verify_token)):
        roles = payload.get("roles", [])
        if required_role not in roles:
            raise HTTPException(status_code=403, detail=f"Missing role: {required_role}")
        return payload
    return role_checker

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/models")
async def list_models():
    return client.models.list().data

@app.post("/question")
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))):
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
async def ask_question(request: CompletionRequest, user = Depends(check_role("APIUser"))):
    with trace("Interview Prep Assistant"):
        result = await Runner.run(triage_agent, request.message)
        return result.final_output

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
