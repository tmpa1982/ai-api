import logging

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from llm_agents.interview_agents.evaluator_agent import EvaluatorAgent
from llm_agents.interview_agents.interview_agent import InterviewAgent
from llm_agents.interview_agents.triage_agent import TriageAgent

from .interview_models import (
    InterviewState,
    InterviewInputState,
)

logger = logging.getLogger(__name__)

class ChatBotGraph:
    def __init__(self, llm):
        graph_builder = StateGraph(InterviewState, input_schema=InterviewInputState)

        triage_agent = TriageAgent(llm)
        interview_agent = InterviewAgent(llm)
        evaluator_agent = EvaluatorAgent(llm)

        graph_builder.add_node("interview_agent", interview_agent)
        graph_builder.add_node("triage_agent", triage_agent)
        graph_builder.add_node("evaluator_agent", evaluator_agent)

        graph_builder.add_edge(START, "triage_agent")
        memory = InMemorySaver()
        self.graph = graph_builder.compile(checkpointer=memory)

    def invoke(self, message: str, terminate: bool, thread_id: str):
        result = self.graph.invoke(
            {
                "messages": [HumanMessage(content=message)],
                "end_interview": terminate,
            },
            {"configurable": {"thread_id": thread_id}},
        )
        return {
            "message": result['messages'][-1].content,
            "evaluator_scorecard": result.get("evaluator_scorecard"),
            "thread_id": thread_id
        }
