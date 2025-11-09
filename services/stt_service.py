"""
Speech-to-Text Service using OpenAI Whisper API.
"""

import tempfile
import os
from openai import OpenAI

class STTService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def transcribe(self, audio_bytes: bytes) -> str:
        """Convert audio bytes to text using Whisper API."""
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio bytes cannot be empty")
        
        temp_file = None
        try:
            # Detect audio format from magic bytes (file signature)
            # WebM starts with: 1A 45 DF A3
            # WAV starts with: 52 49 46 46 (RIFF)
            # MP3 starts with: FF FB or FF F3 or FF F2
            try:
                audio_format = self._detect_audio_format(audio_bytes)
            except ValueError as e:
                # If format detection fails, log detailed info and re-raise
                print(f"[STT] Format detection failed: {e}")
                print(f"[STT] First 50 bytes (hex): {audio_bytes[:50].hex()}")
                print(f"[STT] First 50 bytes (repr): {repr(audio_bytes[:50])}")
                raise
            
            suffix = f".{audio_format}"
            
            print(f"[STT] Using format: {audio_format}, size: {len(audio_bytes)} bytes")
            
            # Save audio to temporary file (Whisper requires file upload)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(audio_bytes)
            temp_file.flush()  # Ensure data is written
            temp_file.close()
            
            print(f"[STT] Transcribing {len(audio_bytes)} bytes...")
            
            # Transcribe with Whisper
            # Pass the file path directly - OpenAI SDK will handle it
            with open(temp_file.name, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            result = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            print(f"[STT] Result: {result}")
            return result
            
        except Exception as e:
            print(f"[STT] Error during transcription: {e}")
            # Log first few bytes for debugging
            if audio_bytes:
                print(f"[STT] First 20 bytes (hex): {audio_bytes[:20].hex()}")
            raise
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    print(f"[STT] Warning: Could not delete temp file: {e}")
    
    def _detect_audio_format(self, audio_bytes: bytes) -> str:
        """
        Detect audio format from file signature (magic bytes).
        
        Returns:
            Format string: 'webm', 'wav', 'mp3', 'm4a', etc.
        """
        if len(audio_bytes) < 4:
            raise ValueError(f"Audio data too short: {len(audio_bytes)} bytes")
        
        # Check magic bytes
        header = audio_bytes[:12]
        header_hex = header[:8].hex()
        
        # WebM: starts with 1A 45 DF A3 (EBML header)
        if header[:4] == b'\x1a\x45\xdf\xa3':
            print(f"[STT] Detected WebM format")
            return "webm"
        
        # WAV: starts with "RIFF" (52 49 46 46)
        if header[:4] == b'RIFF':
            print(f"[STT] Detected WAV format")
            return "wav"
        
        # MP3: starts with FF FB, FF F3, FF F2, or ID3 tag
        if header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
            print(f"[STT] Detected MP3 format")
            return "mp3"
        if header[:3] == b'ID3':
            print(f"[STT] Detected MP3 format (ID3 tag)")
            return "mp3"
        
        # M4A/MP4: starts with ftyp box (usually at offset 4)
        if len(audio_bytes) >= 8:
            if audio_bytes[4:8] == b'ftyp':
                print(f"[STT] Detected M4A/MP4 format")
                return "m4a"
        
        # OGG: starts with "OggS"
        if header[:4] == b'OggS':
            print(f"[STT] Detected OGG format")
            return "ogg"
        
        # FLAC: starts with "fLaC"
        if header[:4] == b'fLaC':
            print(f"[STT] Detected FLAC format")
            return "flac"
        
        # Check if this looks like corrupted or invalid data
        # Valid audio formats should have recognizable headers
        # If we can't detect it, the data might be corrupted
        raise ValueError(
            f"Invalid audio data: Could not detect format. "
            f"Header (hex): {header_hex}, "
            f"Header (first 12 bytes): {header}, "
            f"Size: {len(audio_bytes)} bytes. "
            f"This might be corrupted data or an unsupported format."
        )