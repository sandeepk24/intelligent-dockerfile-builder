"""Tests for Hadolint JSON parsing."""

from app.validators.hadolint import _parse_findings


def test_parses_hadolint_json():
    raw = """[
      {"code": "DL3006", "level": "error", "message": "Always tag the version", "line": 1}
    ]"""
    findings = _parse_findings(raw)
    assert findings[0]["code"] == "DL3006"
    assert findings[0]["line"] == 1
