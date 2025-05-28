import os
import numpy as np
import sounddevice as sd
from agents.voice import AudioInput, SingleAgentVoiceWorkflow, VoicePipeline
import json
from fastapi import WebSocket, WebSocketDisconnect

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from completion_request import CompletionRequest, VoiceRequest

from agents import Runner, trace
from auth import get_user_from_easy_auth
from triage_agent import triage_agent
from akv import AzureKeyVault

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

@app.post("/openai/voice_question")
async def voice_question(request: VoiceRequest, user = Depends(get_user_from_easy_auth)):
    # Create pipeline with triage agent
    pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(triage_agent))
    
    # Use the audio data from the request
    audio_input = AudioInput(buffer=request.to_numpy())

    with trace("ACME App Voice Assistant"):
        result = await pipeline.run(audio_input)

        # Transfer the streamed result into chunks of audio
        response_chunks = []
        async for event in result.stream():
            if event.type == "voice_stream_event_audio":
                response_chunks.append(event.data)

        # Combine chunks into final response
        response_audio = np.concatenate(response_chunks, axis=0)
        
        # Return the audio data and sample rate to the client
        return {
            "audio_data": list(response_audio.flatten()),
            "sample_rate": request.sample_rate
        }

@app.websocket("/openai/voice_stream")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get initial configuration from client
        config = await websocket.receive_json()
        samplerate = config.get('sample_rate', 44100)
        
        while True:
            pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(triage_agent))
            
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
