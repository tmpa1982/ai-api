import base64
import json
from fastapi import Request, HTTPException

def get_user_from_easy_auth(request: Request):
    header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    if not header:
        raise HTTPException(status_code=401, detail="No authentication header")

    decoded = base64.b64decode(header)
    decoded_json = json.loads(decoded)

    return {
        "identity_provider": decoded_json.get("identityProvider"),
        "user_id": decoded_json.get("userId"),
        "user_details": decoded_json.get("userDetails"),
        "claims": decoded_json.get("claims", []),
    }
