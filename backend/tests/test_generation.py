"""Tests for Dockerfile generation jobs using a fake LLM."""

import pytest

from tests.fakes import FakeLLMProvider


@pytest.mark.asyncio
async def test_generate_dockerfile_job(client, monkeypatch):
    fake = FakeLLMProvider()
    monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: fake)

    analyzed = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-fastapi"},
    )
    assert analyzed.status_code == 200
    project_id = analyzed.json()["project_id"]

    started = await client.post(
        "/api/v1/dockerfiles/generate",
        json={"project_id": project_id, "model": "codellama:7b"},
    )
    assert started.status_code == 202
    job_id = started.json()["job_id"]

    job = await client.get(f"/api/v1/jobs/{job_id}")
    assert job.status_code == 200
    payload = job.json()
    assert payload["status"] == "completed"
    assert payload["dockerfile_id"]

    dockerfile = await client.get(f"/api/v1/dockerfiles/{payload['dockerfile_id']}")
    assert dockerfile.status_code == 200
    body = dockerfile.json()
    assert "FROM python:3.12-slim" in body["dockerfile"]
    assert ".venv" in body["dockerignore"]
    assert body["explanation"]
    assert fake.prompts and "<untrusted_project_data>" in fake.prompts[0]

    edited = await client.put(
        f"/api/v1/dockerfiles/{payload['dockerfile_id']}",
        json={"dockerfile": body["dockerfile"] + "\n# edited\n"},
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "edited"

    history = await client.get("/api/v1/dockerfiles/history")
    assert history.status_code == 200
    assert len(history.json()["items"]) == 1


@pytest.mark.asyncio
async def test_generate_fails_when_ollama_offline(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.generation.get_llm_provider",
        lambda: FakeLLMProvider(connected=False),
    )
    analyzed = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-fastapi"},
    )
    started = await client.post(
        "/api/v1/dockerfiles/generate",
        json={"project_id": analyzed.json()["project_id"]},
    )
    job = await client.get(f"/api/v1/jobs/{started.json()['job_id']}")
    assert job.json()["status"] == "failed"
    assert "Ollama" in job.json()["error"]


@pytest.mark.asyncio
async def test_settings_round_trip(client):
    original = await client.get("/api/v1/settings")
    assert original.status_code == 200
    assert original.json()["ollama_default_model"]

    updated = await client.put(
        "/api/v1/settings",
        json={"ollama_default_model": "llama3.2:3b", "max_repair_attempts": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["ollama_default_model"] == "llama3.2:3b"
    assert updated.json()["max_repair_attempts"] == 2

    await client.put(
        "/api/v1/settings",
        json={
            "ollama_default_model": original.json()["ollama_default_model"],
            "max_repair_attempts": original.json()["max_repair_attempts"],
        },
    )
