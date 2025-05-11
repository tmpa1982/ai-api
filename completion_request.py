from pydantic import BaseModel

class CompletionRequest(BaseModel):
    message: str
