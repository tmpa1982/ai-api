from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import httpx
from auth_utils import check_role

router = APIRouter()

# These should be injected or imported from main, but for now, set as None
AZURE_SPEECH_KEY = None
AZURE_SPEECH_REGION = None

@router.get("/speech/token")
async def get_speech_token(user = Depends(check_role("APIUser"))):
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        raise HTTPException(status_code=500, detail="Speech key/region not configured")
    token_url = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, headers=headers, content="")
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to obtain speech token")
    return JSONResponse({
        "token": resp.text,
        "region": AZURE_SPEECH_REGION,
    })
