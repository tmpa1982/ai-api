from typing import Annotated, Optional
from langgraph.graph import MessagesState
from pydantic import Field
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class InterviewInputState(MessagesState):
    end_interview: Optional[bool] = Field(False, description="Indicates whether the interviewee press the end interview button")

class InterviewState(TypedDict):
    messages: Annotated[list, add_messages]
    interview_type: str
    company_description: str
    job_description: str
    triage_response: dict
    evaluator_scorecard: dict
    end_interview: Optional[bool] = Field(False, description="Indicates whether the interviewee press the end interview button")
