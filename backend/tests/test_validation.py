"""Tests for Dockerfile validation and AI repair."""

import pytest

from app.db.store import store
from app.models.records import RepairRecord, utcnow
from tests.fakes import FakeLLMProvider


async def _generate_dockerfile(client, monkeypatch) -> dict:
    monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: FakeLLMProvider())
    analyzed = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-fastapi"},
    )
    started = await client.post(
        "/api/v1/dockerfiles/generate",
        json={"project_id": analyzed.json()["project_id"]},
    )
    job = await client.get(f"/api/v1/jobs/{started.json()['job_id']}")
    detail = await client.get(f"/api/v1/dockerfiles/{job.json()['dockerfile_id']}")
    return detail.json()


@pytest.mark.asyncio
async def test_validate_requires_confirmation_for_builds(client, monkeypatch):
    dockerfile = await _generate_dockerfile(client, monkeypatch)
    resp = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/validate",
        json={"approve_build": True, "confirm_untrusted_execution": False},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_lint_only_validation_without_build_approval(client, monkeypatch):
    dockerfile = await _generate_dockerfile(client, monkeypatch)

    async def fake_hadolint(_path):
        return {"status": "passed", "findings": [], "reason": None}

    monkeypatch.setattr("app.services.validation.run_hadolint", fake_hadolint)
    started = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/validate",
        json={"approve_build": False},
    )
    assert started.status_code == 202
    job = await client.get(f"/api/v1/jobs/{started.json()['job_id']}")
    assert job.json()["status"] == "completed"
    validation_id = job.json()["validation_id"]
    result = await client.get(f"/api/v1/validations/{validation_id}")
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "lint_only"
    assert body["build"]["status"] == "skipped"
    assert body["approved_build"] is False


@pytest.mark.asyncio
async def test_approved_build_records_failure_and_size(client, monkeypatch):
    dockerfile = await _generate_dockerfile(client, monkeypatch)

    async def fake_hadolint(_path):
        return {"status": "passed", "findings": [], "reason": None}

    async def fake_build(_context, image_tag):
        return {
            "status": "failed",
            "reason": "docker build exited with a non-zero status",
            "image_tag": None,
            "log": "ERROR: failed to solve: executor failed running [/bin/sh -c pip install]",
            "duration_ms": 1200,
        }

    monkeypatch.setattr("app.services.validation.run_hadolint", fake_hadolint)
    monkeypatch.setattr("app.services.validation.build_image", fake_build)

    async def fake_remove(_tag):
        return None

    monkeypatch.setattr("app.services.validation.remove_image", fake_remove)

    started = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/validate",
        json={"approve_build": True, "confirm_untrusted_execution": True},
    )
    job = await client.get(f"/api/v1/jobs/{started.json()['job_id']}")
    result = await client.get(f"/api/v1/validations/{job.json()['validation_id']}")
    body = result.json()
    assert body["status"] == "failed"
    assert body["build"]["status"] == "failed"
    assert "pip install" in body["error_log"]


