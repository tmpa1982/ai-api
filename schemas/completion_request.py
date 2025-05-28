from pydantic import BaseModel
import numpy as np
from typing import List

class CompletionRequest(BaseModel):
    message: str

class VoiceRequest(BaseModel):
    audio_data: List[int]
    sample_rate: int

    def to_numpy(self) -> np.ndarray:
        return np.array(self.audio_data, dtype='int16')
