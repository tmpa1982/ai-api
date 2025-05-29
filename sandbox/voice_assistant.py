# Not used in main.py but can be used to test the voice component

import os
import sys
import asyncio
import numpy as np
import sounddevice as sd
from pathlib import Path

# Add parent directory to path to allow imports from parent
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from agents.voice import TTSModelSettings, VoicePipeline, VoicePipelineConfig, SingleAgentVoiceWorkflow, AudioInput
from agents import trace
from triage_agent import triage_agent
from prompts.voice_prompts import voice_personality_prompt

from akv import AzureKeyVault

akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")


# Define custom TTS model settings with the desired instructions
custom_tts_settings=TTSModelSettings(instructions=voice_personality_prompt)

async def voice_assistant_optimized():
    # samplerate = int(sd.query_devices(kind='input')['default_samplerate'])
    samplerate = 28000
    voice_pipeline_config = VoicePipelineConfig(tts_settings=custom_tts_settings)

    while True:
        pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(triage_agent), config=voice_pipeline_config)

        # Check for input to either provide voice or exit
        cmd = input("Press Enter to speak your query (or type 'esc' to exit): ")
        if cmd.lower() == "esc":
            print("Exiting...")
            break      
        print("Listening...")
        recorded_chunks = []

         # Start streaming from microphone until Enter is pressed
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', callback=lambda indata, frames, time, status: recorded_chunks.append(indata.copy())):
            input()

        # Concatenate chunks into single buffer
        recording = np.concatenate(recorded_chunks, axis=0)

        # Input the buffer and await the result
        audio_input = AudioInput(buffer=recording)

        with trace("ACME App Voice Assistant"):
            result = await pipeline.run(audio_input)

         # Transfer the streamed result into chunks of audio
        response_chunks = []
        async for event in result.stream():
            if event.type == "voice_stream_event_audio":
                response_chunks.append(event.data)

        response_audio = np.concatenate(response_chunks, axis=0)

        # Play response
        print("Assistant is responding...")
        sd.play(response_audio, samplerate=samplerate)
        sd.wait()
        print("---")

# Run the voice assistant
if __name__ == "__main__":
    asyncio.run(voice_assistant_optimized())