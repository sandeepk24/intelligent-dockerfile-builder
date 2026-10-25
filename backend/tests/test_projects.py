"""Tests for project analysis endpoints."""

import io
import zipfile
from pathlib import Path

import pytest

SAMPLE_ROOT = Path(__file__).resolve().parents[2] / "sample-projects"


@pytest.mark.asyncio
async def test_list_workspace_projects(client):
    resp = await client.get("/api/v1/workspace/projects")
    assert resp.status_code == 200
    data = resp.json()
    names = {item["name"] for item in data["projects"]}
    assert {"python-fastapi", "node-express", "go-api"} <= names


@pytest.mark.asyncio
async def test_analyze_python_directory(client):
    resp = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-fastapi"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["language"] == "python"
    assert data["framework"] == "fastapi"
    assert data["entry_point"] == "app/main.py"
    assert "fastapi" in [dep.lower() for dep in data["dependencies"]]


@pytest.mark.asyncio
async def test_analyze_rejects_path_traversal(client):
    resp = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "../backend"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_analyze_zip_upload(client):
    buffer = io.BytesIO()
    source = SAMPLE_ROOT / "python-fastapi"
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(path, Path("python-fastapi") / path.relative_to(source))
    resp = await client.post(
        "/api/v1/projects/analyze",
        files={"file": ("python-fastapi.zip", buffer.getvalue(), "application/zip")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["source_type"] == "zip"
    assert data["language"] == "python"
    assert data["framework"] == "fastapi"
