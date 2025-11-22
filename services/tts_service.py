"""
Text-to-Speech Service using OpenAI TTS API.
"""

from openai import OpenAI
from kokoro import KPipeline
import numpy as np
import sounddevice as sd
import soundfile as sf


class TTSService:
    def __init__(self, voice: str = "af_heart"):
        self.voice = voice  # Save the desired voice name (kokoro)

    def synthesize(self, text: str) -> bytes:
        """Convert text to speech using Kokoro TTS pipeline."""
        if not text or text.strip() == "":
            raise ValueError("Text cannot be empty")
        try:
            print(f"[TTS] Synthesizing (kokoro): {text[:50]}...")

            # Create Kokoro pipeline, use lang_code as needed (e.g., 'a' for english)
            pipeline = KPipeline(lang_code='b')
            generator = pipeline(text, voice=self.voice)
            audio_chunks = []
            for i, (gs, ps, audio) in enumerate(generator):
                print(f"[TTS][Chunk {i}] Grapheme state: {gs[:20]}... | Phoneme state: {ps[:20]}..." if gs and ps else "[TTS][Chunk {i}] Emitting audio chunk")
                audio_chunks.append(audio)
            
            # Concatenate all audio chunks into a single array
            if not audio_chunks:
                raise RuntimeError("No audio generated from kokoro pipeline")
            
            # All chunks are numpy arrays; concatenate and write as wav to bytes
            audio_full = np.concatenate(audio_chunks)
            from io import BytesIO
            buf = BytesIO()
            sf.write(buf, audio_full, 24000, format='WAV')
            audio_bytes = buf.getvalue()
            print(f"[TTS] Generated {len(audio_bytes)} bytes (kokoro WAV)")
            return audio_bytes

        except Exception as e:
            print(f"[TTS] Error: {e}")
            raise
            print(f"[TTS] Generated {len(audio_bytes)} bytes")
            return audio_bytes