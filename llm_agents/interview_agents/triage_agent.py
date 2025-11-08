import logging
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.types import Command
from ..interview_models import InterviewState, infoGathering

logger = logging.getLogger(__name__)

class TriageAgent:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: InterviewState) -> Command[Literal["interview_agent", "__end__"]]:
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

        triage_model = self.llm.with_structured_output(infoGathering)

        response = triage_model.invoke([HumanMessage(content=prompt_content)])

        if response.need_clarification:
            # End with clarifying question for user
            logger.info("ENDING WITH CLARIFYING QUESTION")
            logger.info("RESPONSE: %s", response)
            return Command(
                goto="__end__",
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
