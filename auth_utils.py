from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

security = HTTPBearer()

TENANT_ID = "aa76d384-6e66-4f99-acef-1264b8cef053"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
JWKS_URL = f"{AUTHORITY}/discovery/v2.0/keys"
AUDIENCE = "6495a485-f811-440c-8e96-39d45f00aeab" # Application ID in Enterprise Applications
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

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
