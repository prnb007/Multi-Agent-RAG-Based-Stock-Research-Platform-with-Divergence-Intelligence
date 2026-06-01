# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from utils.parsing import parse_llm_json

load_dotenv()

logger = logging.getLogger(__name__)

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)

_AGENT_FALLBACK = {
    "score": 0.0,
    "confidence": 0.0,
    "summary": "Failed to parse LLM response",
    "evidence": [],
}

async def call_llm(system_prompt: str, user_prompt: str) -> dict:
    """
    Standard LLM call that expects JSON output.
    Returns parsed dict with keys: score, confidence, summary, evidence.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])
    chain = prompt | _llm
    response = await chain.ainvoke({})
    return parse_llm_json(response.content, fallback=_AGENT_FALLBACK)

class AgentOutput(BaseModel):
    agent: Optional[str] = Field(default=None, description="Name of the agent that produced this output")
    score: float = Field(..., ge=-1.0, le=1.0, description="Score from -1.0 (bearish) to +1.0 (bullish)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level from 0 to 1")
    summary: str = Field(..., description="A short summary of the agent's findings")
    evidence: List[str] = Field(..., description="Key bullet points of evidence supporting the score")
    raw_data: Optional[Dict] = Field(default=None, description="Optional extra data")

class BaseAgent:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self) -> AgentOutput:
        raise NotImplementedError("Each agent must implement the analyze method.")
