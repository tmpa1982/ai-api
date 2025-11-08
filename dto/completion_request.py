from pydantic import BaseModel, Field
from typing import Optional

class CompletionRequest(BaseModel):
    message: str
    endInterview: Optional[bool] = Field(False, description="Indicates whether the interview should be ended")
