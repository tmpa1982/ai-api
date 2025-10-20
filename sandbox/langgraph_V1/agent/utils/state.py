from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import Field


class InterviewState(TypedDict):
    messages: Annotated[list, add_messages]
    interviewee_name: str
    interview_type: str
    company_description: str
    job_description: str
    end_interview: Optional[bool] = Field(default=False, description="Indicates whether the interviewee pressed the end interview button")