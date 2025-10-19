#!/usr/bin/env python3
"""
Interactive CLI test for the LangGraph chatbot
"""

import sys
import os

# Add the parent directory to the path so we can import the chatbot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from akv import AzureKeyVault
akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

from llm_agents.langgraph_chatbot import graph
from langchain_core.messages import HumanMessage



# from dotenv import load_dotenv
# load_dotenv()

# if not os.getenv("OPENAI_API_KEY"):
#     loaded = load_dotenv()
#     if loaded and os.getenv("OPENAI_API_KEY"):
#         print("Loaded .env file and found OPENAI_API_KEY.")
#     else:
#         print("No OPENAI_API_KEY found in environment or .env file.")
# else:
#     print("OPENAI_API_KEY found in environment.")


def interactive_chat_test():
    """Interactive CLI test for the chatbot"""
    
    print("🤖 LangGraph Chatbot Interactive Test")
    print("=" * 50)
    print("Type your messages and press Enter to chat with the bot.")
    print("Type 'end' to signal end_interview to the bot for that turn.")
    print("Type 'quit' or 'exit' to end the test.")
    print("=" * 50)
    
    # Create config with thread_id for checkpointing
    config = {"configurable": {"thread_id": "interactive_test"}}
    
    try:
        while True:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye! Ending test.")
                break
            
            # Determine if this turn should end the interview
            end_flag = user_input.lower() == 'end'

            if not user_input and not end_flag:
                print("⚠️  Please enter a message.")
                continue
            
            # Send message to chatbot
            print("🤖 Bot is thinking...")
            
            result = graph.stream(
                {
                    "messages": [
                        HumanMessage(
                            content=("The interview has ended." if end_flag else user_input)
                        )
                    ],
                    "end_interview": end_flag,
                },
                config,
                stream_mode="messages"
            )
            
            # Get the last AI message from the stream
            last_ai_message = None
            for chunk, metadata in result:
                if hasattr(chunk, 'content') and chunk.content:
                    last_ai_message = chunk.content
                    print(f"🤖 Bot: {chunk.content}")
            
            if not last_ai_message:
                print("❌ No response from bot")
                
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    interactive_chat_test()
