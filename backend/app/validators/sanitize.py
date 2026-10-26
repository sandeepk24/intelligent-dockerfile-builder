"""Sanitize untrusted build logs before they are stored or sent to an LLM."""

from __future__ import annotations

import re
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|passwd|authorization)\s*[:=]\s*\S+"
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MAX_LOG_CHARS = 8_000


def sanitize_log(text: str, *, extra_paths: list[str] | None = None) -> str:
    """Redact secrets and local paths, then truncate."""
    cleaned = _ANSI_RE.sub("", text or "")
    cleaned = _SECRET_RE.sub(r"\1=<redacted>", cleaned)
    cleaned = _EMAIL_RE.sub("<redacted-email>", cleaned)

    replacements = [str(Path.home()), "/Users/", "/home/"]
    if extra_paths:
        replacements.extend(extra_paths)
    for path in sorted({item for item in replacements if item}, key=len, reverse=True):
        cleaned = cleaned.replace(path, "<path>")

    if len(cleaned) > MAX_LOG_CHARS:
        cleaned = cleaned[:MAX_LOG_CHARS] + "\n<truncated>"
    return cleaned
