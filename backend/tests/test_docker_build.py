"""Tests for isolated Docker build helpers."""

from pathlib import Path

import pytest

from app.validators.docker_build import build_image


@pytest.mark.asyncio
async def test_build_skipped_when_docker_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.validators.docker_build.docker_available", lambda: False)
    result = await build_image(tmp_path, "idf-test:skip")
    assert result["status"] == "skipped"
    assert "not installed" in result["reason"]
