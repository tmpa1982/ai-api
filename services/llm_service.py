"""
LLM Service using LangChain agents.
"""

import os
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  
from langchain.chat_models import init_chat_model
from typing import Optional
from langchain.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

class LLMService:
    def __init__(self, api_key: str, model: str = "gpt-4", tools: Optional[list] = None, system_prompt: Optional[str] = None,
    cv_path: Optional[str] = None, website_path: Optional[str] = None
    ):
        """
        Initialize the LLM service with an agent.
        
        Args:
            api_key: OpenAI API key
            model: The model identifier (e.g., "gpt-4", "gpt-4o")
            tools: List of tools for the agent to use (optional)
            system_prompt: Custom system prompt for the agent (optional)
        """
        # Set API key in environment for LangChain to use
        # LangChain models read from OPENAI_API_KEY environment variable
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Format model name for LangChain (e.g., "gpt-4" -> "openai:gpt-4")
        model_name = f"openai:{model}" if not model.startswith("openai:") else model
        
        # Initialize the model
        self.model = init_chat_model(model_name, temperature=2)
        print(f"[LLM] Model initialized: {self.model}")

        # RAG tool example CV
        loader = PyPDFLoader(cv_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        all_splits = text_splitter.split_documents(docs)

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = InMemoryVectorStore(embedding=embeddings)
        document_ids = vector_store.add_documents(documents=all_splits)
        print(f"[LLM] Vector store created with {len(document_ids)} documents")

        @tool(response_format="content_and_artifact")
        def retrieve_CV(query: str):
            """Retrieve user's CV."""
            retrieved_docs = vector_store.similarity_search(query, k=2)
            print(f"[LLM] Retrieved {len(retrieved_docs)} documents")
            serialized = "\n\n".join(
                (f"Source: {doc.metadata}\nContent: {doc.page_content}")
                for doc in retrieved_docs
            )
            return serialized, retrieved_docs

        # @tool(response_format="content_and_artifact")
        # def retrieve_job_description(query: str):
        #     """Retrieve information from the website."""
        #     retrieved_docs = vector_store_website.similarity_search(query, k=2)
        #     print(f"[LLM] Retrieved {len(retrieved_docs)} documents")
        #     serialized = "\n\n".join(
        #         (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        #         for doc in retrieved_docs
        #     )
        #     return serialized, retrieved_docs

        self.tools = [retrieve_CV]

        # Load boc_job_description.md as a text
        with open("boc_job_description.md", "r", encoding="utf-8") as f:
            job_description_text = f.read()
        print("Job description loaded:", job_description_text[:50])
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = (
                f"""You are a helpful mock interviewer. You're task is
                 to simulate a mock interview with the candidate based
                 on the job description and company description and the type of interview.
                 If you need more information about the candidate CV use the retrieve_CV tool.
                    - Simulate the interview in character — respond as if you were the interviewer, before asking the next question.
                    - Don't list all questions in advance — just ask one at a time to mimic a real-life interview.
                 Keep your responses short and concise and conversational.

                 Here's the job description she is preparing for:
                 {job_description_text}
                """
            )
        
        # Create the agent
        self.agent = create_agent(self.model, self.tools, system_prompt=system_prompt, checkpointer=InMemorySaver())
    
    def generate_response(self, question: str, thread_id: Optional[str] = None) -> str:
        """
        Generate a response to a user question using the agent.
        
        Args:
            question: The user's question or message
            thread_id: Optional thread ID for conversation memory/context
            
        Returns:
            The agent's response as a string
        """
        try:
            print(f"[LLM] Processing question: {question[:50]}...")
            
            # Prepare the invoke arguments
            invoke_args = {"messages": [{"role": "user", "content": question}]}
            
            # If thread_id is provided, use it for memory/context
            if thread_id:
                result = self.agent.invoke(
                    invoke_args,
                    {"configurable": {"thread_id": thread_id}}
                )
            else:
                result = self.agent.invoke(invoke_args)
            
            # Always expect result["messages"] to exist and to be list of dicts
            last_message = result["messages"][-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            print(f"[LLM] Response generated: {response[:50]}...")
            return response
            
        except Exception as e:
            print(f"[LLM] Error: {e}")
            raise