@pytest.mark.asyncio
async def test_repair_failed_validation(client, monkeypatch):
    dockerfile = await _generate_dockerfile(client, monkeypatch)
    monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: FakeLLMProvider())
    monkeypatch.setattr("app.services.repair.get_llm_provider", lambda: FakeLLMProvider())

    async def fake_hadolint(_path):
        return {"status": "passed", "findings": [], "reason": None}

    async def fake_build(_context, image_tag):
        return {
            "status": "failed",
            "reason": "build failed",
            "image_tag": None,
            "log": "failed to solve: COPY requirements.txt",
            "duration_ms": 10,
        }

    monkeypatch.setattr("app.services.validation.run_hadolint", fake_hadolint)
    monkeypatch.setattr("app.services.validation.build_image", fake_build)

    async def fake_remove(_tag):
        return None

    monkeypatch.setattr("app.services.validation.remove_image", fake_remove)

    started = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/validate",
        json={"approve_build": True, "confirm_untrusted_execution": True},
    )
    validation_id = (await client.get(f"/api/v1/jobs/{started.json()['job_id']}")).json()[
        "validation_id"
    ]

    repaired = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/repair",
        json={"validation_id": validation_id},
    )
    assert repaired.status_code == 202
    job = await client.get(f"/api/v1/jobs/{repaired.json()['job_id']}")
    assert job.json()["status"] == "completed"
    new_id = job.json()["dockerfile_id"]
    detail = await client.get(f"/api/v1/dockerfiles/{new_id}")
    assert detail.json()["status"] == "repaired"
    assert "FROM python:3.12-slim" in detail.json()["dockerfile"]

    history = await client.get(f"/api/v1/dockerfiles/{dockerfile['id']}/repairs")
    assert history.json()["attempts_used"] == 1
    assert history.json()["max_attempts"] == 3
    assert history.json()["items"][0]["root_cause"]


@pytest.mark.asyncio
async def test_repair_rejects_lint_only_validation(client, monkeypatch):
    dockerfile = await _generate_dockerfile(client, monkeypatch)

    async def fake_hadolint(_path):
        return {"status": "passed", "findings": [], "reason": None}

    monkeypatch.setattr("app.services.validation.run_hadolint", fake_hadolint)
    started = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/validate",
        json={"approve_build": False},
    )
    validation_id = (await client.get(f"/api/v1/jobs/{started.json()['job_id']}")).json()[
        "validation_id"
    ]
    resp = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/repair",
        json={"validation_id": validation_id},
    )
    assert resp.status_code == 400
    assert "failed validation" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_passed_build_reports_size_and_session_stats(client, monkeypatch):
    dockerfile = await _generate_dockerfile(client, monkeypatch)

    async def fake_hadolint(_path):
        return {"status": "passed", "findings": [], "reason": None}

    async def fake_build(_context, image_tag):
        return {
            "status": "passed",
            "reason": None,
            "image_tag": image_tag,
            "log": "Successfully built",
            "duration_ms": 2500,
            "image_size_bytes": 45_000_000,
        }

    async def fake_remove(_tag):
        return None

    monkeypatch.setattr("app.services.validation.run_hadolint", fake_hadolint)
    monkeypatch.setattr("app.services.validation.build_image", fake_build)
    monkeypatch.setattr("app.services.validation.remove_image", fake_remove)

    started = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/validate",
        json={"approve_build": True, "confirm_untrusted_execution": True},
    )
    job = await client.get(f"/api/v1/jobs/{started.json()['job_id']}")
    result = await client.get(f"/api/v1/validations/{job.json()['validation_id']}")
    body = result.json()
    assert body["status"] == "passed"
    assert body["image_size_bytes"] == 45_000_000
    assert body["build_duration_ms"] == 2500
    assert body["size_comparison"] is None

    stats = await client.get("/api/v1/stats")
    assert stats.json()["successful_builds"] == 1
    assert stats.json()["avg_build_time_ms"] == 2500
    assert stats.json()["dockerfiles_generated"] == 1


