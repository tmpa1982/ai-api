import logging

from langchain.chat_models import init_chat_model
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

graph_builder = StateGraph(InterviewState, input_schema=InterviewInputState)

llm = init_chat_model("openai:gpt-4o")

triage_agent = TriageAgent(llm)
interview_agent = InterviewAgent(llm)
evaluator_agent = EvaluatorAgent(llm)

graph_builder.add_node("interview_agent", interview_agent)
graph_builder.add_node("triage_agent", triage_agent)
graph_builder.add_node("evaluator_agent", evaluator_agent)

graph_builder.add_edge(START, "triage_agent")
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)