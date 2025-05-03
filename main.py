from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

key_vault_url = "https://tran-akv.vault.azure.net/"

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://tran-openai.openai.azure.com/",
    azure_ad_token_provider=token_provider,
)

app = FastAPI()

TENANT_ID = "aa76d384-6e66-4f99-acef-1264b8cef053"
CLIENT_ID = "6495a485-f811-440c-8e96-39d45f00aeab"
AUDIENCE = CLIENT_ID
OPENID_CONFIG_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"

async def get_openid_config():
    async with httpx.AsyncClient() as client:
        resp = await client.get(OPENID_CONFIG_URL)
        return resp.json()

async def get_jwks():
    config = await get_openid_config()
    jwks_uri = config["jwks_uri"]
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_uri)
        return resp.json()

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    jwks = await get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    key = next(
        (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]),
        None
    )
    if key is None:
        raise HTTPException(status_code=403, detail="Invalid token header")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            options={"verify_aud": True}
        )
    except JWTError as e:
        raise HTTPException(status_code=403, detail=f"Token validation error: {str(e)}")

    return payload

def require_role(required_role: str):
    async def role_checker(user: dict = Depends(get_current_user)):
        roles = user.get("roles", [])
        if required_role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: Missing role")
        return user
    return role_checker

@app.get("/")
async def root(user=Depends(require_role("APIUser"))):
    return client.models.list().data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
