from typing import Optional

from pydantic import BaseModel

class ChatResponse(BaseModel):
    message: str
    thread_id: str
    evaluator_scorecard: Optional[dict] = None
