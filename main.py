import os
import numpy as np
import sounddevice as sd
from agents.voice import TTSModelSettings, VoicePipeline, VoicePipelineConfig, SingleAgentVoiceWorkflow, AudioInput
import json
from fastapi import WebSocket, WebSocketDisconnect

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from schemas.voice_request import VoiceRequest
from schemas.completion_request import CompletionRequest

from agents import Runner, trace
from auth import get_user_from_easy_auth
from triage_agent import triage_agent
from akv import AzureKeyVault
from prompts.voice_prompts import voice_personality_prompt


token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://tran-openai.openai.azure.com/",
    azure_ad_token_provider=token_provider,
)

akv = AzureKeyVault()
os.environ["OPENAI_API_KEY"] = akv.get_secret("openai-apikey")

app = FastAPI()
custom_tts_settings=TTSModelSettings(instructions=voice_personality_prompt)


origins = [
    "http://localhost:5173",  # Vite dev server
    "https://tran-llm-ui.azurewebsites.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/models")
async def list_models():
    return client.models.list().data

@app.post("/question")
async def ask_question(request: CompletionRequest, user = Depends(get_user_from_easy_auth)):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that talks in piraty style.",
            },
            {
                "role": "user",
                "content": request.message,
            }
        ],
        model="gpt-4o-mini"
    )

    return response.choices[0].message.content

@app.post("/openai/question")
async def ask_question(request: CompletionRequest, user = Depends(get_user_from_easy_auth)):
    with trace("Interview Prep Assistant"):
        result = await Runner.run(triage_agent, request.message)
        return result.final_output

@app.websocket("/openai/voice_stream")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get initial configuration from client
        config = await websocket.receive_json()
        voice_pipeline_config = VoicePipelineConfig(tts_settings=custom_tts_settings)
        samplerate = 28000
        print(f"Using sample rate: {samplerate}")
        
        while True:
            pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(triage_agent), config=voice_pipeline_config)
            
            # Send ready signal to client
            await websocket.send_json({"status": "ready", "message": "Ready to record"})
            
            # Receive audio chunks from client
            recorded_chunks = []
            while True:
                try:
                    # Receive chunk as binary data
                    chunk = await websocket.receive_bytes()
                    if not chunk:  # Empty chunk signals end of recording
                        break
                    # Convert bytes to numpy array
                    audio_chunk = np.frombuffer(chunk, dtype='int16')
                    recorded_chunks.append(audio_chunk)
                except WebSocketDisconnect:
                    return
            
            if recorded_chunks:
                # Concatenate chunks into single buffer
                recording = np.concatenate(recorded_chunks, axis=0)
                
                # Process audio
                audio_input = AudioInput(buffer=recording)
                
                with trace("ACME App Voice Assistant"):
                    result = await pipeline.run(audio_input)
                    
                    # Stream response audio back to client
                    await websocket.send_json({"status": "responding", "message": "Assistant is responding..."})
                    
                    async for event in result.stream():
                        if event.type == "voice_stream_event_audio":
                            # Send audio chunk as binary
                            await websocket.send_bytes(event.data.tobytes())
                    
                    # Signal end of response
                    await websocket.send_json({"status": "done", "message": "Response complete"})
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {str(e)}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
