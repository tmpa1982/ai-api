import logging
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, get_buffer_string
from langgraph.types import Command
from ..interview_models import InterviewState, InterviewProcess
from ..langgraph_chatbot import llm

logger = logging.getLogger(__name__)

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
    )

    messages = [SystemMessage(content=interviewer_system_prompt)] + state["messages"]
    messages_str = get_buffer_string(messages)

    response = interviewer_model.invoke([HumanMessage(content=messages_str)])

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
            goto="__end__", 
            update={"messages": [AIMessage(content=response.question)]}
        )
