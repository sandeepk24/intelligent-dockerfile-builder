"""Tests for the in-memory store."""

from datetime import UTC, datetime

from app.db.memory_store import MemoryStore
from app.models.records import DockerfileRecord, JobRecord, ProjectRecord


def test_store_round_trip_and_history_order():
    memory = MemoryStore()
    first = memory.save_dockerfile(
        DockerfileRecord(
            id="df-1",
            project_id="p1",
            dockerfile="FROM python:3.12-slim",
            dockerignore="__pycache__",
            explanation="base",
            decisions=[],
            model="codellama:7b",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    second = memory.save_dockerfile(
        DockerfileRecord(
            id="df-2",
            project_id="p1",
            dockerfile="FROM python:3.13-slim",
            dockerignore="__pycache__",
            explanation="newer",
            decisions=[],
            model="codellama:7b",
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
    )
    history = memory.list_dockerfiles()
    assert [item.id for item in history] == [second.id, first.id]


def test_store_project_and_job_updates():
    memory = MemoryStore()
    project = memory.save_project(
        ProjectRecord(id="p1", source_type="directory", name="demo", root_path="/tmp/demo")
    )
    job = memory.save_job(JobRecord(id="j1", job_type="generate"))
    updated = memory.update_job("j1", status="completed", dockerfile_id="df-1")

    assert memory.get_project("p1") is project
    assert updated is not None
    assert updated.status == "completed"
    assert job.dockerfile_id == "df-1"
