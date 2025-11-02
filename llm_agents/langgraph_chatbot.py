from typing import Literal
import logging

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, get_buffer_string
from langgraph.types import Command

from .interview_models import (
    InterviewState,
    InterviewInputState,
    InterviewProcess,
    EvaluatorScoreCard,
    infoGathering
)

logger = logging.getLogger(__name__)

graph_builder = StateGraph(InterviewState, input=InterviewInputState)


llm = init_chat_model("openai:gpt-4o")

def triage_agent(state: InterviewState) -> Command[Literal["interview_agent", "__end__"]]:

    logger.info("---TRIAGE AGENT---")

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

    REMEMBER:
    - Remember to be friendly and engaging but direct with the candidate. Be human-like so don't just jump in the first question.


    """

    prompt_content = TRIAGE_SYSTEM_PROMPT.format(
        messages=get_buffer_string(state["messages"]), 
    )

    triage_model = (
        llm
        .with_structured_output(infoGathering)
    )

    response = triage_model.invoke([HumanMessage(content=prompt_content)])

    if response.need_clarification:
        # End with clarifying question for user
        logger.info("ENDING WITH CLARIFYING QUESTION")
        logger.info("RESPONSE: %s", response)
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        # Proceed to interview stage
        logger.info("PROCEEDING TO INTERVIEW AGENT")
        logger.info("RESPONSE: %s", response)
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

    logger.info("---INTERVIEW AGENT---")

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

        Remember to be friendly and engaging but direct with the candidate. Be human-like so don't just jump in the first question.
    """

    interviewer_system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
        job_description=state["job_description"],
        company_description=state["company_description"],
        interview_type=state["interview_type"],
    )

    interviewer_model = (
        llm
        .with_structured_output(InterviewProcess)
        # could add retries, could bind tools here
    )


    messages = [SystemMessage(content=interviewer_system_prompt)] + state["messages"]
    # print("Messages as list:", messages)

    messages_str = get_buffer_string(messages)

    # print("Messages as string:", messages_str)

    response = interviewer_model.invoke([HumanMessage(content=messages_str)])

    # print("Structured response is:", response)

    if response.end_interview:
        # Proceed to evaluator stage
        logger.info("INTERVIEW ENDED, PROCEEDING TO EVALUATOR AGENT")
        return Command(
            goto="evaluator_agent", 
        )
    elif state['end_interview']:
        logger.info("INTERVIEW ENDED BY END INTERVIEW BUTTON, PROCEEDING TO EVALUATOR AGENT")
        return Command(
            goto="evaluator_agent", 
        )
    else:
        logger.info("NEXT INTERVIEW QUESTION")
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )

def evaluator_agent(state: InterviewState):

    logger.info("---EVALUATOR AGENT---")

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

        REMEMBER:
        - You're an objective evaluator of the interview, be direct and burtally honest. 
        - If the interview transcript is too short and lacking content, call it out as a poor interview, don't sugar code it.

        Here's the interview transcript (Human is the interviewee and AI is the interviewer):
    """

    evaluator_model = (
        llm
        .with_structured_output(EvaluatorScoreCard)
        # could add retries, could bind tools here
    )

    messages = [SystemMessage(content=EVALUATOR_SYSTEM_PROMPT)] + state["messages"]
    messages_str = get_buffer_string(messages)
    logger.debug("Messages: %s", messages_str)
    response = evaluator_model.invoke([HumanMessage(content=messages_str)])

    logger.info("Evaluator response: %s", response)

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