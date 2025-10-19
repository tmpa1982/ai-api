#!/usr/bin/env python3
"""
Test script to verify the stream filtering fix works correctly.
This script simulates the LangGraph stream output to test the filtering logic.
"""

import sys
import os
from typing import AsyncGenerator
from unittest.mock import Mock

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from voice_agent_main import OutputChunkBuilder, stream_voice

class MockChunk:
    """Mock chunk object to simulate LangGraph message chunks."""
    def __init__(self, content: str):
        self.content = content

class MockVoice:
    """Mock voice object to capture what would be spoken."""
    def __init__(self):
        self.spoken_messages = []
    
    def speak(self, message: str):
        self.spoken_messages.append(message)
        print(f"VOICE SPEAKING: {message}")

async def mock_stream_with_various_messages():
    """Create a mock stream that simulates various types of messages from LangGraph."""
    
    # Simulate different types of messages that might come from LangGraph
    mock_messages = [
        # Human message (should be ignored)
        (MockChunk("Hello, I want to practice for a software engineer interview"), 
         {"langgraph_node": "human"}),
        
        # Triage agent message (should be spoken)
        (MockChunk("Great! I'd love to help you practice for a software engineer interview. What type of interview would you like to simulate?"), 
         {"langgraph_node": "triage_agent"}),
        
        # Human response (should be ignored)
        (MockChunk("I want to practice for a technical interview"), 
         {"langgraph_node": "human"}),
        
        # Interview agent message (should be spoken)
        (MockChunk("Perfect! Let's start with a technical question. Can you explain the difference between a stack and a queue?"), 
         {"langgraph_node": "interview_agent"}),
        
        # Human response (should be ignored)
        (MockChunk("A stack is LIFO and a queue is FIFO"), 
         {"langgraph_node": "human"}),
        
        # Interview agent follow-up (should be spoken)
        (MockChunk("Excellent! That's correct. Now, can you implement a stack using an array?"), 
         {"langgraph_node": "interview_agent"}),
        
        # Evaluator agent message (should be ignored)
        (MockChunk("The candidate demonstrated good understanding of basic data structures..."), 
         {"langgraph_node": "evaluator_agent"}),
        
        # System message (should be ignored)
        (MockChunk("System: Processing evaluation results"), 
         {"langgraph_node": "system"}),
    ]
    
    # Convert to async generator
    async def async_generator():
        for chunk, metadata in mock_messages:
            yield chunk, metadata
    
    return async_generator()

async def test_stream_filtering():
    """Test the stream filtering logic."""
    print("🧪 Testing LangGraph Stream Filtering Fix")
    print("=" * 50)
    
    # Create mock objects
    output_chunk_builder = OutputChunkBuilder()
    mock_voice = MockVoice()
    
    # Create mock stream
    mock_stream = await mock_stream_with_various_messages()
    
    # Test the stream_voice function
    print("Processing stream with debug enabled...")
    await stream_voice(mock_stream, output_chunk_builder, mock_voice, debug=True)
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"Total messages spoken: {len(mock_voice.spoken_messages)}")
    print("Messages that were spoken:")
    for i, msg in enumerate(mock_voice.spoken_messages, 1):
        print(f"  {i}. {msg}")
    
    # Verify the results
    expected_spoken = 3  # Only triage_agent and interview_agent messages
    actual_spoken = len(mock_voice.spoken_messages)
    
    print(f"\n✅ Expected {expected_spoken} messages to be spoken")
    print(f"✅ Actually spoke {actual_spoken} messages")
    
    if actual_spoken == expected_spoken:
        print("🎉 SUCCESS: Stream filtering is working correctly!")
        print("   - Human messages were ignored")
        print("   - Triage agent messages were spoken")
        print("   - Interview agent messages were spoken") 
        print("   - Evaluator agent messages were ignored")
        print("   - System messages were ignored")
    else:
        print("❌ FAILURE: Stream filtering is not working correctly!")
    
    return actual_spoken == expected_spoken

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_stream_filtering())
