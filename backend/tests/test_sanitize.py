"""Tests for build log sanitization."""

from app.validators.sanitize import sanitize_log


def test_redacts_secrets_and_truncates():
    text = "PASSWORD=supersecret\nAuthorization: Bearer abc\n" + ("x" * 20_000)
    cleaned = sanitize_log(text)
    assert "supersecret" not in cleaned
    assert "<redacted>" in cleaned
    assert cleaned.endswith("<truncated>")
