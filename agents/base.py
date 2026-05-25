# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import List

class AgentOutput(BaseModel):
    score: float = Field(..., ge=-1.0, le=1.0, description="Score from -1.0 (bearish) to +1.0 (bullish)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level from 0 to 1")
    summary: str = Field(..., description="A short summary of the agent's findings")
    evidence: List[str] = Field(..., description="Key bullet points of evidence supporting the score")

class BaseAgent:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self) -> AgentOutput:
        raise NotImplementedError("Each agent must implement the analyze method.")
