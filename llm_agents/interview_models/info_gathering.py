from typing import Literal
from pydantic import BaseModel, Field

class infoGathering(BaseModel):
    "Model for collecting all the information before starting the interview simulation"

    interview_type: Literal["Technical", "Behavioral", "Case Study", "Hiring Manager"] = Field(
        description="Type of interview the user would like to simulate",
    ) 
    company_description: str = Field(
        description="Descripton the company you want to simulate the interview for",
    )
    job_description: str = Field(
        description="Description of the role you're applying for",
    )
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the necessary information",
    )
    verification: str = Field(
        description="Verify message that we will start interview after the user has provided the necessary information.",
    )
    