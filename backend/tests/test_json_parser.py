"""Tests for LLM JSON response parsing."""

import pytest

from app.llm.json_parser import parse_json_response


def test_parse_plain_json_object():
    result = parse_json_response('{"dockerfile": "FROM python:3.12-slim"}')
    assert result["dockerfile"] == "FROM python:3.12-slim"


def test_parse_fenced_json():
    text = """```json
{"explanation": "multi-stage build"}
```"""
    result = parse_json_response(text)
    assert result["explanation"] == "multi-stage build"


def test_parse_json_embedded_in_text():
    text = 'Here is the result: {"ok": true} thanks'
    result = parse_json_response(text)
    assert result["ok"] is True


def test_reject_non_object_json():
    with pytest.raises(ValueError, match="object"):
        parse_json_response("[1, 2]")
