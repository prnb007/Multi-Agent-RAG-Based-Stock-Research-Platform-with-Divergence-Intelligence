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

async def call_llm(
    system_prompt: str,
    user_prompt: str,
    schema_fallback: Optional[Dict] = None,
) -> dict:
    """
    Standard LLM call expecting JSON output.
    schema_fallback: pre-computed dict used verbatim when the LLM is
    unavailable, returns garbage, or the response is empty.
    """
    fallback = schema_fallback or {}
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt),
        ])
        chain = prompt | _llm
        response = await chain.ainvoke({})
        raw = response.content

        if not raw or len(raw.strip()) < 10:
            logger.warning("[LLM] Empty/minimal response — using pre-computed fallback")
            return fallback

        parsed = parse_llm_json(raw, fallback=fallback)

        # If both critical fields are missing the LLM gave us nothing useful
        if not parsed.get("summary") and parsed.get("score") is None:
            return fallback

        return parsed
    except Exception as e:
        logger.error(f"[LLM] call_llm exception: {e}")
        return fallback

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
