import re
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_llm_json(raw: str, fallback: dict = None) -> dict:
    """
    Robust JSON extraction from LLM responses.
    Handles: markdown fences, prefix/suffix text, single quotes, trailing commas.
    """
    if not raw or not isinstance(raw, str):
        return fallback or {}

    # Remove markdown code fences
    raw = re.sub(r'```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'```\s*$', '', raw)

    # Find the JSON object (greedy match for nested braces)
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        return fallback or {}

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Fix common LLM mistakes
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # trailing commas
    json_str = json_str.replace("'", '"')                 # single to double quotes

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"[parse_llm_json] Failed to parse: {json_str[:200]}... Error: {e}")
        return fallback or {}
