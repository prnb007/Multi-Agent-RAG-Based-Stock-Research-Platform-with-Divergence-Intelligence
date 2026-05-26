"""
Uses Groq LLM to extract 7 standardized signals from MD&A text.
One LLM call per quarter per ticker.
"""

import json
import logging
import os
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.0,
)

SYSTEM_PROMPT = """You are a financial NLP analyst specializing in SEC filing analysis.
Extract exactly 7 standardized signals from the MD&A text provided.
Return ONLY a valid JSON object with no markdown, no explanation.

Signal definitions:
- management_tone: Overall executive tone. Must be exactly: "optimistic" | "cautious" | "defensive"
- margin_language: How management discusses margins/profitability. Exactly: "expanding" | "stable" | "pressured"
- ai_monetization: How much AI revenue language appears. Exactly: "strong" | "emerging" | "absent"
- demand_signals: Customer demand language. Exactly: "strong" | "mixed" | "weak"
- hiring_language: Workforce discussion. Exactly: "expanding" | "stable" | "freezing"
- regulatory_concern: Regulatory risk language frequency. Exactly: "high" | "moderate" | "low"
- recurring_concerns: List of exactly 3 specific phrases or themes management seems worried about
- key_quotes: List of exactly 2 verbatim short quotes (under 20 words each) that best represent management tone
- confidence: Float 0.0-1.0 representing how much relevant text was available (1.0 = rich MD&A, 0.3 = sparse)

Return this exact JSON shape:
{
  "management_tone": "optimistic",
  "margin_language": "expanding",
  "ai_monetization": "strong",
  "demand_signals": "strong",
  "hiring_language": "stable",
  "regulatory_concern": "moderate",
  "recurring_concerns": ["concern 1", "concern 2", "concern 3"],
  "key_quotes": ["quote 1 under 20 words", "quote 2 under 20 words"],
  "confidence": 0.85
}"""


async def extract_signals(
    ticker: str,
    quarter: str,
    mda_text: str
) -> dict:
    """
    Extract narrative signals from MD&A text using Groq LLM.
    Returns dict with all 7 signals.
    """
    if not mda_text or len(mda_text) < 500:
        logger.warning(
            f"[Extractor] {ticker} {quarter}: MD&A too short "
            f"({len(mda_text)} chars), returning defaults"
        )
        return _default_signals()

    user_prompt = f"""Analyze this MD&A section from {ticker}'s {quarter} 10-Q filing.

MD&A TEXT:
{mda_text[:12000]}

Extract the 7 signals and return JSON only."""

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = await _llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        raw = response.content.strip()
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        signals = json.loads(raw)
        logger.info(
            f"[Extractor] {ticker} {quarter}: "
            f"tone={signals.get('management_tone')} "
            f"AI={signals.get('ai_monetization')} "
            f"margins={signals.get('margin_language')}"
        )
        return signals
    except Exception as e:
        logger.error(f"[Extractor] {ticker} {quarter} failed: {e}")
        return _default_signals()


def _default_signals() -> dict:
    return {
        "management_tone":    "cautious",
        "margin_language":    "stable",
        "ai_monetization":    "absent",
        "demand_signals":     "mixed",
        "hiring_language":    "stable",
        "regulatory_concern": "moderate",
        "recurring_concerns": [],
        "key_quotes":         [],
        "confidence":         0.1,
    }
