"""Tests for existing Dockerfile review and optimization."""

from pathlib import Path

import pytest

from tests.fakes import FakeLLMProvider

SAMPLE = Path(__file__).resolve().parents[2] / "sample-projects" / "python-unoptimized"


@pytest.mark.asyncio
async def test_analyze_unoptimized_project_returns_issues(client):
    resp = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-unoptimized"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["has_dockerfile"] is True
    codes = {issue["code"] for issue in data["dockerfile_issues"]}
    assert "latest-tag" in codes
    assert "copies-secrets" in codes
    assert data["existing_dockerfile"].startswith("FROM python:latest")


@pytest.mark.asyncio
async def test_analyze_pasted_dockerfile(client):
    resp = await client.post(
        "/api/v1/projects/analyze",
        json={
            "source_type": "dockerfile",
            "name": "legacy",
            "dockerfile": "FROM node:latest\nCMD npm start\n",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["source_type"] == "dockerfile"
    assert data["language"] == "javascript"
    assert any(issue["code"] == "latest-tag" for issue in data["dockerfile_issues"])


@pytest.mark.asyncio
async def test_optimize_existing_dockerfile_job(client, monkeypatch):
    fake = FakeLLMProvider()
    monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: fake)

    analyzed = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-unoptimized"},
    )
    project_id = analyzed.json()["project_id"]
    started = await client.post(
        "/api/v1/dockerfiles/optimize",
        json={"project_id": project_id, "model": "codellama:7b"},
    )
    assert started.status_code == 202
    job = await client.get(f"/api/v1/jobs/{started.json()['job_id']}")
    assert job.json()["status"] == "completed"
    detail = await client.get(f"/api/v1/dockerfiles/{job.json()['dockerfile_id']}")
    body = detail.json()
    assert body["status"] == "optimized"
    assert "FROM python:3.12-slim" in body["dockerfile"]
    assert body["original_dockerfile"].startswith("FROM python:latest")
    assert body["issues"]
    assert fake.prompts and "Known issues from static review" in fake.prompts[0]
    assert "<untrusted_project_data>" in fake.prompts[0]
