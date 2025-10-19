from RealtimeSTT import AudioToTextRecorder
from voice_agent_tts import KokoroVoice
from typing import AsyncGenerator
import asyncio
import sys
import os


# Add the parent directory to the path so we can import the chatbot
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from akv import AzureKeyVault
akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

from langgraph_chatbot_dev import graph
from langchain_core.messages import HumanMessage



class OutputChunkBuilder:
    def __init__(self):
        self._msg = ""
        self.end_of_sentence = (".", "?", ";", "!", "\n")

    def add_chunk(self, message_chunk:str):
        self._msg += message_chunk

    def output_chunk_ready(self) -> bool:
        return self._msg.endswith(self.end_of_sentence)

    def _reset_message(self):
        self._msg = ""

    def get_output_chunk(self):
        msg = self._msg # Get the current message chunk
        self._reset_message()
        return msg

    def current_message_length(self) -> int:
        return len(self._msg)

# async def stream_voice(
#     msg_stream: AsyncGenerator,
#     output_chunk_builder: OutputChunkBuilder,
#     voice: KokoroVoice
# ):
#     """Stream messages from the agent to the voice output."""
#     if hasattr(msg_stream, "__aiter__"):
#         async for chunk, metadata in msg_stream:
#             if metadata["langgraph_node"] == "triage_agent":
#                 # build up message chunks until a full sentence is received.
#                 if chunk.content != "":
#                     output_chunk_builder.add_chunk(chunk.content)

#                 if output_chunk_builder.output_chunk_ready():
#                     voice.speak(output_chunk_builder.get_output_chunk())
#     else:
#         for chunk, metadata in msg_stream:
#             if metadata["langgraph_node"] == "triage_agent":
#                 # build up message chunks until a full sentence is received.
#                 if chunk.content != "":
#                     output_chunk_builder.add_chunk(chunk.content)

#                 if output_chunk_builder.output_chunk_ready():
#                     voice.speak(output_chunk_builder.get_output_chunk())

#     # if we have anything left in the buffer, speak it.
#     if output_chunk_builder.current_message_length() > 0:
#         voice.speak(output_chunk_builder.get_output_chunk())

def process_invoke_result(
    result,
    output_chunk_builder: OutputChunkBuilder,
    voice: KokoroVoice
):
    """Process the result from graph.invoke() and speak it."""
    if "messages" in result and result["messages"]:

        print(result['messages'])
        # Get the last message
        last_message = result['messages'][-1]
        
        # Check if it's an AI message with content
        if hasattr(last_message, 'content') and last_message.content and last_message.content.strip():
                # Add the content to the chunk builder
                output_chunk_builder.add_chunk(last_message.content)
                if output_chunk_builder.output_chunk_ready():
                    voice.speak(output_chunk_builder.get_output_chunk())

    # Speak any remaining content
    if output_chunk_builder.current_message_length() > 0:
        voice.speak(output_chunk_builder.get_output_chunk())


# class _Chunk:
#     """Simple container to mimic agent chunk objects with a content attribute."""
#     def __init__(self, content: str):
#         self.content = content


# async def mock_agent_stream(text: str) -> AsyncGenerator[tuple[_Chunk, dict], None]:
#     """Yield chunks of text with metadata to simulate a streaming agent response."""
#     # Split by spaces but include the space in the yielded content to simulate streaming
#     words = text.split(" ")
#     for i, word in enumerate(words):
#         content = word + (" " if i < len(words) - 1 else "")
#         yield _Chunk(content), {"langgraph_node": "agent"}
#         await asyncio.sleep(0.05)

voice = KokoroVoice(voice="af_heart")
output_chunk_builder = OutputChunkBuilder()


if __name__ == "__main__":

    async def main():
        import uuid
        config = {"configurable": {"thread_id": uuid.uuid4().hex}}

        with AudioToTextRecorder(
            model='tiny',
            device='cpu',
            post_speech_silence_duration=1.0
        ) as recorder:
            while True:
                # get the transcribed text from recorder
                query = recorder.text()
                print(query)
                if (query is not None) and (query != ""):

                    # mock response from agent
                    # response_text = "Hi there, Obi-wan Kenobi. Very nice to meet you!"
                    output = graph.invoke(
                        {
                            "messages": [
                                HumanMessage(
                                    content=(query)
                                )
                            ],
                            "end_interview": False,
                        },
                        config,
                    )
                    # output the response to device audio
                    process_invoke_result(output, output_chunk_builder, voice)

    asyncio.run(main())