"""
Voice Agent Router - WebSocket endpoint for voice interaction.
"""

import json
import base64
import os
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.stt_service import STTService
from services.llm_service import LLMService
from services.tts_service import TTSService

router = APIRouter()

# Initialize services
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
stt_service = STTService(model_size='large-v3', device='cpu')
llm_service = LLMService(api_key=OPENAI_API_KEY, model="gpt-5-mini", cv_path="./cv.pdf")
tts_service = TTSService(api_key=OPENAI_API_KEY, voice="alloy")


@router.websocket("/ws")
async def voice_agent_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for voice interaction.
    
    Protocol:
    - Client sends: {"type": "audio_chunk", "data": "base64_audio"}
    - Client sends: {"type": "audio_end"} when done recording
    - Server sends: {"type": "audio_response", "data": "base64_audio"}
    """
    await websocket.accept()
    print("[WS] Client connected")
    
    # Session ID and audio buffer
    # Generate a unique session ID for this WebSocket connection for LLM memory
    session_id = f"voice_session_{uuid.uuid4()}"
    print(f"[WS] Session ID: {session_id}")
    audio_chunks = []
    
    try:
        while True:
            # Receive message
            message = json.loads(await websocket.receive_text())
            msg_type = message.get("type")
            
            if msg_type == "audio_chunk":
                # Receive and buffer audio chunk
                base64_audio = message.get("data")
                if not base64_audio:
                    print("[WS] Warning: Received audio_chunk with no data")
                    continue
                
                try:
                    audio_bytes = base64.b64decode(base64_audio)
                    if len(audio_bytes) == 0:
                        print("[WS] Warning: Decoded audio chunk is empty")
                        continue
                    
                    # Validate it looks like audio data (check for common audio headers)
                    # Only check first chunk to avoid performance issues
                    if len(audio_chunks) == 0 and len(audio_bytes) >= 4:
                        first_bytes = audio_bytes[:4]
                        # Check if it looks like valid audio (WebM, WAV, MP3, etc.)
                        is_valid = (
                            first_bytes[:4] == b'\x1a\x45\xdf\xa3' or  # WebM
                            first_bytes[:4] == b'RIFF' or  # WAV
                            (first_bytes[0] == 0xFF and (first_bytes[1] & 0xE0) == 0xE0) or  # MP3
                            first_bytes[:3] == b'ID3' or  # MP3 ID3
                            first_bytes[:4] == b'OggS' or  # OGG
                            first_bytes[:4] == b'fLaC'  # FLAC
                        )
                        if not is_valid:
                            # Check for known corrupted patterns (MediaRecorder not reset)
                            # This often happens on the first chunk but subsequent chunks are valid
                            if first_bytes[:4] == b'C\xc3\x81\x07' or first_bytes[:2] == b'C\xc3':
                                print(f"[WS] Warning [{session_id}]: Corrupted first chunk detected (hex: {first_bytes.hex()}). "
                                      f"This usually means MediaRecorder wasn't reset. Skipping this chunk and continuing...")
                                # Skip this corrupted chunk but don't send error to client yet
                                # If subsequent chunks are valid, the recording will still work
                                continue
                            else:
                                print(f"[WS] Warning [{session_id}]: First chunk doesn't look like valid audio. First 4 bytes (hex): {first_bytes.hex()}")
                                # Still add it - might be valid audio we don't recognize
                    
                    audio_chunks.append(audio_bytes)
                    print(f"[WS] Buffered chunk: {len(audio_bytes)} bytes (total chunks: {len(audio_chunks)})")
                except Exception as e:
                    print(f"[WS] Error decoding base64 audio chunk: {e}")
                    audio_chunks.clear()  # Clear on error
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Invalid audio data: {str(e)}"
                    })
            
            elif msg_type == "audio_end":
                # Process complete audio: STT → LLM → TTS
                print(f"[WS] Processing {len(audio_chunks)} chunks for session {session_id}...")
                
                if not audio_chunks:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No audio data received"
                    })
                    continue
                
                try:
                    # Combine all chunks
                    complete_audio = b''.join(audio_chunks)
                    
                    # Validate audio data
                    if len(complete_audio) < 100:  # Minimum reasonable audio size
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Audio too short: {len(complete_audio)} bytes"
                        })
                        audio_chunks.clear()
                        continue
                    
                    # Validate the combined audio has a valid header
                    if len(complete_audio) >= 4:
                        first_bytes = complete_audio[:4]
                        is_valid = (
                            first_bytes[:4] == b'\x1a\x45\xdf\xa3' or  # WebM
                            first_bytes[:4] == b'RIFF' or  # WAV
                            (first_bytes[0] == 0xFF and (first_bytes[1] & 0xE0) == 0xE0) or  # MP3
                            first_bytes[:3] == b'ID3' or  # MP3 ID3
                            first_bytes[:4] == b'OggS' or  # OGG
                            first_bytes[:4] == b'fLaC'  # FLAC
                        )
                        if not is_valid:
                            # Check for known corrupted pattern
                            if first_bytes[:4] == b'C\xc3\x81\x07' or first_bytes[:2] == b'C\xc3':
                                error_msg = (
                                    "Corrupted audio data detected. The MediaRecorder may not have been "
                                    "properly reset. Please stop and recreate the MediaRecorder before "
                                    "starting a new recording."
                                )
                                print(f"[WS] ERROR [{session_id}]: {error_msg}")
                                print(f"[WS] First 4 bytes (hex): {first_bytes.hex()}")
                                print(f"[WS] Total audio size: {len(complete_audio)} bytes, chunks: {len(audio_chunks)}")
                                audio_chunks.clear()
                                await websocket.send_json({
                                    "type": "error",
                                    "message": error_msg
                                })
                                continue
                            else:
                                print(f"[WS] Warning [{session_id}]: Combined audio doesn't have valid header. First 4 bytes (hex): {first_bytes.hex()}")
                                # Try to proceed anyway - STT service might handle it
                    
                    # Clear chunks immediately after combining (before processing)
                    # This prevents issues if processing fails
                    audio_chunks.clear()
                    
                    print(f"[WS] Combined audio: {len(complete_audio)} bytes (session: {session_id})")
                    
                    # Step 1: Speech-to-Text
                    transcript = stt_service.transcribe(complete_audio)
                    if not transcript:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Could not transcribe audio"
                        })
                        continue
                    
                    # Step 2: LLM Response (with session_id for memory)
                    response_text = llm_service.generate_response(transcript, thread_id=session_id)
                    
                    # Step 3: Text-to-Speech
                    audio_response = tts_service.synthesize(response_text)
                    
                    # Send audio response
                    audio_base64 = base64.b64encode(audio_response).decode('utf-8')
                    await websocket.send_json({
                        "type": "audio_response",
                        "data": audio_base64
                    })
                    print("[WS] Response sent")
                
                except Exception as e:
                    print(f"[WS] Error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            
            elif msg_type == "reset":
                # Reset conversation
                audio_chunks.clear()
                await websocket.send_json({
                    "type": "status",
                    "message": "Conversation reset"
                })
    
    except WebSocketDisconnect:
        print(f"[WS] Client disconnected")
    finally:
        # Cleanup
        audio_chunks.clear()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "voice_agent"}