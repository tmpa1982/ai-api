from typing import Optional
from pydantic import BaseModel, Field

class InterviewProcess(BaseModel):
    question: str = Field(
        description="Next question to ask the the interviewee",
    )
    end_interview: Optional[bool] = Field(
        description="Whether the user wishes to conclude the interview based on the latest message",
        default=False,
    )
