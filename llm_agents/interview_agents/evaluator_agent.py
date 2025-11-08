import logging
from langchain_core.messages import SystemMessage, HumanMessage, get_buffer_string
from ..interview_models import InterviewState, EvaluatorScoreCard

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: InterviewState) -> InterviewState:
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

        evaluator_model = self.llm.with_structured_output(EvaluatorScoreCard)

        messages = [SystemMessage(content=EVALUATOR_SYSTEM_PROMPT)] + state["messages"]
        messages_str = get_buffer_string(messages)
        logger.debug("Messages: %s", messages_str)
        response = evaluator_model.invoke([HumanMessage(content=messages_str)])

        logger.info("Evaluator response: %s", response)

        return {"evaluator_scorecard": response.model_dump(),
                "messages": [str(response.model_dump())]
                }
