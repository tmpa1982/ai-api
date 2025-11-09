"""
Text-to-Speech Service using OpenAI TTS API.
"""

from openai import OpenAI

class TTSService:
    def __init__(self, api_key: str, voice: str = "onyx"):
        self.client = OpenAI(api_key=api_key)
        self.voice = voice
    
    def synthesize(self, text: str) -> bytes:
        """Convert text to speech using OpenAI TTS API."""
        if not text or text.strip() == "":
            raise ValueError("Text cannot be empty")
        
        try:
            print(f"[TTS] Synthesizing: {text[:50]}...")
            
            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1",  # tts-1
                voice=self.voice,
                input=text,
                response_format="mp3",
            )
            
            # Read audio bytes
            audio_bytes = response.read()
            print(f"[TTS] Generated {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            print(f"[TTS] Error: {e}")
            raise