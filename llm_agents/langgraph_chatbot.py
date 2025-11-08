import logging

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from .interview_models import (
    InterviewState,
    InterviewInputState,
)

logger = logging.getLogger(__name__)

graph_builder = StateGraph(InterviewState, input_schema=InterviewInputState)

llm = init_chat_model("openai:gpt-4o")

from .interview_agents import triage_agent, interview_agent, evaluator_agent

# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("interview_agent", interview_agent)
graph_builder.add_node("triage_agent", triage_agent)
graph_builder.add_node("evaluator_agent", evaluator_agent)

graph_builder.add_edge(START, "triage_agent")
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)