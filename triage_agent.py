from agents import Agent
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from llm_agents.search_agent import search_agent
from llm_agents.knowledge_agent import knowledge_agent
from llm_agents.account_agent import account_agent

triage_agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions("""
You are the virtual assistant for Interview Preparation. Welcome the user and ask how you can help.
Based on the user's intent, route to:
- KnowledgeAgent that stores my CV
- SearchAgent for anything requiring real-time web search
- AccountAgent for account-related queries
"""),
    handoffs=[account_agent, knowledge_agent, search_agent],
)