@pytest.mark.asyncio
async def test_optimized_build_reports_size_delta_against_original(client, monkeypatch):
    monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: FakeLLMProvider())
    analyzed = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-unoptimized"},
    )
    started = await client.post(
        "/api/v1/dockerfiles/optimize",
        json={"project_id": analyzed.json()["project_id"], "model": "codellama:7b"},
    )
    job = await client.get(f"/api/v1/jobs/{started.json()['job_id']}")
    dockerfile_id = job.json()["dockerfile_id"]

    async def fake_hadolint(_path):
        return {"status": "passed", "findings": [], "reason": None}

    async def fake_build(context, image_tag):
        text = (context / "Dockerfile").read_text()
        return {
            "status": "passed",
            "reason": None,
            "image_tag": image_tag,
            "log": "built",
            "duration_ms": 20,
            "image_size_bytes": 900_000_000 if "python:latest" in text else 180_000_000,
        }

    async def fake_remove(_tag):
        return None

    monkeypatch.setattr("app.services.validation.run_hadolint", fake_hadolint)
    monkeypatch.setattr("app.services.validation.build_image", fake_build)
    monkeypatch.setattr("app.services.validation.remove_image", fake_remove)

    validated = await client.post(
        f"/api/v1/dockerfiles/{dockerfile_id}/validate",
        json={"approve_build": True, "confirm_untrusted_execution": True},
    )
    validation_id = (await client.get(f"/api/v1/jobs/{validated.json()['job_id']}")).json()[
        "validation_id"
    ]
    body = (await client.get(f"/api/v1/validations/{validation_id}")).json()
    comparison = body["size_comparison"]
    assert body["status"] == "passed"
    assert body["image_size_bytes"] == 180_000_000
    assert comparison["baseline_status"] == "passed"
    assert comparison["baseline_image_size_bytes"] == 900_000_000
    assert comparison["delta_bytes"] == -720_000_000
    assert comparison["delta_percent"] == -80.0


@pytest.mark.asyncio
async def test_failed_original_build_does_not_fail_optimized_validation(client, monkeypatch):
    monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: FakeLLMProvider())
    analyzed = await client.post(
        "/api/v1/projects/analyze",
        json={"source_type": "directory", "path": "python-unoptimized"},
    )
    started = await client.post(
        "/api/v1/dockerfiles/optimize",
        json={"project_id": analyzed.json()["project_id"], "model": "codellama:7b"},
    )
    dockerfile_id = (await client.get(f"/api/v1/jobs/{started.json()['job_id']}")).json()[
        "dockerfile_id"
    ]

    async def fake_hadolint(_path):
        return {"status": "passed", "findings": [], "reason": None}

    async def fake_build(context, image_tag):
        text = (context / "Dockerfile").read_text()
        if "python:latest" in text:
            return {
                "status": "failed",
                "reason": "original build failed",
                "image_tag": None,
                "log": "failed",
                "duration_ms": 5,
            }
        return {
            "status": "passed",
            "reason": None,
            "image_tag": image_tag,
            "log": "built",
            "duration_ms": 20,
            "image_size_bytes": 180_000_000,
        }

    async def fake_remove(_tag):
        return None

    monkeypatch.setattr("app.services.validation.run_hadolint", fake_hadolint)
    monkeypatch.setattr("app.services.validation.build_image", fake_build)
    monkeypatch.setattr("app.services.validation.remove_image", fake_remove)

    validated = await client.post(
        f"/api/v1/dockerfiles/{dockerfile_id}/validate",
        json={"approve_build": True, "confirm_untrusted_execution": True},
    )
    validation_id = (await client.get(f"/api/v1/jobs/{validated.json()['job_id']}")).json()[
        "validation_id"
    ]
    body = (await client.get(f"/api/v1/validations/{validation_id}")).json()
    assert body["status"] == "passed"
    assert body["size_comparison"]["baseline_status"] == "failed"
    assert body["size_comparison"]["delta_bytes"] is None


@pytest.mark.asyncio
async def test_repair_rejects_beyond_max_attempts(client, monkeypatch):
    dockerfile = await _generate_dockerfile(client, monkeypatch)
    for index in range(3):
        store.save_repair(
            RepairRecord(
                id=f"r{index}",
                validation_id="v1",
                source_dockerfile_id=dockerfile["id"],
                attempt=index + 1,
                created_at=utcnow(),
            )
        )
    resp = await client.post(
        f"/api/v1/dockerfiles/{dockerfile['id']}/repair",
        json={"validation_id": "missing"},
    )
    assert resp.status_code == 400
    assert "Maximum repair attempts" in resp.json()["detail"]
