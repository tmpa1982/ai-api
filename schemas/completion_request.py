from pydantic import BaseModel
import numpy as np
from typing import List

class CompletionRequest(BaseModel):
    message: str
