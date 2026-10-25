"""Helpers for extracting JSON objects from LLM responses."""

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def parse_json_response(text: str) -> dict[str, Any]:
    """Parse a JSON object from model output, including fenced markdown."""
    cleaned = text.strip()
    cleaned = _FENCE_RE.sub("", cleaned).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("LLM response did not contain a JSON object") from None
        parsed = json.loads(cleaned[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON response must be an object")
    return parsed
