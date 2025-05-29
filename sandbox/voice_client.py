import asyncio
import websockets
import sounddevice as sd
import numpy as np
import json
import threading
from queue import Queue

async def voice_client():
    uri = "ws://localhost:8000/openai/voice_stream"
    async with websockets.connect(uri) as websocket:
        # Send initial configuration
        samplerate = int(sd.query_devices(kind='input')['default_samplerate'])
        samplerate = 28000

        await websocket.send(json.dumps({"sample_rate": samplerate}))

        while True:
            # Wait for server ready signal
            response = await websocket.recv()
            status = json.loads(response)
            if status["status"] == "ready":
                print("\nPress Enter to start recording (or type 'exit' to quit):")
                user_input = input()
                if user_input.lower() == 'exit':
                    break

                print("Recording... Press Enter to stop.")
                recorded_chunks = []

                # Start recording
                def audio_callback(indata, frames, time, status):
                    recorded_chunks.append(indata.copy())

                with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', 
                                 callback=audio_callback):
                    input()  # Wait for Enter to stop recording

                # Send recorded audio
                for chunk in recorded_chunks:
                    await websocket.send(chunk.tobytes())
                await websocket.send(b"")  # Empty chunk to signal end of recording

                # Handle response
                response_chunks = []
                while True:
                    try:
                        msg = await websocket.recv()
                        if isinstance(msg, str):
                            status = json.loads(msg)
                            print(status["message"])
                            if status["status"] == "done":
                                break
                        else:
                            # Binary audio data
                            audio_chunk = np.frombuffer(msg, dtype='int16')
                            response_chunks.append(audio_chunk)
                    except websockets.ConnectionClosed:
                        break

                if response_chunks:
                    # Play response
                    response_audio = np.concatenate(response_chunks, axis=0)
                    sd.play(response_audio, samplerate=samplerate)
                    sd.wait()

if __name__ == "__main__":
    asyncio.run(voice_client()) 