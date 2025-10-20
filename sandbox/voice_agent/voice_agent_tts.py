from kokoro import KPipeline
import numpy as np
import sounddevice as sd


class KokoroVoice:
    def __init__(self, voice: str, sample_rate: int = 24000, chunk_size: int = 2048):
        """Initialise the model to use for TTS.

        Args:
            voice (str):
                The voice to use.
                See https://github.com/hexgrad/kokoro/blob/main/kokoro.js/voices/
                for all voices.
            sample_rate (int, optional):
                The sample rate to use. Defaults to 24000.
            chunk_size (int, optional):
                The chunk size to use. Defaults to 2048.
        """
        self.voice = voice
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.initialise_model()

    def initialise_model(self):
        """Load the model to use for TTS."""
        self.pipeline = KPipeline(lang_code="b")

    def convert_text_to_speech(self, text: str) -> list[np.ndarray]:
        """Convert text to speech and return the waveform as frames."""
        generator = self.pipeline(text, voice=self.voice)
        frames = []
        for i, (_, _, audio) in enumerate(generator):
            for start in range(0, len(audio), self.chunk_size):
                chunk = audio[start : start + self.chunk_size]
                frames.append(np.array(chunk, dtype=np.float32))
        return frames

    def speak(self, text: str):
        """Play the generated speech audio."""
        frames = self.convert_text_to_speech(text)
        audio = np.concatenate(frames)
        sd.play(audio, self.sample_rate)
        sd.wait()
