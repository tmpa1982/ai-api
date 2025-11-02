from typing import Literal
from pydantic import BaseModel, Field

class EvaluatorScoreCard(BaseModel):
    communication_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Score for communication skills including clarity, articulation, confidence, and ability to explain complex concepts (1=Poor, 10=Excellent)",
    )
    technical_competency_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Score for technical knowledge, problem-solving ability, accuracy of answers, and depth of understanding (1=Poor, 10=Excellent)",
    )
    behavioural_fit_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Score for behavioral responses, cultural fit, leadership potential, teamwork, and situational handling (1=Poor, 10=Excellent)",
    )
    overall_score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="Overall interview performance score combining all dimensions (1=Poor, 10=Excellent)",
    )
    strengths: str = Field(
        description="Detailed description of the candidate's key strengths demonstrated during the interview",
        min_length=50,
    )
    areas_of_improvement: str = Field(
        description="Specific areas where the candidate can improve, with actionable recommendations",
        min_length=50,
    )
