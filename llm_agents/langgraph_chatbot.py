from typing import Annotated

from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, get_buffer_string
from langgraph.types import Command
from pydantic import BaseModel, Field
from typing import Annotated, Optional, Literal
import os

class InterviewInputState(MessagesState):
    """InputState is only 'messages'."""

class InterviewState(TypedDict):
    messages: Annotated[list, add_messages]
    interview_type: str
    company_description: str
    job_description: str
    triage_response: dict
    evaluator_scorecard: dict

class InterviewProcess(BaseModel):
    question: str = Field(
        description="Next question to ask the the interviewee",
    )
    end_interview: bool = Field(
        description="Whether the user wishes to conclude the interview based on the latest message",
        default=False,
    )

class EvaluatorScoreCard(BaseModel):
    communication_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Score for communication skills including clarity, articulation, confidence, and ability to explain complex concepts (1=Poor, 10=Excellent)",
    )
    technical_competency_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Score for technical knowledge, problem-solving ability, accuracy of answers, and depth of understanding (1=Poor, 10=Excellent)",
    )
    behavioural_fit_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Score for behavioral responses, cultural fit, leadership potential, teamwork, and situational handling (1=Poor, 10=Excellent)",
    )
    overall_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Overall interview performance score combining all dimensions (1=Poor, 10=Excellent)",
    )
    strengths: str = Field(
        description="Detailed description of the candidate's key strengths demonstrated during the interview",
        min_length=50,
    )
    areas_of_improvement: str = Field(
        description="Specific areas where the candidate can improve, with actionable recommendations",
        min_length=50,
    )

class infoGathering(BaseModel):
    "Model for collecting all the information before starting the interview simulation"

    interview_type: str = Field(
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

graph_builder = StateGraph(InterviewState, input=InterviewInputState)


llm = init_chat_model("openai:gpt-4o-mini")

def triage_agent(state: InterviewState) -> Command[Literal["interview_agent", "__end__"]]:

    print("---TRIAGE AGENT---")

    print(state)

    if 'triage_response' in state:
        if not state['triage_response']['need_clarification']:
            return Command(goto="interview_agent")


    TRIAGE_SYSTEM_PROMPT = """
    You are a career coach specializing in helping people prepare for job interviews.
    Your task is to collect the interview type, company description, and job description from the user before handing it off to the interview_agent to start the interview simulation.
    These are the messages that have been exchanged so far from the user asking for the interview preparation:
        <Messages>
        {messages}
        </Messages>

    """

    prompt_content = TRIAGE_SYSTEM_PROMPT.format(
        messages=get_buffer_string(state["messages"]), 
    )

    triage_model = (
        llm
        .with_structured_output(infoGathering)
    )

    response = triage_model.invoke([HumanMessage(content=prompt_content)])

    # print(response)

    if response.need_clarification:
        # End with clarifying question for user
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        # Proceed to interview stage
        return Command(
            goto="interview_agent", 
            update={"messages": [AIMessage(content=response.verification)],
                    "job_description": response.job_description,
                    "interview_type": response.interview_type,
                    "company_description": response.company_description,
                    "triage_response": response.model_dump(),
                   }
        )


def interview_agent(state: InterviewState) -> Command[Literal['evaluator_agent', '__end__']]:

    print("---INTERVIEW AGENT---")

    INTERVIEWER_SYSTEM_PROMPT = """
        You are a career coach specializing in helping people prepare for job interviews.
        Your task is to simulate a mock interview with the candidate based on the job description and company description and the type of interview.
        - Simulate the interview in character — respond as if you were the Interviewer, before asking the next question.
        - Don't list all questions in advance — just ask one at a time to mimic a real-life interview.

        Here is the job description:
        {job_description}

        Here is the company description:
        {company_description}

        Here is the type of interview:
        {interview_type}
    """

    interviewer_system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
        job_description=state["job_description"],
        company_description=state["company_description"],
        interview_type=state["interview_type"],
    )
    # print(interviewer_system_prompt)

    interviewer_model = (
        llm
        .with_structured_output(InterviewProcess)
        # could add retries, could bind tools here
    )


    messages = [SystemMessage(content=interviewer_system_prompt)] + state["messages"]
    # print("Messages as list:", messages)

    messages_str = get_buffer_string(messages)

    print("Messages as string:", messages_str)

    response = interviewer_model.invoke([HumanMessage(content=messages_str)])

    print("Structured response is:", response)

    if not response.end_interview:
    # End with next interview question for the user
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        # Proceed to evaluator stage
        return Command(
            goto="evaluator_agent", 
            # update={"messages": [AIMessage(content=response.verification)]}
        )

def evaluator_agent(state: InterviewState):

    print("---EVALUATOUR AGENT---")

    EVALUATOR_SYSTEM_PROMPT = f"""
        You are a career coach specializing in helping people prepare for job interviews.
        Your task is to evaluate the mock interview the user just completed and provide a helpful feedback to the user based on the scorecard.

        As a reminder: 
        The job description was:
        {state["job_description"]}

        The company description was:
        {state["company_description"]}

        And the type of interview was:
        {state["interview_type"]}
    """

    print(EVALUATOR_SYSTEM_PROMPT)

    evaluator_model = (
        llm
        .with_structured_output(EvaluatorScoreCard)
        # could add retries, could bind tools here
    )

    messages = [SystemMessage(content=EVALUATOR_SYSTEM_PROMPT)] + state["messages"]
    messages_str = get_buffer_string(messages)
    print(messages_str)
    response = evaluator_model.invoke([HumanMessage(content=messages_str)])

    print(response)

    return {"evaluator_scorecard": response.model_dump(),
            "messages": [str(response.model_dump())]
            }


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("interview_agent", interview_agent)
graph_builder.add_node("triage_agent", triage_agent)
graph_builder.add_node("evaluator_agent", evaluator_agent)

graph_builder.add_edge(START, "triage_agent")
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)