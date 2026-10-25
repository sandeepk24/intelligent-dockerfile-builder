"""Tests for health and model discovery endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Health endpoint returns expected structure."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "ollama_connected" in data
    assert "ollama_url" in data


@pytest.mark.asyncio
async def test_models_endpoint(client):
    """Models endpoint returns expected structure."""
    resp = await client.get("/api/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "default_model" in data
    assert isinstance(data["models"], list)
