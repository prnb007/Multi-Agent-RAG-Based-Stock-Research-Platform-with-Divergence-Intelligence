import re
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse_llm_json(raw: str, fallback: Optional[dict] = None) -> dict:
    """
    Defensive JSON extraction from LLM responses.
    Handles every weird format LLMs produce.
    """
    if not raw or not isinstance(raw, str):
        return fallback or {}

    # Step 1: Strip markdown fences
    raw = re.sub(r'```(?:json|JSON)?\s*\n?', '', raw)
    raw = re.sub(r'\n?```\s*$', '', raw)
    raw = raw.strip()

    # Step 2: Try direct parse first (most efficient path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Step 3: Extract the outermost JSON object using balanced braces
    json_str = _extract_json_object(raw)
    if not json_str:
        logger.warning(f"[parse_llm_json] No JSON object found in: {raw[:200]}")
        return fallback or {}

    # Step 4: Try parsing extracted JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Step 5: Apply common fixes
    cleaned = json_str
    cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)         # trailing commas
    cleaned = re.sub(r"(?<!\\)'", '"', cleaned)              # single quotes (not escaped)
    cleaned = re.sub(r'//[^\n]*', '', cleaned)               # // comments
    cleaned = re.sub(r'/\*[\s\S]*?\*/', '', cleaned)         # /* */ comments

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(
            f"[parse_llm_json] All attempts failed. Raw: {raw[:300]}... Error: {e}"
        )
        return fallback or {}


def _extract_json_object(text: str) -> Optional[str]:
    """Find first balanced JSON object in text."""
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        char = text[i]

        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue

        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None
