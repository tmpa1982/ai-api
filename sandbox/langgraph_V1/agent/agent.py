from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field
####################################
from dotenv import load_dotenv
import os
import sys
load_dotenv()
sys.path.append(os.path.dirname((os.path.abspath(__file__))))

from utils.nodes import tool_node
from utils.state import InterviewState
from langchain_core.messages import SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver


if __name__ == "__main__":

    agent = create_agent(
        model="openai:gpt-4o",
        tools=tool_node,
        prompt=SystemMessage(content="""You are mock interview assisstant. Your goal is to run a mock interview with the user.
     Before starting always fetch the user information using the 'fetch_interviewer_details' tool and tailor the some of the questions based on the interviewee detail. """),
        checkpointer=InMemorySaver(),
    )

    # The system prompt will be set dynamically based on context
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Hi, my name is Adam, I would like to run a mock interview. I would like to prepare for a data anayst role for Morgan stanley. Let's try a technical type interview."}]},
        {"configurable": {"thread_id": "1"}},
    )
    # result["messages"][-1].pretty_print()
    for msg in result['messages']:
        msg.pretty_print()