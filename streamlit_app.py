import streamlit as st
import requests

st.title("🤖 LangChain Chat Interface")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

# Handle user input
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Make API call
    try:
        response = requests.post(
            "http://localhost:8000/openai/langchain/question",
            json={"message": user_input}
        )
        response.raise_for_status()
        
        assistant_message = response.json()
        
        # Add assistant message to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_message["content"]
        })
        
        # Rerun to update the chat display
        st.rerun()
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with the API: {str(e)}")
        
# Add a sidebar with some information
with st.sidebar:
    st.markdown("### About")
    st.markdown("""
    This is a simple chat interface that connects to the LangChain endpoint.
    
    Make sure the FastAPI server is running on port 8000 before using this interface.
    """)
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun() 